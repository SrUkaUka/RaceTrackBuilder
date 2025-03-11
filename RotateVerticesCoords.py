import bpy

# Global dictionary to store vertex lists per object
object_vertex_lists = {}

# Global property to control TriBlock mode (6 vertices) or QuadBlock mode (8 vertices)
bpy.types.Scene.use_quadblock = bpy.props.BoolProperty(
    name="QuadBlock",
    description="Use 8 vertices (QuadBlock) instead of 6 (TriBlock)",
    default=False
)

def get_active_object():
    """Returns the active object in the scene."""
    return bpy.context.object if bpy.context.object and bpy.context.object.type == 'MESH' else None

def get_vertex_list():
    """Gets the vertex list of the active object."""
    obj = get_active_object()
    if obj is None:
        return None
    return object_vertex_lists.setdefault(obj.name, [])

def add_selected_vertex():
    """Manually adds a selected vertex to the active object's list."""
    obj = get_active_object()
    if obj is None:
        return

    vertex_list = get_vertex_list()
    bpy.ops.object.mode_set(mode='OBJECT')  # Switch to object mode to access vertices
    selected_verts = [v for v in obj.data.vertices if v.select]

    if len(selected_verts) != 1:
        return

    v = selected_verts[0]
    vertex_data = (v.index, v.co.copy())

    if vertex_data in vertex_list:
        return  # Prevent duplicates

    max_verts = 8 if bpy.context.scene.use_quadblock else 6
    if len(vertex_list) >= max_verts:
        return  

    vertex_list.append(vertex_data)
    bpy.ops.object.mode_set(mode='EDIT')  # Switch back to edit mode
    bpy.context.area.tag_redraw()  # Refresh UI

def rotate_indices(step):
    """Rotates the vertex indices in the mesh."""
    obj = get_active_object()
    if obj is None:
        return

    vertex_list = get_vertex_list()
    num_verts = len(vertex_list)
    expected_verts = 8 if bpy.context.scene.use_quadblock else 6

    if num_verts != expected_verts:
        print(f"❌ You must have exactly {expected_verts} vertices in the list.")
        return

    bpy.ops.object.mode_set(mode='OBJECT')  # Switch to object mode to modify vertices

    original_indices = [v[0] for v in vertex_list]
    original_coords = [v[1] for v in vertex_list]

    # Circular rotation based on the 'step' value (positive or negative)
    step = step % num_verts  # Ensure the rotation is within the list size
    rotated_indices = original_indices[-step:] + original_indices[:-step]

    # Apply the new coordinates to the mesh
    for new_index, old_coord in zip(rotated_indices, original_coords):
        obj.data.vertices[new_index].co = old_coord

    # Update the list with the new indices
    object_vertex_lists[obj.name] = list(zip(rotated_indices, original_coords))

    bpy.ops.object.mode_set(mode='EDIT')  # Switch back to edit mode
    bpy.context.area.tag_redraw()  # Refresh UI

def clear_selected_list():
    """Clears the selected vertex list of the active object."""
    obj = get_active_object()
    if obj and obj.name in object_vertex_lists:
        object_vertex_lists[obj.name] = []
        bpy.context.area.tag_redraw()

def remove_last_vertex():
    """Removes the last added vertex from the active object's list."""
    vertex_list = get_vertex_list()
    if vertex_list:
        vertex_list.pop()
        bpy.context.area.tag_redraw()

# Blender UI Panel
class OBJECT_PT_Rotate90(bpy.types.Panel):
    """UI Panel for vertex index rotation and management."""
    bl_label = "Rotate Indices"
    bl_idname = "OBJECT_PT_rotate_90"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        obj = get_active_object()
        vertex_list = get_vertex_list()

        if obj is None:
            layout.label(text="Select a mesh object")
            return

        layout.label(text=f"Object: {obj.name}")

        # Checkbox to choose between TriBlock (6) and QuadBlock (8)
        layout.prop(context.scene, "use_quadblock", text="QuadBlock")

        # Main buttons
        row = layout.row()
        row.operator("object.add_selected_vertex", text="Add Vertex")

        row = layout.row()
        row.operator("object.rotate_indices_90", text="R90")
        row.operator("object.rotate_indices_neg90", text="R-90")

        # Display selected vertex list
        layout.label(text="Selected Vertices List:")

        if vertex_list:
            for i, (index, coord) in enumerate(vertex_list):
                layout.label(text=f"{i+1}. Index: {index} - {tuple(coord)}")

            layout.operator("object.remove_last_vertex", text="Remove Last")
            layout.operator("object.clear_selected_list", text="Clear All")
        else:
            layout.label(text="(Empty List)")

# Operators
class OBJECT_OT_AddVertex(bpy.types.Operator):
    """Adds the currently selected vertex to the active object's list."""
    bl_idname = "object.add_selected_vertex"
    bl_label = "Add Vertex"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        add_selected_vertex()
        return {'FINISHED'}

class OBJECT_OT_Rotate90(bpy.types.Operator):
    """Rotates the selected vertex indices 90 degrees clockwise (2 positions)."""
    bl_idname = "object.rotate_indices_90"
    bl_label = "R90"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rotate_indices(2)  # Rotate two positions downward (clockwise)
        return {'FINISHED'}

class OBJECT_OT_RotateNeg90(bpy.types.Operator):
    """Rotates the selected vertex indices 90 degrees counterclockwise (-2 positions)."""
    bl_idname = "object.rotate_indices_neg90"
    bl_label = "R-90"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rotate_indices(-2)  # Rotate two positions upward (counterclockwise)
        return {'FINISHED'}

class OBJECT_OT_ClearList(bpy.types.Operator):
    """Clears the list of selected vertices for the active object."""
    bl_idname = "object.clear_selected_list"
    bl_label = "Clear All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        clear_selected_list()
        return {'FINISHED'}

class OBJECT_OT_RemoveLast(bpy.types.Operator):
    """Removes the last added vertex from the list of the active object."""
    bl_idname = "object.remove_last_vertex"
    bl_label = "Remove Last"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        remove_last_vertex()
        return {'FINISHED'}

# Register in Blender with a keyboard shortcut
addon_keymaps = []

def register():
    """Registers the addon and assigns a keyboard shortcut."""
    global addon_keymaps
    bpy.utils.register_class(OBJECT_PT_Rotate90)
    bpy.utils.register_class(OBJECT_OT_AddVertex)
    bpy.utils.register_class(OBJECT_OT_Rotate90)
    bpy.utils.register_class(OBJECT_OT_RotateNeg90)
    bpy.utils.register_class(OBJECT_OT_ClearList)
    bpy.utils.register_class(OBJECT_OT_RemoveLast)

    # Add keyboard shortcut SHIFT + W
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="Mesh", space_type="EMPTY")
    kmi = km.keymap_items.new("object.add_selected_vertex", "W", "PRESS", shift=True)
    addon_keymaps.append((km, kmi))

def unregister():
    """Unregisters the addon and removes the assigned keyboard shortcut."""
    global addon_keymaps
    bpy.utils.unregister_class(OBJECT_PT_Rotate90)
    bpy.utils.unregister_class(OBJECT_OT_AddVertex)
    bpy.utils.unregister_class(OBJECT_OT_Rotate90)
    bpy.utils.unregister_class(OBJECT_OT_RotateNeg90)
    bpy.utils.unregister_class(OBJECT_OT_ClearList)
    bpy.utils.unregister_class(OBJECT_OT_RemoveLast)

    # Remove keyboard shortcut
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
