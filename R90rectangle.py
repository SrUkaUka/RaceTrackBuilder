import bpy
import bmesh

# Custom operator to select the vertices of a rectangle (3x3)
class MESH_OT_select_rectangle(bpy.types.Operator):
    bl_idname = "mesh.select_rectangle"
    bl_label = "Select Rectangle Vertices"
    bl_options = {'REGISTER', 'UNDO'}
    
    rectangle_vertices_list = []

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}

        # Clear the list before each execution
        MESH_OT_select_rectangle.rectangle_vertices_list.clear()

        # Switch to edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        # Ensure the lookup table is updated
        bm.verts.ensure_lookup_table()

        # Deselect all vertices
        bpy.ops.mesh.select_all(action='DESELECT')
        vertices = sorted(bm.verts, key=lambda v: (v.co.y, v.co.x))  # Sort by position

        if len(vertices) < 9:
            self.report({'ERROR'}, "Not enough vertices (9 vertices required)")
            return {'CANCELLED'}

        # Select the first 9 vertices and store them
        for i in range(9):
            vert = vertices[i]
            vert.select = True
            MESH_OT_select_rectangle.rectangle_vertices_list.append((vert.index, vert.co.copy()))

        # Update the mesh in edit mode
        bmesh.update_edit_mesh(obj.data)

        # Print the full list of selected vertices
        print("\nList of selected vertices (Index, Coordinates):")
        for idx, co in MESH_OT_select_rectangle.rectangle_vertices_list:
            print(f"Index: {idx}, Coordinates: {co}")

        return {'FINISHED'}

# Operator to rotate the vertices 90 degrees clockwise
class MESH_OT_rotate_vertices_90(bpy.types.Operator):
    bl_idname = "mesh.rotate_vertices_90"
    bl_label = "Rotate Vertices 90"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Make sure the vertices are selected before rotating
        bpy.ops.mesh.select_rectangle()  # Automatically call the vertex selection

        if not MESH_OT_select_rectangle.rectangle_vertices_list:
            self.report({'ERROR'}, "No vertices registered in the list")
            return {'CANCELLED'}

        # Indices of a 3x3 mesh in clockwise direction
        rotation_indices = [6, 3, 0, 7, 4, 1, 8, 5, 2]
        current_coordinates = [co for _, co in MESH_OT_select_rectangle.rectangle_vertices_list]
        
        # Assign the rotated coordinates to the corresponding vertices
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        for i, new_idx in enumerate(rotation_indices):
            bm.verts[MESH_OT_select_rectangle.rectangle_vertices_list[i][0]].co = current_coordinates[new_idx]

        # Update the mesh
        bmesh.update_edit_mesh(obj.data)

        print("\nList of rotated vertices and updated positions:")
        for idx, co in MESH_OT_select_rectangle.rectangle_vertices_list:
            print(f"Index: {idx}, Coordinates: {co}")

        return {'FINISHED'}

# Operator to rotate the vertices 90 degrees counterclockwise
class MESH_OT_rotate_vertices_neg_90(bpy.types.Operator):
    bl_idname = "mesh.rotate_vertices_neg_90"
    bl_label = "Rotate Vertices -90"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Make sure the vertices are selected before rotating
        bpy.ops.mesh.select_rectangle()  # Automatically call the vertex selection

        if not MESH_OT_select_rectangle.rectangle_vertices_list:
            self.report({'ERROR'}, "No vertices registered in the list")
            return {'CANCELLED'}

        # Indices of a 3x3 mesh in counterclockwise direction
        rotation_indices = [2, 5, 8, 1, 4, 7, 0, 3, 6]
        current_coordinates = [co for _, co in MESH_OT_select_rectangle.rectangle_vertices_list]
        
        # Assign the rotated coordinates to the corresponding vertices
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        for i, new_idx in enumerate(rotation_indices):
            bm.verts[MESH_OT_select_rectangle.rectangle_vertices_list[i][0]].co = current_coordinates[new_idx]

        # Update the mesh
        bmesh.update_edit_mesh(obj.data)

        print("\nList of rotated vertices and updated positions:")
        for idx, co in MESH_OT_select_rectangle.rectangle_vertices_list:
            print(f"Index: {idx}, Coordinates: {co}")

        return {'FINISHED'}

# Custom panel in Blender
class VIEW3D_PT_custom_panel(bpy.types.Panel):
    bl_label = "Rotate Rectangle Vertices"
    bl_idname = "VIEW3D_PT_custom_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.rotate_vertices_90", text="Rotate Vertices 90")
        layout.operator("mesh.rotate_vertices_neg_90", text="Rotate Vertices -90")

# Register classes
def register():
    bpy.utils.register_class(MESH_OT_select_rectangle)
    bpy.utils.register_class(MESH_OT_rotate_vertices_90)
    bpy.utils.register_class(MESH_OT_rotate_vertices_neg_90)
    bpy.utils.register_class(VIEW3D_PT_custom_panel)

def unregister():
    bpy.utils.unregister_class(MESH_OT_select_rectangle)
    bpy.utils.unregister_class(MESH_OT_rotate_vertices_90)
    bpy.utils.unregister_class(MESH_OT_rotate_vertices_neg_90)
    bpy.utils.unregister_class(VIEW3D_PT_custom_panel)

if __name__ == "__main__":
    register()
