import bpy
import bmesh
from mathutils import Vector, kdtree

# -------------------------------
# Operator: Activate Snap (Closest/Vertex)
# -------------------------------
class SnapSettingsOperator(bpy.types.Operator):
    """Activates Snap with 'Closest' method and 'Vertex' element"""
    bl_idname = "view3d.snap_settings_operator"
    bl_label = "Activate Snap Closest to Vertex"

    def execute(self, context):
        context.scene.tool_settings.use_snap = True
        context.scene.tool_settings.snap_target = 'CLOSEST'
        context.scene.tool_settings.snap_elements = {'VERTEX'}
        self.report({'INFO'}, "Snap activated: Closest and Vertex")
        return {'FINISHED'}

# -------------------------------
# Operator: Disable Snap
# -------------------------------
class DisableSnapOperator(bpy.types.Operator):
    """Disables Snap"""
    bl_idname = "view3d.disable_snap_operator"
    bl_label = "Disable Snap"

    def execute(self, context):
        context.scene.tool_settings.use_snap = False
        self.report({'INFO'}, "Snap disabled")
        return {'FINISHED'}

# -------------------------------
# Operator: Snap selected vertices to the closest ones
# -------------------------------
class SnapVertexToClosestOperator(bpy.types.Operator):
    """Snaps selected vertices from multiple objects to the closest vertex of other objects"""
    bl_idname = "view3d.snap_vertex_to_closest_operator"
    bl_label = "Snap Selected Vertices to Closest Vertices"

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if len(selected_objects) < 2:
            self.report({'WARNING'}, "Select at least two mesh objects.")
            return {'CANCELLED'}

        active_object = selected_objects[0]
        reference_objects = selected_objects[1:]
        bpy.ops.object.mode_set(mode='OBJECT')

        # Get the global coordinates of reference vertices
        reference_vertices_global = []
        for ref_obj in reference_objects:
            reference_vertices_global.extend([ref_obj.matrix_world @ v.co for v in ref_obj.data.vertices])
        if not reference_vertices_global:
            self.report({'WARNING'}, "No vertices found in the reference objects.")
            return {'CANCELLED'}

        # Process the selected vertices of the active object
        bm = bmesh.new()
        bm.from_mesh(active_object.data)
        selected_vertices = [v for v in bm.verts if v.select]
        if not selected_vertices:
            bm.free()
            self.report({'WARNING'}, "No vertices selected in the active object.")
            return {'CANCELLED'}

        for v in selected_vertices:
            global_v_co = active_object.matrix_world @ v.co
            closest_vertex_global = min(reference_vertices_global, key=lambda v2_co: (global_v_co - v2_co).length)
            local_closest_co = active_object.matrix_world.inverted() @ closest_vertex_global
            v.co = local_closest_co

        bm.to_mesh(active_object.data)
        bm.free()
        active_object.data.update()

        self.report({'INFO'}, "Vertices adjusted successfully.")
        return {'FINISHED'}

# -------------------------------
# Operator: Attach by Distance (Optimized with KDTree)
# -------------------------------
class AttachByDistanceOperator(bpy.types.Operator):
    """Snaps vertices of separate objects without merging them, based on a distance threshold.

    Collects all vertices from selected MESH objects and groups those within 
    the specified threshold. If a group has vertices that do not yet share 
    the same position, they snap to the position of a representative vertex.
    """
    bl_idname = "view3d.attach_by_distance_operator"
    bl_label = "Attach by Distance"

    distance_threshold: bpy.props.FloatProperty(
        name="Distance Threshold",
        description="Maximum distance for snapping vertices",
        default=0.1,
        min=0.0
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # Collect all selected MESH objects
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objects:
            self.report({'WARNING'}, "No mesh objects selected.")
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Prepare a dictionary with the bmesh of each object and a global list of vertices
        bm_dict = {}
        global_verts = []  # List of tuples: (global_co, (obj, bm_vert))

        for obj in selected_objects:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            bm_dict[obj] = bm
            for v in bm.verts:
                global_co = obj.matrix_world @ v.co
                global_verts.append((global_co, (obj, v)))

        n = len(global_verts)
        if n == 0:
            self.report({'WARNING'}, "No vertices found.")
            return {'CANCELLED'}

        parent = list(range(n))

        # Union-Find functions to group vertices
        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_j] = root_i

        thresh = self.distance_threshold
        epsilon = 1e-6

        # Create KDTree for efficient neighbor searching
        kd = kdtree.KDTree(n)
        for i, (co, _) in enumerate(global_verts):
            kd.insert(co, i)
        kd.balance()

        # Use KDTree to find neighbors within the threshold
        for i, (co, _) in enumerate(global_verts):
            for (_, j, dist) in kd.find_range(co, thresh):
                if i != j:
                    union(i, j)

        # Organize clusters in a dictionary: id_cluster -> list of indices
        clusters = {}
        for i in range(n):
            root = find(i)
            clusters.setdefault(root, []).append(i)

        changes = 0
        # Process each cluster with more than one vertex
        for cluster_indices in clusters.values():
            if len(cluster_indices) < 2:
                continue  # Isolated vertex; do nothing

            # Choose a representative position (e.g., the first vertex in the group)
            rep_co = global_verts[cluster_indices[0]][0]

            # Check if the cluster is already snapped (all positions nearly identical)
            already_snapped = all((global_verts[idx][0] - rep_co).length <= epsilon for idx in cluster_indices)
            if already_snapped:
                continue

            # Update the position of each vertex in the cluster to match the representative
            for idx in cluster_indices:
                _, (obj, bm_vert) = global_verts[idx]
                new_local_co = obj.matrix_world.inverted() @ rep_co
                if (bm_vert.co - new_local_co).length > epsilon:
                    bm_vert.co = new_local_co
                    changes += 1

        # Write changes to each object and free bmesh
        for obj, bm in bm_dict.items():
            bm.to_mesh(obj.data)
            bm.free()
            obj.data.update()

        self.report({'INFO'}, f"Attached vertices by distance (threshold {self.distance_threshold}). {changes} vertices moved.")
        return {'FINISHED'}

# -------------------------------
# Snap Settings Panel
# -------------------------------
class SnapSettingsPanel(bpy.types.Panel):
    """Panel in the 3D View for managing Snap tools"""
    bl_label = "Snap Settings"
    bl_idname = "VIEW3D_PT_snap_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator(SnapSettingsOperator.bl_idname, text="Activate Snap Closest to Vertex")
        layout.operator(DisableSnapOperator.bl_idname, text="Disable Snap")
        layout.operator(SnapVertexToClosestOperator.bl_idname, text="Snap Vertices to Closest (Snap)")
        layout.operator(AttachByDistanceOperator.bl_idname, text="Attach by Distance")

# -------------------------------
# Class Registration
# -------------------------------
classes = [
    SnapSettingsOperator,
    DisableSnapOperator,
    SnapVertexToClosestOperator,
    AttachByDistanceOperator,
    SnapSettingsPanel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
