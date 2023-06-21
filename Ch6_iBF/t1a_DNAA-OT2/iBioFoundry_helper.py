# # Automated Liquid Handling for Golden Gate Assembly using Opentrons OT2

#author: Camillo Moschner (PhD student, Bakhis Lab) | Date: 31.08.2021
# --------------------------------------------------------------------------------------------------------------------------------------------
metadata = {
    'protocolName': '# Automated Liquid Handling for Golden Gate Assembly using Opentrons OT2',
    'author': 'Camillo Moschner <cm967@cam.ac.uk> / <camillo.moschner@gmail.com>',
    'description': 'Programme for the automated assembly of Golden Gate DNA assemblies.',
    'apiLevel': '2.10',
    'Date': '25.10.2021'
    }
# --------------------------------------------------------------------------------------------------------------------------------------------

from IPython.display import display, clear_output, Audio, display
from copy import deepcopy
from itertools import chain, combinations
from random import randint
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import math

from opentrons import protocol_api, execute, simulate
# --------------------------------------------------------------------------------------------------------------------------------------------
# CLASS DEFINITIONS

class Plate():
    """
    Creates a plate object, representing any type of labware plate or rack to allow tracking of its constituents.
    In1 (optional): str or int (plate wells, default='96')
    In2 (optional): str (name or ID of the plate)
    Out: plate object
    """
    def __init__(self, plate_format='96',name='undefined',only_columns='all',empty_margin=0):
        alphabet = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
        well_format_dic = {'6' : (2,4),
                           '12' : (3,5), 
                           '24' : (4, 7), 
                           '32' : (8, 5), 
                           '96' : (8, 13), 
                           '384': (16, 25)
                          }
        column_label_end, row_label_end = well_format_dic[str(plate_format)][0]-empty_margin, well_format_dic[str(plate_format)][1]-empty_margin
        row_label = alphabet[empty_margin:column_label_end]
        #well_list = [letter.upper()+str(column_label) for letter in row_label for column_label in range(1+empty_margin,row_label_end)]
        self.layout = pd.DataFrame(0, index = row_label, columns=np.arange(1+empty_margin,row_label_end))
        self.format = plate_format
        self.name, self.rows, self.columns = name, column_label_end, row_label_end-1
        if only_columns =='odd':
            self.layout = self.layout.loc[:,[x for x in np.arange(1,self.columns,2)]]
        elif only_columns =='even': # also requires changing of the fill_start_position argument if you want to fill this plate up
            self.layout = self.layout.loc[:,[x for x in np.arange(2,self.columns,2)]]
        well_list = []
        for row_idx in self.layout.index:
            for col_idx in self.layout.columns:
                well_list.append(str(row_idx)+str(col_idx))
        self.well_list = well_list
    @property # compute all occupied wells every time this is called -> allows for self-updating information
    def occupied_wells(self):
        constructs = list(chain.from_iterable([self.layout[column_no].loc[self.layout[column_no]!=0].to_list() for column_no in self.layout.columns]))
        occupied_wells_dic = {}
        for s_construct in constructs:
            occupied_wells_dic[find_df_coordinates(self.layout,s_construct)] = s_construct
        return occupied_wells_dic
        

# --------------------------------------------------------------------------------------------------------------------------------------------
# FUNCTION DEFINITIONS  

def update_labware(df,new_deck_components):
    """
    Helper function to update the deck overview with a new labware (either a single string or a list of multiple labware components)
    """
    if type(new_deck_components) == list:
        for labware_item in new_deck_components:
            df.replace(labware_item.parent,f"{new_deck_components.parent}-{labware_item.load_name}",inplace=True)
    elif type(new_deck_components.parent) == str:
        df.replace(new_deck_components.parent,f"{new_deck_components.parent}-{new_deck_components.load_name}",inplace=True)

 # --------------------------------------------------------------------------------------------------------------------------------------------
       
