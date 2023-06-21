import bpy

# Delete all objects in the scene
for obj in bpy.data.objects:
    bpy.data.objects.remove(obj)

def simple_mm(width_l, length_l, height_l):
    """
    """
    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    bpy.context.object.dimensions = ( width_l, length_l, height_l)
    

def st_mm(tr_width_l, tr_length_l, tr_height_l, 
st_width_l, st_length_l, st_heigh_l):
    """
    """
    # create mesh & object for the main trench
    mesh_tr = bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    ob_tr = bpy.context.object
    bpy.context.object.dimensions = ( tr_width_l, tr_length_l, tr_height_l)
    ob_tr.name = 'TRENCH'
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
    bpy.context.object.modifiers["Boolean"].object = bpy.data.objects['TRENCH']
    bpy.context.object.modifiers["Boolean"].operation = 'UNION'
    bpy.ops.object.modifier_apply(modifier="Boolean")
    # delete trench, the leftover from the add modifier 
    object_to_delete = bpy.data.objects['TRENCH']
    bpy.data.objects.remove(object_to_delete, do_unlink=True)

    
      
## Set the dimensions of the objects
save_file = False
file_name = "221223_bpy_inlcuding_str.stl"
width = 1.6
height = 1.6
length = 80

st_width = 3
st_length = 90
st_height = 0.5

# Set the distance between the objects
spacing = 2


# Create the remaining objects and position them on the ground plane
for i in range(10):
    #simple_mm(width, length, height)
    #bpy.context.object.location.x += width + (spacing+width) * i
    st_mm(width, length, height, 
          st_width, st_length, st_height)
    
    bpy.context.object.location.x += width + (spacing+width+st_width*2) * i
    st_width += 1


# Select all objects in the scene
for obj in bpy.data.objects:
    obj.select_set(True)

# Set the options for the STL export
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.render.filepath = "/Users/camillomoschner/Desktop/" + file_name

# Export the selected objects to an STL file
if save_file:
    bpy.ops.export_mesh.stl(filepath=bpy.context.scene.render.filepath, use_selection=True)

