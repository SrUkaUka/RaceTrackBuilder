import bpy
import bmesh
from mathutils import Vector

# Operator to activate Snap
class SnapSettingsOperator(bpy.types.Operator):
    """Activates Snap with 'Closest' and 'Vertex' settings"""
    bl_idname = "view3d.snap_settings_operator"
    bl_label = "Activate Snap Closest to Vertex"

    def execute(self, context):
        # Activate Snap
        context.scene.tool_settings.use_snap = True

        # Set Snap method to "Closest"
        context.scene.tool_settings.snap_target = 'CLOSEST'

        # Set Snap element to "Vertex"
        context.scene.tool_settings.snap_elements = {'VERTEX'}

        self.report({'INFO'}, "Snap activated: Closest and Vertex")
        return {'FINISHED'}

# Operator to disable Snap
class DisableSnapOperator(bpy.types.Operator):
    """Disables Snap"""
    bl_idname = "view3d.disable_snap_operator"
    bl_label = "Disable Snap"

    def execute(self, context):
        # Disable Snap
        context.scene.tool_settings.use_snap = False
        self.report({'INFO'}, "Snap disabled")
        return {'FINISHED'}

# Operator to snap vertices to closest ones
class SnapVertexToClosestOperator(bpy.types.Operator):
    """Snaps the selected vertices of multiple objects to the closest vertices of other objects"""
    bl_idname = "view3d.snap_vertex_to_closest_operator"
    bl_label = "Snap Selected Vertices to Closest Vertices"

    def execute(self, context):
        # Get all selected mesh objects
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if len(selected_objects) < 2:
            self.report({'WARNING'}, "Select at least two mesh objects.")
            return {'CANCELLED'}

        # Define the first object as the active object and others as reference objects
        active_object = selected_objects[0]
        reference_objects = selected_objects[1:]

        # Make sure the active object is in OBJECT mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Combine all global coordinates of reference objects
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

        # Adjust selected vertices to the closest ones in the reference objects
        for v in selected_vertices:
            global_v_co = active_object.matrix_world @ v.co
            closest_vertex_global = min(reference_vertices_global, key=lambda v2_co: (global_v_co - v2_co).length)
            local_closest_co = active_object.matrix_world.inverted() @ closest_vertex_global
            v.co = local_closest_co

        # Update the mesh of the active object
        bm.to_mesh(active_object.data)
        bm.free()
        active_object.data.update()

        self.report({'INFO'}, f"Vertices adjusted successfully.")
        return {'FINISHED'}

# Panel for Snap settings
class SnapSettingsPanel(bpy.types.Panel):
    """Creates a panel in the 3D view"""
    bl_label = "Snap Settings"
    bl_idname = "VIEW3D_PT_snap_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'  # Changed from 'Herramientas' to 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator(SnapSettingsOperator.bl_idname, text="Activate Snap Closest to Vertex")
        layout.operator(DisableSnapOperator.bl_idname, text="Disable Snap")
        layout.operator(SnapVertexToClosestOperator.bl_idname, text="Snap Vertices to Closest (Snap)")

# Register the classes
classes = [
    SnapSettingsOperator,
    DisableSnapOperator,
    SnapVertexToClosestOperator,
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
