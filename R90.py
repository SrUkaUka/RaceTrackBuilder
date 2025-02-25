import bpy
import bmesh
import mathutils

# Function to calculate the centroid of all vertices
def calculate_centroid(verts):
    total = mathutils.Vector((0.0, 0.0, 0.0))
    for v in verts:
        total += v.co
    return total / len(verts)

# Function to find the closest vertex that hasn't been registered yet
def closest_vertex(obj, current_vertex, visited_vertices, centroid):
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()  # Update the vertex lookup table
    min_distance = float('inf')
    closest_vertex = None

    for v in bm.verts:
        if v.index in visited_vertices:
            continue
        distance = (v.co - current_vertex.co).length
        # Exclude the centroid from the search
        if (v.co - centroid).length < 1e-5:  # Tolerance for centering with the centroid
            continue
        if distance < min_distance:
            min_distance = distance
            closest_vertex = v

    return closest_vertex

# Custom operator to find and register the closest vertices
class MESH_OT_find_vertices(bpy.types.Operator):
    bl_idname = "mesh.find_vertices"
    bl_label = "Find Closest Vertices"
    bl_options = {'REGISTER', 'UNDO'}

    # Attribute to store the list of selected vertices
    vertex_list = []

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}

        # Clear the list before each execution
        MESH_OT_find_vertices.vertex_list.clear()

        # Switch to edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        # Ensure the lookup table is updated
        bm.verts.ensure_lookup_table()

        # Select all vertices and calculate the centroid
        bpy.ops.mesh.select_all(action='SELECT')
        centroid = calculate_centroid(bm.verts)
        print(f"Centroid: {centroid}")

        # Find the closest vertex to the centroid
        initial_vertex = min(bm.verts, key=lambda v: (v.co - centroid).length)
        visited_vertices = {initial_vertex.index}

        # Print the coordinates and index of the automatically selected vertex
        print(f"Index of the initially selected vertex: {initial_vertex.index}")
        print(f"Coordinates of the initially selected vertex: {initial_vertex.co}")

        # Select the initial vertex
        initial_vertex.select = True
        bmesh.update_edit_mesh(obj.data)

        # Loop to find and select closest vertices one by one
        while True:
            # Find the closest unvisited vertex
            closest_vertex_found = closest_vertex(obj, initial_vertex, visited_vertices, centroid)

            if closest_vertex_found is None:
                print("No closest vertex found")
                break

            # Deselect the previous vertex and select the new closest vertex
            initial_vertex.select = False
            closest_vertex_found.select = True

            # Update the initial vertex
            initial_vertex = closest_vertex_found
            visited_vertices.add(closest_vertex_found.index)

            # Register the new vertex in the list
            MESH_OT_find_vertices.vertex_list.append(
                (closest_vertex_found.index, closest_vertex_found.co.copy())
            )

            # Update the mesh in edit mode
            bmesh.update_edit_mesh(obj.data)

        # Print the complete list of selected vertices at the end
        print("\nList of selected vertices (Index, Coordinates):")
        for idx, co in MESH_OT_find_vertices.vertex_list:
            print(f"Index: {idx}, Coordinates: {co}")

        return {'FINISHED'}

# Operator to rotate the vertices 90 degrees clockwise
class MESH_OT_rotate_vertices(bpy.types.Operator):
    bl_idname = "mesh.rotate_vertices"
    bl_label = "R90"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Find the vertices before rotating
        bpy.ops.mesh.find_vertices()

        if not MESH_OT_find_vertices.vertex_list:
            self.report({'ERROR'}, "No vertices registered in the list")
            return {'CANCELLED'}

        # Create a copy of the vertex list
        rotated_list = MESH_OT_find_vertices.vertex_list[-2:] + MESH_OT_find_vertices.vertex_list[:-2]

        # Update the coordinates of the vertices in the mesh
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        for i, (index, _) in enumerate(rotated_list):
            bm.verts[index].co = MESH_OT_find_vertices.vertex_list[i][1]

        # Update the mesh
        bmesh.update_edit_mesh(obj.data)

        # Print the rotated vertex list
        print("\nList of rotated vertices and updated positions (Index, Coordinates):")
        for idx, co in rotated_list:
            print(f"Index: {idx}, Coordinates: {co}")

        return {'FINISHED'}

# Operator to rotate the vertices 90 degrees counterclockwise
class MESH_OT_rotate_vertices_left(bpy.types.Operator):
    bl_idname = "mesh.rotate_vertices_left"
    bl_label = "R-90"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Find the vertices before rotating
        bpy.ops.mesh.find_vertices()

        if not MESH_OT_find_vertices.vertex_list:
            self.report({'ERROR'}, "No vertices registered in the list")
            return {'CANCELLED'}

        # Create a copy of the vertex list and rotate it
        rotated_list = MESH_OT_find_vertices.vertex_list[2:] + MESH_OT_find_vertices.vertex_list[:2]

        # Update the coordinates of the vertices in the mesh
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        for i, (index, _) in enumerate(rotated_list):
            bm.verts[index].co = MESH_OT_find_vertices.vertex_list[i][1]

        # Update the mesh
        bmesh.update_edit_mesh(obj.data)

        # Print the rotated vertex list
        print("\nList of rotated vertices and updated positions (Index, Coordinates):")
        for idx, co in rotated_list:
            print(f"Index: {idx}, Coordinates: {co}")

        return {'FINISHED'}

# Custom panel in Blender
class VIEW3D_PT_custom_panel(bpy.types.Panel):
    bl_label = "Rotate 90"
    bl_idname = "VIEW3D_PT_custom_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.find_vertices", text="Find Closest Vertices")
        layout.operator("mesh.rotate_vertices", text="R90")
        layout.operator("mesh.rotate_vertices_left", text="R-90")  # Button for counterclockwise rotation

        # Display the list of vertices in the panel after execution
        if MESH_OT_find_vertices.vertex_list:
            box = layout.box()
            box.label(text="List of Vertices:")
            for idx, co in MESH_OT_find_vertices.vertex_list:
                box.label(text=f"Index: {idx}, Coord: {co}")

# Register classes
def register():
    bpy.utils.register_class(MESH_OT_find_vertices)
    bpy.utils.register_class(MESH_OT_rotate_vertices)
    bpy.utils.register_class(MESH_OT_rotate_vertices_left)  # Register the R-90 operator
    bpy.utils.register_class(VIEW3D_PT_custom_panel)

def unregister():
    bpy.utils.unregister_class(MESH_OT_find_vertices)
    bpy.utils.unregister_class(MESH_OT_rotate_vertices)
    bpy.utils.unregister_class(MESH_OT_rotate_vertices_left)  # Unregister the R-90 operator
    bpy.utils.unregister_class(VIEW3D_PT_custom_panel)

if __name__ == "__main__":
    register()
