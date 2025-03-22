import bpy
import bmesh
import json

# Global variable to store UV data loaded from JSON
loaded_uvs_data = {}

def update_texture(obj, texture_path):
    """Changes the object's texture if the JSON contains a new one."""
    if not texture_path or texture_path == "No Texture":
        return  # Do not change the texture if there is no valid one

    # Ensure standardized path format
    texture_path = texture_path.replace("\\", "/")

    if obj.active_material and obj.active_material.use_nodes:
        for node in obj.active_material.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                img = bpy.data.images.get(texture_path)
                if not img:
                    try:
                        img = bpy.data.images.load(texture_path)
                    except:
                        print(f"Could not load texture: {texture_path}")
                        return
                
                node.image = img  # Assign the new texture
                print(f"Texture changed for {obj.name} to: {texture_path}")
                break

def update_uv_animation(scene):
    """Updates UVs and texture according to the current frame for all objects in the scene."""
    global loaded_uvs_data

    for obj in bpy.data.objects:
        if obj.type != 'MESH' or obj.name not in loaded_uvs_data:
            continue  # Skip non-mesh objects or objects not in JSON

        uvs_list = loaded_uvs_data[obj.name]  # Animation data for this object
        if "frames" not in uvs_list or not uvs_list["frames"]:
            continue  # Skip if no frames exist for this object

        frames = uvs_list["frames"]
        frame_index = str(scene.frame_current % len(frames))  # Get current frame index

        if frame_index not in frames:
            continue

        frame_data = frames[frame_index]

        me = obj.data
        bm = bmesh.from_edit_mesh(me) if obj.mode == 'EDIT' else bmesh.new()
        if obj.mode != 'EDIT':
            bm.from_mesh(me)

        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            continue

        frame_uvs = frame_data["UVs"]

        # Ensure the face count matches
        if len(frame_uvs) != len(bm.faces):
            print(f"Warning: The number of faces in the JSON does not match the mesh for {obj.name}.")
            continue

        for face, uv_data in zip(bm.faces, frame_uvs):
            if len(face.loops) != len(uv_data):
                print(f"Warning: Different number of loops in face {face.index} of {obj.name}")
                continue  # Skip this face if the structure does not match

            for loop, uv in zip(face.loops, uv_data):
                loop[uv_layer].uv = (uv[0], uv[1])

        if obj.mode != 'EDIT':
            bm.to_mesh(me)
            bm.free()
        else:
            bmesh.update_edit_mesh(me, loop_triangles=True)

        # Change texture if necessary
        if "Texture" in frame_data:
            update_texture(obj, frame_data["Texture"])

class UV_OT_LoadUVsFromJSON(bpy.types.Operator):
    """Loads a JSON file with UVs for multiple objects"""
    bl_idname = "uv.load_uvs_json"
    bl_label = "Load UVs from JSON"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        global loaded_uvs_data

        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict) or not data:
                self.report({'ERROR'}, "The JSON does not have the correct format.")
                return {'CANCELLED'}

            # Convert all texture paths to use `/` for consistency
            for obj_data in data.values():
                for frame_data in obj_data["frames"].values():
                    if "Texture" in frame_data and frame_data["Texture"] != "No Texture":
                        frame_data["Texture"] = frame_data["Texture"].replace("\\", "/")

            loaded_uvs_data = data  # Store all animation data from JSON

            self.report({'INFO'}, f"JSON file loaded with {len(loaded_uvs_data)} objects.")

        except Exception as e:
            self.report({'ERROR'}, f"Error loading JSON: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class UV_PT_UVToolsPanel(bpy.types.Panel):
    """Panel in the UV editor to apply UVs from JSON"""
    bl_label = "UV Animation Tools"
    bl_idname = "UV_PT_UVAnimationToolsPanel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Load Sequence"

    def draw(self, context):
        layout = self.layout
        layout.operator("uv.load_uvs_json", text="Load UVs from JSON", icon="FILE_FOLDER")
        layout.label(text="UV Animation is Active for Multiple Objects!")

def register():
    bpy.utils.register_class(UV_OT_LoadUVsFromJSON)
    bpy.utils.register_class(UV_PT_UVToolsPanel)

    # Avoid adding the handler multiple times
    if update_uv_animation not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(update_uv_animation)

def unregister():
    bpy.utils.unregister_class(UV_OT_LoadUVsFromJSON)
    bpy.utils.unregister_class(UV_PT_UVToolsPanel)

    # Remove the handler if present
    if update_uv_animation in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(update_uv_animation)

if __name__ == "__main__":
    register()