def identify_plate(format_name,feature):
    """Gives either the 'max_well_vol' or the 'plate_format' for a format_name.
    """
    choice_dic = {'corning_384_wellplate_112ul_flat': {'max_well_vol' : 65, # safety volume!
                                                       'plate_format' : '384'},
                  'biorad_384_wellplate_50ul' : {'max_well_vol' : 50,
                                                 'plate_format' : '384'},
                  '384PP_AQ_BP2' : {'max_well_vol' : 64., # Beckman Coulter working range: 2.5-12 μL | SKU: 001-14555
                                    'plate_format' : '384',
                                    'dead_vol' : 15},
                  '384LDV_AQ_B2' : {'max_well_vol' : 11.5, # DMSO working range: 2.5-12 μL | SKU: LP-0200
                                    'plate_format' : '384',
                                    'dead_vol' : 2.5},
                  '384_PCR_plate Framestar - 4titude' : {'max_well_vol' : 30, # https://www.azenta.com/products/framestar-384-well-skirted-pcr-plate
                                                         # DMSO working range: 15-65 μL | SKU: PP-0200
                                                         'plate_format' : '384',
                                                         'dead_vol' : 1}, 
                  'corning_96_wellplate_360ul_flat': {'max_well_vol' : 300,
                                                    'plate_format' : '96',
                                                    'dead_vol' : 10},
                  'biorad_96_wellplate_200ul_pcr': {'max_well_vol' : 190,
                                                    'plate_format' : '96',
                                                    'dead_vol' : 2},
                  'opentrons_96_aluminumblock_biorad_wellplate_200ul': {'max_well_vol' : 190,
                                                                        'plate_format' : '96'}, 
                  'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap' : {'max_well_vol' : 1_500,
                                                                              'plate_format' : '24'},
                  'opentrons_96_aluminumblock_generic_pcr_strip_200ul' : {'max_well_vol' : 190,
                                                                          'plate_format' : '96',
                                                                          'dead_vol' : 2},
                  'usascientific_96_wellplate_2.4ml_deep' : {'max_well_vol' : 190,
                                                             'plate_format' : '96',
                                                             'dead_vol' : 2_500},
                  'corning_24_wellplate_3.4ml_flat' : {'max_well_vol' : 3_300,
                                                       'plate_format' : '24'},
                  'corning_12_wellplate_6.9ml_flat' : {'max_well_vol' : 6_800,
                                                       'plate_format' : '12'},
                  'corning_6_wellplate_16.8ml_flat' : {'max_well_vol' : 16_700,
                                                       'plate_format' : '6'},

                 }
    return choice_dic[format_name][feature]

# --------------------------------------------------------------------------------------------------------------------------------------------

def create_part_IDs_list(first_part_ID_info_tuple,no_of_identifiers):
    """
    Creates list of unique, incrementally increasing IDS.
    In1: tuple of (str, int/float)
    In2: int
    """
    prefix = first_part_ID_info_tuple[0]
    start_no = first_part_ID_info_tuple[1]
    assembly_ID_list = []
    for x in np.arange(no_of_identifiers):
        assembly_ID_list.append(prefix+str(start_no))
        start_no += 1
    return assembly_ID_list

# --------------------------------------------------------------------------------------------------------------------------------------------

def show_time(time_duration_in_sec):
    """
    Takes duration in seconds and converts it to hours:minutes:seconds.
    """
    return f"{time.strftime('%H:%M:%S', time.gmtime(time_duration_in_sec))}"

# --------------------------------------------------------------------------------------------------------------------------------------------
def show_rack_usage(tiprack, statement=True):
    """
    Show how many and which tips of the tiprack have already been used.
    In: opentrons.protocol_api.labware.Labware
    Out1: list of positions used
    Out2: pandas.DataFrame of used and unused tiprack positions
    """
    def convert_to_position_tuple(str_position):
        if len(str_position) == 2:
            result_tuple = (str_position[0],int(str_position[1]))
        elif len(str_position) == 3:
            result_tuple = (str_position[0],int(str_position[1:]))
        return result_tuple
    rack = Plate('96')
    rack = rack.layout
    try:
        next_tip = convert_to_position_tuple(tiprack.next_tip().well_name)
    except AttributeError:
        return( f"All tips have been used up in {tiprack}",rack.replace(0,'x'))
    try:
        next_tip_position_row = convert_to_position_tuple(tiprack.next_tip().well_name)[0]
        next_tip_position_column = convert_to_position_tuple(tiprack.next_tip().well_name)[1]
    except AttributeError:
            print(f"Tips used up {tiprack.name}")
    rack = Plate('96')
    rack = rack.layout
    columns_used = list(rack.columns)[:list(rack.columns).index(next_tip_position_column)]
    rows_used = list(rack.index)[:list(rack.index).index(next_tip_position_row)+1]
    # create used positions lists
    used_positions = []
    for column_name in columns_used:
        for row_name in rack.index:
            used_positions.append(tuple([row_name,column_name]))
    final_column=list(rack.columns)[list(rack.columns).index(next_tip_position_column)]
    final_rows = list(rack.index)[:list(rack.index).index(next_tip_position_row)]
    # final column
    [used_positions.append(tuple([row_name,final_column])) for row_name in final_rows]
    # update positions
    for used_position in used_positions:
        rack.loc[used_position]='x'
    if statement == True:
        print(f"{tiprack}:\n -> {len(used_positions)} tips used:")
    return used_positions, rack

