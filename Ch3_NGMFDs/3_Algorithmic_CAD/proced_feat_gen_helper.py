# # # Procedural Feature Generation w/ Blender Helper File
# # # author: Camillo Moschner | date: 29.12.22

import bpy
import pandas as pd


# FUNCTIONS
# - - - - - - - - - - - - - - - - - - - - - -- - - - - - - - - - - - - - - - - - - - - - 
def simple_mm(width_l, length_l, height_l):
    """
    """
    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    bpy.context.object.dimensions = ( width_l, length_l, height_l)
# - - - - - - - - - - - - - - - - - - - - - -- - - - - - - - - - - - - - - - - - - - - - 
def st_mm(tr_width_l, tr_length_l, tr_height_l, 
st_width_l, st_length_l, st_heigh_l):
    """
    """
    # create mesh & object for the main trench
    mesh_tr = bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    ob_tr = bpy.context.object
    bpy.context.object.dimensions = ( tr_width_l, tr_length_l, tr_height_l)
    ob_tr.name = 'ST_TRENCH'
    # calculate total dimensions of the side trenches
    st_width_total = tr_width_l + 2 *st_width_l
    st_z_position = (tr_height_l - st_heigh_l) / 2
    st_y_position = (tr_length_l - st_length_l) / 2
    # create mesh & object for the side trenches
    st_mesh = bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, -st_y_position, -st_z_position))
    ob_st = bpy.context.object
    bpy.context.object.dimensions = ( st_width_total, st_length_l, st_heigh_l)
    ob_st.name = 'SIDE-TRENCH'
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = bpy.data.objects['ST_TRENCH']
    bpy.context.object.modifiers["Boolean"].operation = 'UNION'
    bpy.ops.object.modifier_apply(modifier="Boolean")
    # delete trench, the leftover from the add modifier 
    object_to_delete = bpy.data.objects['ST_TRENCH']
    bpy.data.objects.remove(object_to_delete, do_unlink=True)
# - - - - - - - - - - - - - - - - - - - - - -- - - - - - - - - - - - - - - - - - - - - - 
def suction_mm(tr_width_l, tr_length_l, tr_height_l, 
         total_tr_length_l, bkport_width_l, bkport_length = 3):
    """
    """
    # calculate extra starting positions
    bkport_x_position = bkport_width_l
    bkport_y_position = tr_length_l / 2 + bkport_length / 2
    tr_y_position = (total_tr_length_l - tr_length_l) / 2
    # create mesh & object for the side trenches
    bkport_mesh = bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(bkport_x_position, bkport_y_position, 0))
    bkport_st = bpy.context.object
    bpy.context.object.dimensions = ( tr_width_l, bkport_length, tr_height_l)
    bkport_st.name = 'BKPORT-SECTION'
    # create mesh & object for the main trench
    mesh_tr = bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, tr_y_position, 0))
    ob_tr = bpy.context.object
    bpy.context.object.dimensions = ( tr_width_l, total_tr_length_l, tr_height_l)
    ob_tr.name = 'TRENCH'
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = bpy.data.objects['BKPORT-SECTION']
    bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
    bpy.ops.object.modifier_apply(modifier="Boolean")
    # delete trench, the leftover from the add modifier 
    object_to_delete = bpy.data.objects['BKPORT-SECTION']
    bpy.data.objects.remove(object_to_delete, do_unlink=True)