import bpy
import bmesh


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

        # Botones de simetría
        box.separator()
        box.label(text="Mirror:")
        row = box.row(align=True)
        row.operator("uv.textools_island_mirror_v", text="Mirror V")  # Nuevo botón vertical
        row.operator("uv.textools_island_mirror_h", text="Mirror H")  # Nuevo botón horizontal

        # Botón de Fill
        box.separator()
        box.operator("uv.textools_uv_fill", text="Fill")


class Rotate90Operator(bpy.types.Operator):
    bl_idname = "uv.textools_island_rotate_90"
    bl_label = "Rotate 90 degrees"
    bl_description = "Rotate the selection 90 degrees around the global Rotation/Scaling Pivot"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.area.ui_type == 'UV' and 
                context.active_object and 
                context.active_object.type == 'MESH' and 
                context.active_object.mode == 'EDIT' and 
                context.object.data.uv_layers)

    def execute(self, context):
        bpy.ops.transform.rotate(value=1.5708, orient_axis='Z')  # 90 grados en radianes
        return {'FINISHED'}


class RotateMinus90Operator(bpy.types.Operator):
    bl_idname = "uv.textools_island_rotate_minus_90"
    bl_label = "Rotate -90 degrees"
    bl_description = "Rotate the selection -90 degrees around the global Rotation/Scaling Pivot"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.area.ui_type == 'UV' and 
                context.active_object and 
                context.active_object.type == 'MESH' and 
                context.active_object.mode == 'EDIT' and 
                context.object.data.uv_layers)

    def execute(self, context):
        bpy.ops.transform.rotate(value=-1.5708, orient_axis='Z')  # -90 grados en radianes
        return {'FINISHED'}


class MirrorVerticalOperator(bpy.types.Operator):
    bl_idname = "uv.textools_island_mirror_v"
    bl_label = "Mirror Vertical"
    bl_description = "Mirror selected UVs vertically"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.area.ui_type == 'UV' and 
                context.active_object and 
                context.active_object.type == 'MESH' and 
                context.active_object.mode == 'EDIT' and 
                context.object.data.uv_layers)

    def execute(self, context):
        bpy.ops.transform.mirror(constraint_axis=(False, True, False))  # Reflejo en el eje Y
        return {'FINISHED'}


class MirrorHorizontalOperator(bpy.types.Operator):
    bl_idname = "uv.textools_island_mirror_h"
    bl_label = "Mirror Horizontal"
    bl_description = "Mirror selected UVs horizontally"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.area.ui_type == 'UV' and 
                context.active_object and 
                context.active_object.type == 'MESH' and 
                context.active_object.mode == 'EDIT' and 
                context.object.data.uv_layers)

    def execute(self, context):
        bpy.ops.transform.mirror(constraint_axis=(True, False, False))  # Reflejo en el eje X
        return {'FINISHED'}


class UVFillOperator(bpy.types.Operator):
    bl_idname = "uv.textools_uv_fill"
    bl_label = "Fill"
    bl_description = "Fill the 0-1 UV area with the selected UVs"
    bl_options = {'REGISTER', 'UNDO'}

    align: bpy.props.BoolProperty(name='Align', description="Align orientation", default=False)

    @classmethod
    def poll(cls, context):
        return (context.area.ui_type == 'UV' and 
                context.active_object and 
                context.active_object.type == 'MESH' and 
                context.active_object.mode == 'EDIT' and 
                context.object.data.uv_layers)

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.active

        if not uv_layer:
            self.report({'ERROR'}, "No UV map found")
            return {'CANCELLED'}

        uvs = [loop[uv_layer].uv for face in bm.faces if face.select for loop in face.loops]

        if not uvs:
            self.report({'ERROR'}, "No UVs selected")
            return {'CANCELLED'}

        min_u, max_u = min(uv[0] for uv in uvs), max(uv[0] for uv in uvs)
        min_v, max_v = min(uv[1] for uv in uvs), max(uv[1] for uv in uvs)

        scale_u = 1.0 / (max_u - min_u) if max_u - min_u != 0 else 1.0
        scale_v = 1.0 / (max_v - min_v) if max_v - min_v != 0 else 1.0

        for face in bm.faces:
            if face.select:
                for loop in face.loops:
                    uv = loop[uv_layer].uv
                    uv[0] = (uv[0] - min_u) * scale_u
                    uv[1] = (uv[1] - min_v) * scale_v

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(UVResetTexturePanel)
    bpy.utils.register_class(Rotate90Operator)
    bpy.utils.register_class(RotateMinus90Operator)
    bpy.utils.register_class(MirrorVerticalOperator)
    bpy.utils.register_class(MirrorHorizontalOperator)
    bpy.utils.register_class(UVFillOperator)


def unregister():
    bpy.utils.unregister_class(UVResetTexturePanel)
    bpy.utils.unregister_class(Rotate90Operator)
    bpy.utils.unregister_class(RotateMinus90Operator)
    bpy.utils.unregister_class(MirrorVerticalOperator)
    bpy.utils.unregister_class(MirrorHorizontalOperator)
    bpy.utils.unregister_class(UVFillOperator)


if __name__ == "__main__":
    register()
