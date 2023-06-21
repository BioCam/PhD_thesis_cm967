# Image Analysis Helper Functions File
# author: Camillo Moschner
# email: cm967@cam.ac.uk
# start: 28.04.2021

# import statements:
from PIL import Image
import numpy as np
import os 

from glob import glob
import matplotlib.pyplot as plt
from matplotlib.pyplot import imshow

import pandas as pd
import copy
from skimage.filters import gaussian

from scipy.signal import find_peaks
from skimage.transform import rotate

# --------------------------------------------------------------

# Function Defintions

# standard functions:
def convert_to_nparray(im_directory):
    # 1. use Pillow to open image file:
    im = Image.open(im_directory)
    # 2. use numpy arrary to convert Pillow object to Numpy array:
    im = np.asarray(im)
    return im

def crop_im_and_show(im, y_selection, x_selection): # probably have to try different crops for optimal selection
    # 3. crop image:
    cropped_im = im[y_selection,x_selection]
    # present 
    plt.figure(figsize=(15,15))
    imshow(cropped_im)
    return "Have you looked at muliple timepoints to check for stage drift?"

def invert_nparray(nparray_x):
    new_nparray_z = copy.deepcopy(nparray_x)
    indices_one = new_nparray_z == 1
    indices_zero = new_nparray_z == 0
    new_nparray_z[indices_one] = 0 # replacing 1s with 0s
    new_nparray_z[indices_zero] = 1 # replacing 0s with 1s
    return new_nparray_z

# In order to process each FOV you need to easily access the information of all the images in the folder containing the images. 
# To do so, create a Pandas DataFrame that contains all the images' info (directory, (lane - if applicable,) FOV, timepoint, colour_channel).

# CAREFUL: images have to be named like "xy000_T000_mCherry.png" for the following function to parse through them!