# --------------------------------------------------------------------------------------------------------------------------------------------

def transfer_volume_divided(vol_to_be_transferred, max_pipette_vol):
    """
    Takes any volume and divides that volume into list of pipetting steps based a given maximal pipetting volume.
    """
    no_pipetting_steps = math.ceil(vol_to_be_transferred/max_pipette_vol)
    no_pipetting_steps
    if no_pipetting_steps != 1:
        steps_info = []
        for step_idx in np.arange(no_pipetting_steps-1):
            steps_info.append(max_pipette_vol)
            vol_to_be_transferred = vol_to_be_transferred-max_pipette_vol
        steps_info.append(vol_to_be_transferred)
    else:
        steps_info=[vol_to_be_transferred]
    return steps_info
# --------------------------------------------------------------------------------------------------------------------------------------------

def updated_delay(local_protocol,wait_time_seconds, update_time_seconds,display_statement='',display_statement_extra=None):
    delay_list = transfer_volume_divided(wait_time_seconds,update_time_seconds)
    for idx, time_delay in enumerate(delay_list):
        clear_output()
        display(display_statement)
        if display_statement_extra!=None:
            display(display_statement_extra)
        display(f" Timer: {(idx+1)*time_delay} / {len(delay_list)*time_delay} sec")
        local_protocol.delay(time_delay)
        #time.sleep(time_delay)
# --------------------------------------------------------------------------------------------------------------------------------------------

def allDone():
  display(Audio(url='http://codeskulptor-demos.commondatastorage.googleapis.com/GalaxyInvaders/theme_01.mp3', autoplay=True))
    # https://simpleguics2pygame.readthedocs.io/en/latest/_static/links/snd_links.html

def startNow():
  display(Audio(url='http://commondatastorage.googleapis.com/codeskulptor-demos/riceracer_assets/music/start.ogg', autoplay=True))
    # https://simpleguics2pygame.readthedocs.io/en/latest/_static/links/snd_links.html
# --------------------------------------------------------------------------------------------------------------------------------------------

def divide_list_into_chunks(list_l, chunk_size):
    for i in range(0, len(list_l), chunk_size): 
        yield list_l[i:i + chunk_size]
        
# --------------------------------------------------------------------------------------------------------------------------------------------

