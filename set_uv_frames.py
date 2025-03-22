import bpy
import bmesh
import json
import bpy_extras.io_utils  # Import ExportHelper to manage .json 

uvs_storage = {}  # Stores uv data of each object
active_uvs_list = None
first_object_name = None  

class UV_OT_NewList(bpy.types.Operator):
    """Create a new list to store UVs from selected object"""
    bl_idname = "uv.new_list"
    bl_label = "New List"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global active_uvs_list, first_object_name, uvs_storage
        
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "No valid object selected")
            return {'CANCELLED'}

        first_object_name = obj.name

        # Create a dictionary with a correct structure
        if first_object_name not in uvs_storage:
            uvs_storage[first_object_name] = {
                "Object": first_object_name,
                "frames": {}
            }

        active_uvs_list = uvs_storage[first_object_name]
        self.report({'INFO'}, f"New list created for {first_object_name}")
        return {'FINISHED'}

class UV_OT_RemoveLast(bpy.types.Operator):
    """Deletes last frame from active list"""
    bl_idname = "uv.remove_last"
    bl_label = "Remove Last"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global active_uvs_list
        
        if active_uvs_list is None or not active_uvs_list["frames"]:
            self.report({'WARNING'}, "No frames to remove.")
            return {'CANCELLED'}

        last_frame = max(map(int, active_uvs_list["frames"].keys()))
        del active_uvs_list["frames"][str(last_frame)]
        self.report({'INFO'}, f"Frame {last_frame} removed.")
        return {'FINISHED'}

class UV_OT_PrintSelectedUVs(bpy.types.Operator):
    """Saves Uv coordinates from actual frame"""
    bl_idname = "uv.print_selected_uvs"
    bl_label = "Assign Frame"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global active_uvs_list

        if active_uvs_list is None:
            self.report({'WARNING'}, "You must start a list before assigning a frame.")
            return {'CANCELLED'}

        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh selected")
            return {'CANCELLED'}

        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "The mesh must be in Edit Mode")
            return {'CANCELLED'}

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        uv_layer = bm.loops.layers.uv.active

        if uv_layer is None:
            self.report({'WARNING'}, "No active UV map")
            return {'CANCELLED'}

        selected_faces = [face for face in bm.faces if face.select]
        if not selected_faces:
            self.report({'WARNING'}, "No UV faces selected")
            return {'CANCELLED'}

        frame_number = len(active_uvs_list["frames"])
        frame_uvs = [[(loop[uv_layer].uv.x, loop[uv_layer].uv.y) for loop in face.loops] for face in selected_faces]

        texture_path = None
        if obj.active_material and obj.active_material.use_nodes:
            for node in obj.active_material.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    texture_path = bpy.path.abspath(node.image.filepath).replace("\\", "/")  # Estandarización de ruta
                    break

        frame_data = {
            "UVs": frame_uvs,
            "Texture": texture_path if texture_path else "No Texture"
        }

        active_uvs_list["frames"][str(frame_number)] = frame_data
        self.report({'INFO'}, f"Frame {frame_number} saved with {len(frame_uvs)} UV faces.")
        return {'FINISHED'}

class UV_OT_ExportAnimationInfo(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):  # Added ExportHelper
    """Exports all lists from UV coordinates in JSON format"""
    bl_idname = "uv.export_animation_info"
    bl_label = "Export Animation Info"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".json"  # Defines file extension

    def execute(self, context):
        global uvs_storage

        if not uvs_storage:
            self.report({'WARNING'}, "No UV data to export")
            return {'CANCELLED'}

        # Convert all stored texture paths to use `/`
        for obj_data in uvs_storage.values():
            for frame_data in obj_data["frames"].values():
                if "Texture" in frame_data and frame_data["Texture"] != "No Texture":
                    frame_data["Texture"] = frame_data["Texture"].replace("\\", "/")

        data_to_export = json.dumps(uvs_storage, indent=4)

        with open(self.filepath, "w", encoding="utf-8") as file:
            file.write(data_to_export)

        self.report({'INFO'}, f"UV data exported to {self.filepath}")
        return {'FINISHED'}

class UV_PT_UVToolsPanel(bpy.types.Panel):
    """Uv editor panel"""
    bl_label = "UV Tools"
    bl_idname = "UV_PT_UVToolsPanel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Anim texture"

    def draw(self, context):
        layout = self.layout
        layout.operator("uv.new_list", text="New List", icon="FILE_NEW")
        layout.operator("uv.remove_last", text="Remove Last", icon="TRASH")
        layout.separator()
        layout.operator("uv.print_selected_uvs", text="Assign Frame", icon="UV")
        layout.operator("uv.export_animation_info", text="Export Animation Info", icon="EXPORT")

        layout.label(text="UV Data:")

        if active_uvs_list is None or not active_uvs_list["frames"]:
            layout.label(text="No UV data assigned.")
        else:
            box = layout.box()
            for frame, frame_data in active_uvs_list["frames"].items():
                frame_box = box.box()
                frame_box.label(text=f'Frame: {frame}')
                frame_box.label(text=f'Texture: {frame_data["Texture"]}')
                frame_box.label(text="UVs:")
                for face_uvs in frame_data["UVs"]:
                    for uv in face_uvs:
                        frame_box.label(text=f"({uv[0]:.6f}, {uv[1]:.6f})")

addon_keymaps = []

def register():
    bpy.utils.register_class(UV_OT_NewList)
    bpy.utils.register_class(UV_OT_RemoveLast)
    bpy.utils.register_class(UV_OT_PrintSelectedUVs)
    bpy.utils.register_class(UV_OT_ExportAnimationInfo)
    bpy.utils.register_class(UV_PT_UVToolsPanel)

    # Shortcut key to assign frame Shift + A
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Window", space_type='EMPTY')
        kmi = km.keymap_items.new("uv.print_selected_uvs", 'A', 'PRESS', shift=True)
        addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(UV_OT_NewList)
    bpy.utils.unregister_class(UV_OT_RemoveLast)
    bpy.utils.unregister_class(UV_OT_PrintSelectedUVs)
    bpy.utils.unregister_class(UV_OT_ExportAnimationInfo)
    bpy.utils.unregister_class(UV_PT_UVToolsPanel)

    # Remove keyboard shortcut when unregistering addon
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
