import bpy
import bmesh
import json
import os
import bpy_extras.io_utils  # Import ExportHelper to manage .json files

uvs_storage = {}  # Stores UV data for each object
active_uvs_list = None
first_object_name = None

class UV_OT_NewList(bpy.types.Operator):
    """Create a new list to store UVs from the selected object"""
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

        # Create dictionary structure if it doesn't exist
        if first_object_name not in uvs_storage:
            uvs_storage[first_object_name] = {
                "Object": first_object_name,
                "frames": {}
            }

        active_uvs_list = uvs_storage[first_object_name]
        self.report({'INFO'}, f"New list created for {first_object_name}")
        return {'FINISHED'}

class UV_OT_RemoveLast(bpy.types.Operator):
    """Delete the last frame from the active list"""
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
    """Save UV coordinates from the current frame"""
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
                    texture_path = bpy.path.abspath(node.image.filepath).replace("\\", "/")
                    break

        frame_data = {
            "UVs": frame_uvs,
            "Texture": texture_path if texture_path else "No Texture"
        }

        active_uvs_list["frames"][str(frame_number)] = frame_data
        self.report({'INFO'}, f"Frame {frame_number} saved with {len(frame_uvs)} UV faces.")
        return {'FINISHED'}

class UV_OT_ExportAnimationInfo(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Export all stored UV data to a JSON file"""
    bl_idname = "uv.export_animation_info"
    bl_label = "Export Animation Info"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".json"

    def execute(self, context):
        global uvs_storage

        if not uvs_storage:
            self.report({'WARNING'}, "No UV data to export")
            return {'CANCELLED'}

        for obj_data in uvs_storage.values():
            for frame_data in obj_data["frames"].values():
                if "Texture" in frame_data and frame_data["Texture"] != "No Texture":
                    frame_data["Texture"] = frame_data["Texture"].replace("\\", "/")

        data_to_export = json.dumps(uvs_storage, indent=4)

        with open(self.filepath, "w", encoding="utf-8") as file:
            file.write(data_to_export)

        self.report({'INFO'}, f"UV data exported to {self.filepath}")
        return {'FINISHED'}

class UV_OT_ExportObjSequence(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Duplicate objects for each recorded frame, assign corresponding UVs and textures,
       and export each object's sequence as a separate OBJ file.
       The exported files will be saved in the chosen folder with the object's name plus '_anim01' suffix."""
    bl_idname = "uv.export_obj_sequence"
    bl_label = "Export obj sequence"
    bl_options = {'REGISTER', 'UNDO'}

    # Instead of filename_ext we expect a folder, pero mantenemos el helper para usar el selector
    filename_ext = ".obj"
    use_filter_folder = True  # Añadido para que se pueda seleccionar una carpeta

    def execute(self, context):
        global uvs_storage

        if not uvs_storage:
            self.report({'WARNING'}, "No UV data available for export")
            return {'CANCELLED'}

        export_dir = os.path.dirname(self.filepath)
        if not os.path.isdir(export_dir):
            self.report({'WARNING'}, "Please select a valid directory")
            return {'CANCELLED'}

        for obj_name, obj_data in uvs_storage.items():
            if not obj_data["frames"]:
                continue
            try:
                original_obj = bpy.data.objects[obj_name]
            except KeyError:
                self.report({'WARNING'}, f"Object {obj_name} not found in scene")
                continue

            duplicates = []
            texture_materials = {}
            frames_data = obj_data["frames"]
            sorted_frame_keys = sorted(frames_data.keys(), key=lambda x: int(x))
            
            # Duplicate and assign UVs and textures for each frame
            for key in sorted_frame_keys:
                frame_data = frames_data[key]
                dup = original_obj.copy()
                dup.data = original_obj.data.copy()
                context.scene.collection.objects.link(dup)
                dup.name = f"{obj_name}_frame{int(key):02d}"
                
                mesh = dup.data
                if not mesh.uv_layers:
                    mesh.uv_layers.new(name="UVMap")
                uv_layer = mesh.uv_layers.active.data
                
                stored_uvs = frame_data.get("UVs", [])
                uv_face_index = 0
                for poly in mesh.polygons:
                    if uv_face_index >= len(stored_uvs):
                        break
                    face_uvs = stored_uvs[uv_face_index]
                    if len(face_uvs) == poly.loop_total:
                        for i, loop_index in enumerate(range(poly.loop_start, poly.loop_start + poly.loop_total)):
                            uv_layer[loop_index].uv = face_uvs[i]
                    uv_face_index += 1
                
                desired_texture = frame_data.get("Texture", "No Texture")
                if desired_texture != "No Texture":
                    assign_flag = True
                    if dup.data.materials:
                        current_mat = dup.data.materials[0]
                        if current_mat.use_nodes:
                            for node in current_mat.node_tree.nodes:
                                if node.type == 'TEX_IMAGE' and node.image:
                                    current_path = bpy.path.abspath(node.image.filepath).replace("\\", "/")
                                    if current_path == desired_texture:
                                        assign_flag = False
                                        break
                    if assign_flag:
                        dup.data.materials.clear()
                        if desired_texture in texture_materials:
                            new_mat = texture_materials[desired_texture]
                        else:
                            new_mat = bpy.data.materials.new(name=f"Mat_{obj_name}_frame_{key}")
                            new_mat.use_nodes = True
                            nodes = new_mat.node_tree.nodes
                            links = new_mat.node_tree.links
                            for node in list(nodes):
                                nodes.remove(node)
                            tex_node = nodes.new(type='ShaderNodeTexImage')
                            bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
                            output_node = nodes.new(type='ShaderNodeOutputMaterial')
                            try:
                                img = bpy.data.images.load(desired_texture)
                                tex_node.image = img
                            except Exception as e:
                                self.report({'WARNING'}, f"Could not load image: {desired_texture}")
                            links.new(tex_node.outputs['Color'], bsdf_node.inputs['Base Color'])
                            links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
                            texture_materials[desired_texture] = new_mat
                        dup.data.materials.append(new_mat)
                
                duplicates.append(dup)
            
            # Finalize duplication and UV assignment: switch to Object Mode, update selection, and export
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            for dup in duplicates:
                dup.select_set(True)
            context.view_layer.objects.active = duplicates[0] if duplicates else None
            
            # Define el filepath de exportación para este objeto
            export_filepath = os.path.join(export_dir, f"{obj_name}_anim01.obj")
            bpy.ops.wm.obj_export(filepath=export_filepath,
                                  export_selected_objects=True)
            
            self.report({'INFO'}, f"Exported {len(duplicates)} OBJ frames for {obj_name} to {export_filepath}")
        
        return {'FINISHED'}

class UV_PT_UVToolsPanel(bpy.types.Panel):
    """UV Editor Panel"""
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
        layout.operator("uv.export_obj_sequence", text="Export obj sequence", icon="EXPORT")
        
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
    bpy.utils.register_class(UV_OT_ExportObjSequence)
    bpy.utils.register_class(UV_PT_UVToolsPanel)

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
    bpy.utils.unregister_class(UV_OT_ExportObjSequence)
    bpy.utils.unregister_class(UV_PT_UVToolsPanel)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