def extend_fill_plate_df_with_list(empty_plate_df, reagent_list, fill_start_position='A1', inplace=False, fill_first='columns'):
    """
    Fills any pandas.DataFrame with a list of values, columns first then rows IF the value is 0/'0' and 
    updates you on what position it started filling if the pandas.DataFrame was not empty.
    In1: pd.DataFrame (empty if cell_value==0 or '0)
    In2: list
    In (optional): str (postion to start filling) 
    In (optional): bool (inplace change, True or False)
    """
    def convert_to_position_tuple(str_position):
        if len(str_position) == 2:
            result_tuple = (str_position[0],int(str_position[1]))
        elif len(str_position) == 3:
            result_tuple = (str_position[0],int(str_position[1:]))
        return result_tuple
    # choose whether to change the pandas.DataFrame inplace or not
    if inplace == True:
        copied_empty_plate_df = empty_plate_df
    else:
        copied_empty_plate_df = deepcopy(empty_plate_df)
    # choose whether to fill columns or rows first
    if fill_first=='rows':
        order = (copied_empty_plate_df.index, copied_empty_plate_df.columns)
    elif fill_first=='columns':
        order = (copied_empty_plate_df.columns, copied_empty_plate_df.index)
    # identify fill_start_position in callable way
    fill_start_tuple = convert_to_position_tuple(fill_start_position)
    # main commands
    helper_parts_list = deepcopy(reagent_list)
    if fill_start_position != 'A1':
        # create list of positions everything-upto-fill_start_position 
        if fill_first=='rows':
            full_well_list = [str(row_idx)+str(column_idx) 
                              for row_idx in copied_empty_plate_df.index
                              for column_idx in copied_empty_plate_df.columns]
        elif fill_first=='columns':
            full_well_list = [str(row_idx)+str(column_idx)
                              for column_idx in copied_empty_plate_df.columns
                              for row_idx in copied_empty_plate_df.index]
        not_to_use_position_list = full_well_list[ :full_well_list.index(fill_start_position) ]
        for row_idx in order[0]:
            for column_idx in order[1]:
                if not_to_use_position_list != []:
                    if fill_first=='rows':
                        locator = (row_idx,column_idx)
                    elif fill_first=='columns':
                        locator = (column_idx,row_idx)
                    # fill 'x' if any of these positions is not filled/a 0 or '0'
                    if (copied_empty_plate_df.loc[locator]==0) or (copied_empty_plate_df.loc[locator]=='0'):
                        copied_empty_plate_df.loc[locator]='x'
                    # remove position either way -> ensures that even filled positions will not affect the code
                    not_to_use_position_list.remove(not_to_use_position_list[0])
    # fill plate with reagent_list
    for row_idx in order[0]:
        for column_idx in order[1]:
            if helper_parts_list != []:
                if fill_first=='rows':
                    locator = (row_idx,column_idx)
                elif fill_first=='columns':
                    locator = (column_idx,row_idx)
                if (copied_empty_plate_df.loc[locator]==0) or (copied_empty_plate_df.loc[locator]=='0'):
                    copied_empty_plate_df.loc[locator]=helper_parts_list[0]
                    helper_parts_list.remove(helper_parts_list[0])
    # deal with the scenario that the given fill_start_position is already occupied -> extend-fill from the next available position
    if copied_empty_plate_df.iloc[0,0] != reagent_list[0]:#fill_start_position != 'A1':
        #copied_empty_plate_df.loc[ convert_to_position_tuple(find_df_coordinates(copied_empty_plate_df,reagent_list[0])) ] 
        if copied_empty_plate_df.loc[fill_start_tuple] != reagent_list[0]:#find_df_coordinates(copied_empty_plate_df,reagent_list[0]):
            print(f"Position {fill_start_position} has already been occupied with \'{copied_empty_plate_df.loc[fill_start_tuple]}\'.\n -> The next available position, {find_df_coordinates(copied_empty_plate_df,reagent_list[0])}, has been used to extend-fill the plate starting with \'{reagent_list[0]}\'!")
    return copied_empty_plate_df

# --------------------------------------------------------------------------------------------------------------------------------------------

def reverse_fill_plate_df_with_list(empty_plate_df, reagent_list):
    """
    In reverse order, fills any pandas.DataFrame with a list of values, columns first then rows IF the value is .
    """
    helper_parts_list = deepcopy(reagent_list)

    for row_idx in reversed(empty_plate_df.index):
        for column_idx in reversed(empty_plate_df.columns):
            if helper_parts_list != []:
                if (empty_plate_df.loc[row_idx,column_idx]==0) or (empty_plate_df.loc[row_idx,column_idx]=='0'):
                    empty_plate_df.loc[row_idx,column_idx]=helper_parts_list[0]
                    helper_parts_list.remove(helper_parts_list[0])
    return empty_plate_df

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def reversefill_CPplate_df_fromTopRight_with_list(empty_plate_df, reagent_list, dilution_no):
    """
    Special pandas.DataFrame filling with list case: cell plating multi-well plates require to be filled starting 
    top-right, go left and always have to have their dilutions in the same column below the first plating instance.
    This is because we look at them in a mirrored form during the plating process!
    """
    helper_parts_list = deepcopy(reagent_list)
    row_list = list(divide_list_into_chunks(list(empty_plate_df.index),dilution_no))
    for row_subset in row_list:
        for column_idx in reversed(empty_plate_df.columns):
            if helper_parts_list != []:
                for row_idx in row_subset:
                    if (empty_plate_df.loc[row_idx,column_idx]==0) or (empty_plate_df.loc[row_idx,column_idx]=='0'):
                            empty_plate_df.loc[row_idx,column_idx]=helper_parts_list[0]
                            helper_parts_list.remove(helper_parts_list[0])
            
    return empty_plate_df

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - DRAWING PLATES FUNCTIONS

