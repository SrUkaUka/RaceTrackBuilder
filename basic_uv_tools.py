import bpy


class UVResetTexturePanel(bpy.types.Panel):
    bl_label = "Reset Texture"
    bl_idname = "UV_PT_reset_texture"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'UV Editing'

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        
        # Botón de Reset Texture
        box.operator("uv.reset", text="Reset Texture")
        
        # Grupo de botones de rotación
        box.label(text="Rotation:")
        row = box.row(align=True)
        row.operator("uv.textools_island_rotate_90", text="Rotate 90°")
        row.operator("uv.textools_island_rotate_minus_90", text="Rotate -90°")
        
        # Botón de simetría
        box.separator()
        box.operator("uv.textools_island_mirror", text="Mirror Symmetry")


class Rotate90Operator(bpy.types.Operator):
    bl_idname = "uv.textools_island_rotate_90"
    bl_label = "Rotate 90 degrees"
    bl_description = "Rotate the selection 90 degrees around the global Rotation/Scaling Pivot"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.area.ui_type != 'UV':
            return False
        if not bpy.context.active_object:
            return False
        if bpy.context.active_object.type != 'MESH':
            return False
        if bpy.context.active_object.mode != 'EDIT':
            return False
        if not bpy.context.object.data.uv_layers:
            return False
        return True

    def execute(self, context):
        sync = bpy.context.scene.tool_settings.use_uv_select_sync
        if sync:
            selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

        # Rotación de 90 grados en radianes
        bpy.ops.transform.rotate(value=1.5708, orient_axis='Z')  # 90 grados en radianes

        if sync:
            bpy.context.scene.tool_settings.mesh_select_mode = selection_mode

        return {'FINISHED'}


class RotateMinus90Operator(bpy.types.Operator):
    bl_idname = "uv.textools_island_rotate_minus_90"
    bl_label = "Rotate -90 degrees"
    bl_description = "Rotate the selection -90 degrees around the global Rotation/Scaling Pivot"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.area.ui_type != 'UV':
            return False
        if not bpy.context.active_object:
            return False
        if bpy.context.active_object.type != 'MESH':
            return False
        if bpy.context.active_object.mode != 'EDIT':
            return False
        if not bpy.context.object.data.uv_layers:
            return False
        return True

    def execute(self, context):
        sync = bpy.context.scene.tool_settings.use_uv_select_sync
        if sync:
            selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

        # Rotación de -90 grados en radianes
        bpy.ops.transform.rotate(value=-1.5708, orient_axis='Z')  # -90 grados en radianes

        if sync:
            bpy.context.scene.tool_settings.mesh_select_mode = selection_mode

        return {'FINISHED'}


class SymmetryOperator(bpy.types.Operator):
    bl_idname = "uv.textools_island_mirror"
    bl_label = "Symmetry"
    bl_description = "Mirror selected faces with respect to the global Rotation/Scaling Pivot"
    bl_options = {'REGISTER', 'UNDO'}

    is_vertical: bpy.props.BoolProperty(name="is_vertical", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        if bpy.context.area.ui_type != 'UV':
            return False
        if not bpy.context.active_object:
            return False
        if bpy.context.active_object.type != 'MESH':
            return False
        if bpy.context.active_object.mode != 'EDIT':
            return False
        if not bpy.context.object.data.uv_layers:
            return False
        return True

    def execute(self, context):
        is_vertical = self.is_vertical
        if is_vertical:
            bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False))
        else:
            bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False))

        return {'FINISHED'}


def register():
    bpy.utils.register_class(UVResetTexturePanel)
    bpy.utils.register_class(Rotate90Operator)
    bpy.utils.register_class(RotateMinus90Operator)
    bpy.utils.register_class(SymmetryOperator)


def unregister():
    bpy.utils.unregister_class(UVResetTexturePanel)
    bpy.utils.unregister_class(Rotate90Operator)
    bpy.utils.unregister_class(RotateMinus90Operator)
    bpy.utils.unregister_class(SymmetryOperator)


if __name__ == "__main__":
    register()
