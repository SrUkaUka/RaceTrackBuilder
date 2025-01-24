import bpy
import bmesh
from mathutils import Vector
import math

# Function to order vertices in a counterclockwise direction
def order_vertices(vertices):
    center = sum(vertices, Vector()) / len(vertices)
    sorted_verts = sorted(vertices, key=lambda v: math.atan2(v.y - center.y, v.x - center.x))
    return sorted_verts

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

# Function to create a plane with 4 vertices (quadblock)
def insert_quadblock(context, vertices):
    """
    Create a quad (4-sided polygon) based on the selected vertices.

    Parameters:
        context (bpy.context): Blender context.
        vertices (list of Vector): List of 4 vertices to define the quad.

    Returns:
        obj (bpy.types.Object): The newly created quad object.
    """
    if len(vertices) != 4:
        return {'CANCELLED'}

    ordered_verts = order_vertices(vertices)
    mesh = bpy.data.meshes.new(name="QuadBlock")
    obj = bpy.data.objects.new(name="QuadBlockObject", object_data=mesh)

    context.collection.objects.link(obj)  # Add to the active collection

    bm = bmesh.new()
    vert_dict = {idx: bm.verts.new(vert) for idx, vert in enumerate(ordered_verts)}
    bm.verts.ensure_lookup_table()
    bm.faces.new([vert_dict[i] for i in range(4)])  # Create the face
    bm.to_mesh(mesh)
    bm.free()

    # Subdivide the created object
    subdivide_new_object(obj)

    return obj

# Function to create a triangle with 3 vertices (triblock)
def insert_triblock(context, vertices):
    """
    Create a triangle (3-sided polygon) based on the selected vertices.

    Parameters:
        context (bpy.context): Blender context.
        vertices (list of Vector): List of 3 vertices to define the triangle.

    Returns:
        obj (bpy.types.Object): The newly created triangle object.
    """
    if len(vertices) != 3:
        return {'CANCELLED'}

    ordered_verts = order_vertices(vertices)
    mesh = bpy.data.meshes.new(name="TriBlock")
    obj = bpy.data.objects.new(name="TriBlockObject", object_data=mesh)

    context.collection.objects.link(obj)  # Add to the active collection

    bm = bmesh.new()
    vert_dict = {idx: bm.verts.new(vert) for idx, vert in enumerate(ordered_verts)}
    bm.verts.ensure_lookup_table()
    bm.faces.new([vert_dict[i] for i in range(3)])  # Create the face
    bm.to_mesh(mesh)
    bm.free()

    # Subdivide the created object
    subdivide_new_object(obj)

    return obj

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

# Operator for "Insert Quadblock"
class OBJECT_OT_InsertQuadblock(bpy.types.Operator):
    """
    Insert a quad quadblock by selecting 4 vertices.
    """
    bl_idname = "mesh.insert_quadblock"
    bl_label = "Insert Quadblock"

    def execute(self, context):
        selected_verts = get_selected_vertices()
        if len(selected_verts) == 4:
            insert_quadblock(context, selected_verts)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Select exactly 4 vertices.")
            return {'CANCELLED'}

# Operator for "Insert Triblock"
class OBJECT_OT_InsertTriblock(bpy.types.Operator):
    """
    Insert a quad triblock by selecting 3 vertices.
    """
    bl_idname = "mesh.insert_triblock"
    bl_label = "Insert Triblock"

    def execute(self, context):
        selected_verts = get_selected_vertices()
        if len(selected_verts) == 3:
            insert_triblock(context, selected_verts)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Select exactly 3 vertices.")
            return {'CANCELLED'}

# Panel for the buttons in the "Tools" tab
class VIEW3D_PT_InsertShapesPanel(bpy.types.Panel):
    """
    UI Panel to insert shapes in the 3D Viewport.
    """
    bl_label = "Insert Shapes"
    bl_idname = "VIEW3D_PT_insert_shapes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.insert_quadblock")
        layout.operator("mesh.insert_triblock")

# Register operators and panel
def register():
    bpy.utils.register_class(OBJECT_OT_InsertQuadblock)
    bpy.utils.register_class(OBJECT_OT_InsertTriblock)
    bpy.utils.register_class(VIEW3D_PT_InsertShapesPanel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_InsertQuadblock)
    bpy.utils.unregister_class(OBJECT_OT_InsertTriblock)
    bpy.utils.unregister_class(VIEW3D_PT_InsertShapesPanel)

if __name__ == "__main__":
    register()