def source_image_info(ims_folder_directory,ims_format):
    """
    Takes image directory (str) and image format (str) (either 'tif' or 'png') from images saved with the standard
    FOV_timpoint_channel format and creates a DataFrame containing the info of all images in that directory.
    """
    ims_folder_directory = glob(ims_folder_directory+"*."+ims_format)
    ims_df = pd.DataFrame(ims_folder_directory, columns=['directory'])
    # conditional processing based on whether trenches have already been extracted:
    if len(ims_df['directory'].str.split(os.path.sep)[0][-1].split('_')) == 3: # for experiment format: FOV_timepoint_channel
        # 1- FOV:
        ims_df['FOV'] = ims_df['directory'].str.split(os.path.sep)
        # 2- timepoint:
        ims_df['timepoint'] = [directory[-1].split(os.path.sep)[0].split('_')[-2] for directory in ims_df['FOV']]
        ims_df['timepoint'] = ims_df['timepoint'].str.slice(start=1) # 'T0001' -> '0001'
        ims_df['timepoint'] = ims_df['timepoint'].astype(int)  # '0001' -> 1
        # 3- channel:
        ims_df['colour_channel'] = [directory[-1].split(os.path.sep)[0].split('_')[-1].split('.')[0] for directory in ims_df['FOV']]
        ims_df['FOV'] = [directory[-1].split(os.path.sep)[0].split('_')[-3] for directory in ims_df['FOV']]
        # sort the DataFrame & reset the index
        ims_df.sort_values(by=['FOV','timepoint','colour_channel'],inplace=True)
        ims_df.reset_index(drop=True, inplace=True)
        print("Dataframe with {:} rows and {:} columns has been created.".format(ims_df.shape[0],ims_df.shape[1]))
        print("# FOVs:", len(ims_df['FOV'].unique()), 
            "\n# timepoints/FOV:", len(ims_df['timepoint'].unique()), 
            "\n# colour channels/timepoint/FOV:", len(ims_df['colour_channel'].unique()))
    elif len(ims_df['directory'].str.split(os.path.sep)[0][-1].split('_')) == 4: # for experiment format: FOV_trench_channel_timepoint
        split_file_names = ims_df['directory'].str.split(os.path.sep)[0][-1].split('_')
        # 1- FOV:
        ims_df['FOV'] = [directory.split(os.path.sep)[-1].split('_')[0] for directory in ims_df['directory']]
        # 2- trench:
        ims_df['trench'] = [directory.split(os.path.sep)[-1].split('_')[1] for directory in ims_df['directory']]
        ims_df['trench'] = ims_df['trench'].str.slice(start=2) # 'tr001' -> '0001'
        ims_df['trench'] = ims_df['trench'].astype(int)  # '0001' -> 1
        # 3- channel:
        ims_df['colour_channel'] = [directory.split(os.path.sep)[-1].split('_')[2] for directory in ims_df['directory']]
        # 4- timepoint:
        ims_df['timepoint'] = [directory.split(os.path.sep)[-1].split('_')[3][:-4] for directory in ims_df['directory']]
        ims_df['timepoint'] = ims_df['timepoint'].str.slice(start=1) # 'T0001' -> '0001'
        ims_df['timepoint'] = ims_df['timepoint'].astype(int)  # '0001' -> 1
        
        # 5- sort the DataFrame & reset the index
        ims_df.sort_values(by=['FOV','trench','colour_channel','timepoint'],inplace=True)
        ims_df.reset_index(drop=True, inplace=True)

        # 6- calculate cumulative trench count:
        ims_df['trench_cum'] = ims_df['FOV']+'_'+ims_df['trench'].astype(str)
        trench_cum_list = []
        cum_trench_counter = 0
        for trench_id_unique in list(ims_df['trench_cum'].unique()):
            for trench_id in list(ims_df['trench_cum']):
                if trench_id == trench_id_unique:
                    trench_cum_list.append(cum_trench_counter)
            cum_trench_counter += 1
        ims_df.drop('trench_cum', axis = 1, inplace = True)
        ims_df['trench_cum'] = pd.DataFrame(trench_cum_list)
        print("Dataframe with {:} rows and {:} columns has been created.".format(ims_df.shape[0],ims_df.shape[1]))
        print("# FOVs:", len(ims_df['FOV'].unique()), 
              "# trenches:", len(ims_df['trench'].unique()), 
            "\n# timepoints/FOV:", len(ims_df['timepoint'].unique()), 
            "\n# colour channels/timepoint/FOV:", len(ims_df['colour_channel'].unique()))
    return ims_df

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def find_FOV_trench_peaks(PC_ims_info_df,im_timepoint,investigated_FOV,pixel_micron_conversion_factor,trench_distance_mcr, sigma=9, plot = False):
    """
    Takes phase contrast DataFrame of a the entire dataset (i.e. all FOVs) + the name of the FOV that needs to be investigated
    and calculates all peak intensities from the phase contrast image at the centre of the image.
    Out1: DataFrame containing entire PC intensities at line tested (index= x position, column1= x position in micron, column2= intensity)
    Out2: DataFrame containing only trench peak intensities (index= x position, column1= x position in micron, column2= intensity)
    """
    PC_im_nparr = convert_to_nparray( PC_ims_info_df.loc[PC_ims_info_df['FOV']==investigated_FOV]['directory'].iloc[im_timepoint] )
    # use gaussian blur to blur out small local differences in the image that might interfere with peak finiding:
    PC_im_nparr = gaussian(PC_im_nparr, sigma = sigma, preserve_range=True)
    # choose which horizontal line you want to use for trench peak identification:
    test_line_first_quarter = int(PC_im_nparr.shape[0]*0.25)
    test_line_middle = int(PC_im_nparr.shape[0]*0.5)
    test_line_third_quarter = int(PC_im_nparr.shape[0]*0.75)
    
    def create_intensity_profile(pc_np_array,test_y_line):
        local_PC_hor_intensity_profile = pd.DataFrame(data=PC_im_nparr[test_y_line,:])
        print('FOV {:}: Horizontal phase contrast intensity profile - line {:}\n'.format(investigated_FOV,test_y_line))
        #PC_hor_intensity_profile.plot(figsize=(15,5));
        local_PC_hor_intensity_profile.reset_index(inplace=True)
        local_PC_hor_intensity_profile['index'] = PC_hor_intensity_profile['index'] * pixel_micron_conversion_factor
        local_PC_hor_intensity_profile.rename(columns={0: "intensity",'index':'position_micron'},inplace=True)
        return local_PC_hor_intensity_profile
    
    PC_hor_intensity_profile_first_quarter = create_intensity_profile(PC_im_nparr,test_line_first_quarter)
    PC_hor_intensity_profile_middle = create_intensity_profile(PC_im_nparr,test_line_middle)
    PC_hor_intensity_profile_third_quarter = create_intensity_profile(PC_im_nparr,test_line_third_quarter)
    PC_hor_intensity_profile = pd.concat((PC_hor_intensity_profile_first_quarter, PC_hor_intensity_profile_middle,
                                          PC_hor_intensity_profile_third_quarter))
    PC_hor_intensity_profile.groupby(PC_hor_intensity_profile.intensity).mean()
    print(PC_hor_intensity_profile_first_quarter, PC_hor_intensity_profile_middle,
                                          PC_hor_intensity_profile_third_quarter)
    # find trench intensity peaks:
    peaks = find_peaks(np.array(PC_hor_intensity_profile['intensity']), distance=trench_distance_mcr/pixel_micron_conversion_factor)
    peaks_intensities = PC_hor_intensity_profile.loc[peaks[0].tolist(),:]
    print("{:} trenches identified in FOV {:}.".format(len(peaks_intensities),investigated_FOV))
    # plot intensity profile w/ annotated peaks:
    if plot == True:
        plt.figure(figsize=(15,5))
        plt.plot(PC_hor_intensity_profile['position_micron'],PC_hor_intensity_profile['intensity']);
        plt.plot(peaks_intensities['position_micron'],peaks_intensities['intensity'], "x")
        plt.title('FOV {:} Phase Contrast Intensity Profile at Row {:}'.format(investigated_FOV,test_line))
        plt.xlabel('micron')
        plt.ylabel('phase contrast intensity')
    #plt.close()
    return PC_hor_intensity_profile,peaks_intensities