def draw_circle(x,y, radius):
    theta = np.linspace( 0 , 2 * np.pi , 150 )
    a, b = radius * np.cos( theta ) + x, radius * np.sin( theta ) + y
    return a,b

def create_color_list(number_needed):
    color_list = []
    for i in range(number_needed):
        new_colour_hex_code = '#%06X' % randint(0, 0xFFFFFF)
        while new_colour_hex_code in color_list:
            new_colour_hex_code = '#%06X' % randint(0, 0xFFFFFF)
        color_list.append(new_colour_hex_code)
    return color_list

def plot_plate(row_no, column_no, color_list_l=False, df=None,alpha=1):
    figure, axes = plt.subplots( 1,figsize=(10,8))
    y_range,x_range = list(range(1,row_no+1)), list(range(1,column_no+1))
    alphabet = ['A','B','C','D','E','F','G','H','I','J','K','L','M',
                'N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    column_labels, counter = alphabet[:y_range[-1]], 0
    if color_list_l==False:
        color_list_l = create_color_list(96)
    for x in x_range:
        for y in y_range:
            axes.plot(*draw_circle(x,y,0.45),color='black',alpha=0.7)
            if isinstance(df, pd.DataFrame):
                locator = (y-1,x-1)
                if (df.iloc[locator]==0) or (df.iloc[locator]=='0') or (df.iloc[locator]=='x'):
                    pass
                else:                   
                    plt.text(x-0.4, y+0.05, df.iloc[locator],size=24/row_no+column_no)
                    #axes.fill_between(*draw_circle(x,y,0.44), color='C0', alpha=0.3)
                    circle = plt.Circle((x,y),0.44,color=color_list_l[counter],alpha=alpha)
                    axes.add_patch(circle)
                    counter+=1
    axes.set_aspect( 1 )
    plt.title( f"{row_no*column_no}-well Plate",y=-0.06)
    plt.gca().invert_yaxis()
    plt.xticks(np.arange(min(x_range), max(x_range)+1, 1))
    plt.yticks(np.arange(min(y_range), max(y_range)+1, 1))
    axes.xaxis.tick_top()
    axes.set_yticklabels(column_labels, minor=False)
    plt.show()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def find_df_coordinates(df_to_search,value,tuple_result=False):
    """
    Finds index and column of any value inside a DataFrame and returns them 
    as a str by default, can be changed to tuple to allow easy .loc identification.
    """
    if tuple_result==True:
        results = [(index_name,col_name) for index_name in df_to_search.index for col_name in df_to_search.columns if df_to_search.loc[index_name,col_name] == value]
    else:
        results = [str(index_name)+str(col_name) for index_name in df_to_search.index for col_name in df_to_search.columns if df_to_search.loc[index_name,col_name] == value]
    if results == []:
        print(f"Item {value} not in pandas.DataFrame")
    elif len(results) == 1:
        return results[0]
    else:
        return results


# --------------------------------------------------------------------------------------------------------------------------------------------

def find_df_coordinates_containing(df_to_search,value,tuple_result=False,statement=True):
    """
    Finds index and column of any value inside a DataFrame and returns them 
    as a str by default, can be changed to tuple to allow easy .loc identification.
    """
    if tuple_result==True:
        results = []
        for index_name in df_to_search.index:
            for col_name in df_to_search.columns:
                try:
                    if value in df_to_search.loc[index_name,col_name]:
                        result = (index_name,col_name)
                        results.append(result)
                except:
                    pass
    else:
        results = []
        for index_name in df_to_search.index:
            for col_name in df_to_search.columns:
                if str(df_to_search.loc[index_name,col_name]) == str(value):
                        result = str(index_name)+str(col_name)
                        results.append(result)
                else:
                    try:
                        if value in df_to_search.loc[index_name,col_name]:
                            result = str(index_name)+str(col_name)
                            results.append(result)
                    except:
                        pass
    if results == []:
        if statement:
            print(f"Item {value} not in pandas.DataFrame")
        else:
            pass
    elif len(results) == 1:
        return results
    else:
        return results

# --------------------------------------------------------------------------------------------------------------------------------------------
    
def plate_index_mapping(CP_plate_associated_list, n):
    """
    in1: CP_plate_no_list = list of assemblies associated with their CP_plate
    in2: n = number of deck positions filled with plate
    """
    new_list = []
    for plate_no in CP_plate_associated_list:
        if (n-1) >= plate_no:
            new_list.append(plate_no)
        elif (plate_no > 1*n-1) and (plate_no < 2*n):
            new_list.append(plate_no-n)
        elif (plate_no > 2*n-1) and (plate_no < 3*n):
            new_list.append(plate_no-2*n)
        elif (plate_no > 3*n-1) and (plate_no < 4*n):
            new_list.append(plate_no-3*n)
        elif (plate_no > 4*n-1) and (plate_no < 5*n):
            new_list.append(plate_no-4*n)
        elif (plate_no > 5*n-1) and (plate_no < 6*n):
            new_list.append(plate_no-5*n)
    return new_list

# --------------------------------------------------------------------------------------------------------------------------------------------

def convert_to_position_tuple(str_position):
    if len(str_position) == 2:
        result_tuple = (str_position[0],int(str_position[1]))
    elif len(str_position) == 3:
        result_tuple = (str_position[0],int(str_position[1:]))
    return result_tuple

# --------------------------------------------------------------------------------------------------------------------------------------------

def tips_used(tiprack_invest):
    """
    Takes tiprack object and calculates number of tips used in this tiprack object
    """
    try:
        if (len(show_rack_usage(tiprack_invest)[0])== 63) & (type(show_rack_usage(tiprack_invest)[0][0]) != tuple):
            no_used_samples = 96
            print(f"Tiprack used up")
        else:
            no_used_samples = len(show_rack_usage(tiprack_invest)[0])
    except:
        no_used_samples = len(show_rack_usage(tiprack_invest)[0])
    return no_used_samples


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def notna_data(series):
    """
    Powerful tiny function: takes pandas.Series that can contain NaN cells and returns pandas.Series of only real values.
    """
    return series.loc[series.notna()]


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def replenish_tiprack(tiprack_to_replenish):
    """Quick reset of tiprack to default, full mode -> used to replenish tiprack. Includes a security question.
    """
    checkup_question = 'No'
    while checkup_question != 'yes':
        checkup_question = input(f"\n    [Have you replenished all the tips in {tiprack_to_replenish}? (yes/no)\n      answer:") #\n - {tiprack20a}
        if checkup_question == 'no':
            print(f"      You need to replenish the tips in your tipracks, otherwise you will run out of tips before the protocol has finished.\n")
    tiprack_to_replenish.reset()
    print(f"              Excellent! Now you can continue running the rest of the protocol.]")

# --------------------------------------------------------------------------------------------------------------------------------------------

"""
LIQUID HEIGHT CALCULATIONS
"""
def calc_bioradPCRtube_height(volume_given,units='ul'):
    """
    Calculates height of liquid inside 0.2 ml BioRad PCR tube, given only the liquid volume.
    Not perfect as it assumes that the cone has a steady incline from top to bottom, ignoring that the tube is actually
    made up of a cylindrical and a cone component.
    In: float - liquid volume - in ul (default) or ml
    Out: float - liquid height in tube - in mm
    """
    r = 5.46/2 # units: mm ->http://www.dongilsc.co.kr/default/ls/ls0302.php?com_board_basic=read_form&com_board_idx=36&sub=03&&com_board_search_code=&com_board_search_value1=&com_board_search_value2=&com_board_page=5&&com_board_id=12&&com_board_id=12
    vol_adjustment_factor = 1.7338049 # factor for specific BioRad tube => vol_adjustment_factor = (np.pi * (eppi_rack['A1'].diameter/2)**2 * 17.8) / v_cone
    if units=='ul': # allows volume being given in 1µl or ml and height output always in mm
        conversion_factor = 1 # 1ml = 1_000 mm^3 ∴ 1µl = 1mm^3 
    elif units=='ml':
        conversion_factor = 1_000
    liquid_height = (volume_given*vol_adjustment_factor/(np.pi * r**2)) * conversion_factor
    return round(liquid_height,2)
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

def calc_eppi_height(volume_given,units='ul'):
    """
    Calculates height of liquid inside 1.5 ml Eppendorf tube, given only the liquid volume.
    v2 - now updated to account for the cylindrical and the conical part of the tube separately!
    In: float - liquid volume - in ul (default) or ml
    Out: float - liquid height in tube - in mm
    """
    r = 8.7/2 # units: mm -> eppi_rack['A1'].diameter
    vol_adjustment_factor = 3.4017177 # for cone part = (np.pi * (eppi_rack['A1'].diameter/2)**2 * (eppi_rack['A1'].depth-20)) / V_cone_max_volume
    if units=='ul': # allows volume being given in 1µl or ml and height output always in mm
        conversion_factor, v_cone = 1, 311.065 # 1ml = 1_000 mm^3 ∴ 1µl = 1mm^3 
    elif units=='ml':
        conversion_factor, v_cone = 1_000, 0.311065
    if volume_given < v_cone: # volume only in cone part
        liquid_height = (volume_given*vol_adjustment_factor/(np.pi * r**2)) * conversion_factor
    else: # volume also entering cylindrical part
        liquid_height = 17.8 +  ((volume_given-v_cone)/(np.pi * r**2)) * conversion_factor
    return round(liquid_height,2)

def save_eppi_height_cal(reagent_vol):
    reagent_height = calc_eppi_height(reagent_vol)-0.6
    if reagent_height > 1:
        return reagent_height
    else:
        return 1.0
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

def calc_15ml_Falcon_height(volume_given,units='ml'):
    """
    Calculates height of liquid inside 15 ml Falcon tube, given only the liquid volume.
    In: float - liquid volume - in ml (default) or ul
    Out: float - liquid height in tube - in mm
    """
    r = 14.9/2 # units: mm; inner diameter as stored by Opentrons 
    # -> https://www.fishersci.co.uk/shop/products/falcon-50ml-conical-centrifuge-tubes-2/10788561 # opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical
    if units=='ul': # allows volume being given in 1µl or ml and height output always in mm
        conversion_factor, v_cone = 1, 1_300 # 1ml = 1_000 mm^3 ∴ 1µl = 1mm^3 
    elif units=='ml':
        conversion_factor, v_cone = 1_000, 1.3
    vol_adjustment_factor = 2.928
    if volume_given < v_cone: # volume only in cone part
        liquid_height = (volume_given*vol_adjustment_factor/(np.pi * r**2)) * conversion_factor
    else: # volume also entering cylindrical part
        liquid_height = 23.36 +  ((volume_given-v_cone)/(np.pi * r**2)) * conversion_factor
    return round(liquid_height,2)
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

def calc_50ml_Falcon_height(volume_given,units='ml'):
    """
    Calculates height of liquid inside 50 ml Falcon tube, given only the liquid volume.
    In: float - liquid volume - in ml (default) or ul
    Out: float - liquid height in tube - in mm
    """
    r = 26/2 # 27.81/2 # units: mm; inner diameter as stored by Opentrons 
    # -> https://www.fishersci.co.uk/shop/products/falcon-50ml-conical-centrifuge-tubes-2/10788561 # opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical
    if units=='ul': # allows volume being given in 1µl or ml and height output always in mm
        conversion_factor, v_cone = 1, 3_215.297 # 1ml = 1_000 mm^3 ∴ 1µl = 1mm^3 
    elif units=='ml':
        conversion_factor, v_cone = 1_000, 3.215297 
    vol_adjustment_factor = 2.7
    if volume_given < v_cone: # volume only in cone part
        liquid_height = (volume_given*vol_adjustment_factor/(np.pi * r**2)) * conversion_factor
    else: # volume also entering cylindrical part
        liquid_height = 15.88 +  ((volume_given-v_cone)/(np.pi * r**2)) * conversion_factor
    return round(liquid_height,2)

# --------------------------------------------------------------------------------------------------------------------------------------------

