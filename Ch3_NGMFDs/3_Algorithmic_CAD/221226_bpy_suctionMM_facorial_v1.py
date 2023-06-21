# # # 221226_bpy_suctionMM_facorial_v1
# # # author: Camillo Moschner | date: 29.12.22

import bpy
import os
import sys
# Change working directory of this bpy file to file location
dir = os.path.dirname('/Users/camillomoschner/Desktop/PhD_thesis/Ch3_NGMFDs/2_2PP-PL_Hybrid/v5_procedural_feature_generation/')
if not dir in sys.path:
    sys.path.append(dir )
from proced_feat_gen_helper import *
import pandas as pd

# Delete all objects in the scene
for obj in bpy.data.objects:
    bpy.data.objects.remove(obj)
# - - - - - - - - - - - - - - - - - - - - - -- - - - - - - - - - - - - - - - - - - - - - 

tr_factorial_df = pd.read_csv('/Users/camillomoschner/Desktop/PhD_thesis/Ch3_NGMFDs/2_2PP-PL_Hybrid/v5_procedural_feature_generation/suctionmm_runs.csv')    
## Set the dimensions of the objects
save_file = False
file_name = "221226_bpy_smm_w_indices.stl"

# Set the distance between the objects
spacing = 2

# Create a string to store the output
output = ""
objects_x_dims = []
# Create the remaining objects and position them on the ground plane
new_x_pos=0
bkp_back_l = 45
#for i in range(10):
for repeats in range(0,1):
    # add repeats to comparisson along the entire FL
    for row in range(len(tr_factorial_df)): # len(tr_factorial_df)
        current_tr_info = tr_factorial_df.iloc[row,:]
        # add text as indices & fiduciaries
        if row%2==0:
            bpy.ops.object.text_add(enter_editmode=False, align='WORLD', 
            location=(new_x_pos - current_tr_info['tr_w']/2+2.2, 
            current_tr_info['tr_l']/2+0.4, 0), scale=(1, 1, 1))
            ob = bpy.context.scene.objects['Text']
            ob.name = 'tr_no'+str(row)
            ob.data.body = str(row)
            bpy.ops.object.editmode_toggle()
            text_height = 1
            bpy.context.object.data.extrude = text_height
            bpy.context.object.scale[0] = 1.8
            bpy.context.object.scale[1] = 1.8
            ob.location[0] = ob.location[0] - ob.dimensions[0]/2
            ob.location[2] = text_height
        # Add replicates next to each other
        for replicates in range(0,1):
            suction_mm(current_tr_info['tr_w'], current_tr_info['tr_l'], current_tr_info['tr_h'], 
         current_tr_info['tr_l']+bkp_back_l, current_tr_info['bkp_w'], bkport_length = 2)
            bpy.context.object.location.x = new_x_pos + current_tr_info['tr_w']/2#(tr_width+spacing) * i
            # Analyse latest generated object to adjust new location for next object
            active_object = bpy.context.view_layer.objects.active
            active_object.location[2] = current_tr_info['tr_h']/2
            output += f"Object: {active_object.name}\n"
            output += f"Dimensions: {active_object.dimensions}\n"
            output += f"Coordinates: {active_object.location}\n"
            objects_x_dims.append(active_object.location[0])
            
            new_x_pos = active_object.location[0] + spacing + current_tr_info['tr_w']/2
# - - - - - - - - - - - - - - - - - - - - - -- - - - - - - - - - - - - - - - - - - - - - 

# Copy the output string to the clipboard
output += f"\n# objects: {len(bpy.data.objects)}\n"
output += f"\nx range: {round(min(objects_x_dims),2)} - {round(max(objects_x_dims),2)}\n"
bpy.context.window_manager.clipboard = output

# Select all objects in the scene
for obj in bpy.data.objects:
    obj.select_set(True)

# Set the options for the STL export
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.render.filepath = "/Users/camillomoschner/Desktop/" + file_name

# Export the selected objects to an STL file
if save_file:
    bpy.ops.export_mesh.stl(filepath=bpy.context.scene.render.filepath, use_selection=True)