def create_FOV_trench_mask(PC_image,investigated_FOV, FOV_peakdata,pixel_micron_conversion_factor,trench_distance_mcr, plot=False):
    """Out: np array of trench mask
    """
    # Define necessary MFD and imaging information:
    trench_distance_pixels = int(trench_distance_mcr/pixel_micron_conversion_factor)
    # create rough trench mask:
    trench_mask = np.zeros(PC_image.shape)
    im_margin = 10
    print("Trench mask with dimensions {:} has been created.".format(trench_mask[im_margin:trench_mask.shape[0]-im_margin,:].shape))
    for index in FOV_peakdata.index.tolist():
        trench_mask[im_margin:trench_mask.shape[0]-im_margin,index-int(trench_distance_pixels/4):index+int(trench_distance_pixels/4)] = 1
    if plot == True:
        plt.figure(figsize=(15,5))
        imshow(trench_mask)
        plt.title('FOV {:} Trench Mask'.format(investigated_FOV))
        #plt.xlabel('micron')
        #plt.ylabel('phase contrast intensity')
    return trench_mask


def find_merged_segm_FOV_trench_peaks(merged_currentFOV_segm_im,pixel_micron_conversion_factor,trench_distance_mcr,sigma, plot=False):
    """Out: peaks
    """
    merged_currentFOV_segm_im = gaussian(merged_currentFOV_segm_im, sigma = sigma, preserve_range=True)
    test_line_first_quarter = int(merged_currentFOV_segm_im.shape[0]*0.25)
    test_line_middle = int(merged_currentFOV_segm_im.shape[0]*0.5)
    test_line_third_quarter = int(merged_currentFOV_segm_im.shape[0]*0.75)
    def create_intensity_profile(segm_np_array,test_y_line):
        # initiate DataFrame:
        segm_hor_intensity_profile = pd.DataFrame(data=segm_np_array[test_y_line,:])
        segm_hor_intensity_profile.reset_index(inplace=True)
        segm_hor_intensity_profile['index'] = segm_hor_intensity_profile['index'] * pixel_micron_conversion_factor
        segm_hor_intensity_profile.rename(columns={0: "intensity",'index':'position_micron'},inplace=True)
        return segm_hor_intensity_profile
    segm_hor_intensity_profile_first_quarter = create_intensity_profile(merged_currentFOV_segm_im,test_line_first_quarter)
    segm_hor_intensity_profile_middle = create_intensity_profile(merged_currentFOV_segm_im,test_line_middle)
    segm_hor_intensity_profile_third_quarter = create_intensity_profile(merged_currentFOV_segm_im,test_line_third_quarter)
    
    all_three_intensity_profiles = pd.concat([segm_hor_intensity_profile_first_quarter['intensity'], segm_hor_intensity_profile_middle['intensity'], segm_hor_intensity_profile_third_quarter['intensity']],axis=1)
    segm_hor_intensity_profile = segm_hor_intensity_profile_middle
    segm_hor_intensity_profile['intensity']= all_three_intensity_profiles.mean(axis=1)
    segm_hor_intensity_profile
    # identify peaks:
    peaks = find_peaks(np.array(segm_hor_intensity_profile['intensity']), distance=trench_distance_mcr/pixel_micron_conversion_factor)
    peaks_intensities = segm_hor_intensity_profile.loc[peaks[0].tolist(),:]
    # show plot if wanted:
    if plot == True:
        plt.figure(figsize=(15,5))
        plt.plot(segm_hor_intensity_profile['position_micron'],segm_hor_intensity_profile['intensity']);
        plt.plot(peaks_intensities['position_micron'],peaks_intensities['intensity'], "x")
        plt.title(f"Segmentation Intensity Mean Profile between Rows {test_line_first_quarter, test_line_middle, test_line_third_quarter}")
        plt.xlabel('micron')
        plt.ylabel('segm. marker contrast intensity (added)')
    return segm_hor_intensity_profile,peaks_intensities
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 


## Physcial Characteristics
#(1) Micrograph and (2) Mother Machine parameters
#(1) is given in the .nd2 file. Open it with the NIS Viewer; bottom of the screen will tell you micron/pixel | (2) has to be known by the user and influence the choice of Mother Machine that you use for the experiment in the first place
pixel_micron_conversion = 0.10921 # (1) unit: micron/pixel
trench_distance = 10 # (2) unit: micron
trench_width = 1.0 # (2) unit: micron

# Calculate ~min and ~max surface area for stationary E. coli cell with width=0.7-1.4 micron and length=1 micron:
true_surface_area_micr_per_pixel = pixel_micron_conversion**2 # unit: micron^2/pixel

min_cell_width = 0.7 # unit: micron | standard=0.7
max_cell_width = 1.4 # unit: micron
min_cell_length = 1 # unit: micron
max_cell_length = 7 # unit: micron

min_cell_area_total = min_cell_width*min_cell_length # unit: micron^2

min_pixel_area_per_cell = min_cell_area_total/true_surface_area_micr_per_pixel # unit: pixel

sqmicron_pixel_conversion_factor = 1/(pixel_micron_conversion**2) # unit: micron^2/pixel
