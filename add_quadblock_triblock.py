import bpy
import bmesh
from mathutils import Vector

# Function to extrude selected vertices without moving them
def extrude_vertices(obj):
    # Switch to Edit mode
    bpy.ops.object.mode_set(mode='EDIT')

    # Select all vertices
    bpy.ops.mesh.select_all(action='SELECT')

    # Extrude vertices but keep them in the same location
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, 0)})

    # Switch back to Object mode
    bpy.ops.object.mode_set(mode='OBJECT')

# Function to separate the extruded vertices by selection
def separate_by_selection(obj):
    # Switch to Edit mode
    bpy.ops.object.mode_set(mode='EDIT')

    # Select all vertices
    bpy.ops.mesh.select_all(action='SELECT')

    # Separate by selection
    bpy.ops.mesh.separate(type='SELECTED')

    # Switch back to Object mode
    bpy.ops.object.mode_set(mode='OBJECT')

# Function to join two objects together
def join_objects(obj1, obj2):
    # Set the active object
    bpy.context.view_layer.objects.active = obj1

    # Select both objects
    obj1.select_set(True)
    obj2.select_set(True)

    # Join the objects
    bpy.ops.object.join()

# Function to create a face and subdivide the geometry
def fill_and_subdivide(obj):
    # Switch to Edit mode
    bpy.ops.object.mode_set(mode='EDIT')

    # Select all vertices
    bpy.ops.mesh.select_all(action='SELECT')

    # Fill the selected vertices (creating a face)
    bpy.ops.mesh.face_make_planar()

    # Switch back to Object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Subdivide the object
    subdivide_new_object(obj)

# Function to subdivide only the newly created object
def subdivide_new_object(new_obj):
    # Ensure we are in Object mode before operations
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Select and activate the newly created object
    new_obj.select_set(True)
    bpy.context.view_layer.objects.active = new_obj

    # Switch to Edit mode and subdivide
    bpy.ops.object.mode_set(mode='EDIT')  # Enter Edit mode
    bpy.ops.mesh.select_all(action='SELECT')  # Select all geometry
    bpy.ops.mesh.subdivide(number_cuts=1)  # Subdivide
    bpy.ops.object.mode_set(mode='OBJECT')  # Return to Object mode

# Function to get the coordinates of the selected vertices
def get_selected_vertices():
    """
    Retrieve the world coordinates of selected vertices in Edit mode.

    Returns:
        list of Vector: The selected vertices' world coordinates.
    """
    selected_verts = []
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH' and obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
            selected_verts.extend([obj.matrix_world @ v.co for v in bm.verts if v.select])
    return selected_verts

# Operator for the extrusion process
class OBJECT_OT_ExtrudeAndSubdivide(bpy.types.Operator):
    """
    Extrude the selected vertices, separate them, join the objects, and create a face with subdivision.
    """
    bl_idname = "mesh.extrude_and_subdivide"
    bl_label = "Extrude and Subdivide"

    def execute(self, context):
        # Get the selected vertices
        selected_verts = get_selected_vertices()
        
        # Ensure we have either 3 or 4 selected vertices
        if len(selected_verts) == 3 or len(selected_verts) == 4:
            # Extrude the selected vertices
            extrude_vertices(context.active_object)

            # Separate the extruded vertices
            separate_by_selection(context.active_object)

            # Get the new objects created after separation
            obj1 = context.active_object
            obj2 = bpy.context.view_layer.objects.active

            # Join the two objects together
            join_objects(obj1, obj2)

            # Create a face and subdivide the geometry
            fill_and_subdivide(obj1)

            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Select exactly 3 or 4 vertices.")
            return {'CANCELLED'}

# Panel for the buttons in the "Tools" tab
class VIEW3D_PT_InsertShapesPanel(bpy.types.Panel):
    """
    UI Panel to insert shapes in the 3D Viewport.
    """
    bl_label = "Extrude and Subdivide"
    bl_idname = "VIEW3D_PT_extrude_subdivide"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.extrude_and_subdivide")

# Register operators and panel
def register():
    bpy.utils.register_class(OBJECT_OT_ExtrudeAndSubdivide)
    bpy.utils.register_class(VIEW3D_PT_InsertShapesPanel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_ExtrudeAndSubdivide)
    bpy.utils.unregister_class(VIEW3D_PT_InsertShapesPanel)

if __name__ == "__main__":
    register()
