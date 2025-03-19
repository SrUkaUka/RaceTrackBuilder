import bpy
import bmesh


class UVResetTexturePanel(bpy.types.Panel):
    bl_label = "UV Tools"
    bl_idname = "UV_PT_reset_texture"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'UV Editing'

    def draw(self, context):
        layout = self.layout

        # Section: Reset Texture
        box_reset = layout.box()
        box_reset.label(text="Reset Texture:")
        box_reset.operator("uv.reset", text="Reset Texture")

        # Section: Rotate
        box_rotate = layout.box()
        box_rotate.label(text="Rotation:")
        row = box_rotate.row(align=True)
        row.operator("uv.textools_island_rotate_90", text="Rotate -90°")
        row.operator("uv.textools_island_rotate_minus_90", text="Rotate 90°")

        # Section: Mirror
        box_mirror = layout.box()
        box_mirror.label(text="Mirror:")
        row = box_mirror.row(align=True)
        row.operator("uv.textools_island_mirror_v", text="Mirror H")
        row.operator("uv.textools_island_mirror_h", text="Mirror V")

        # Section: Fill
        box_fill = layout.box()
        box_fill.operator("uv.textools_uv_fill", text="Fill")

        # Sección: Move UVs
        box_move = layout.box()
        box_move.label(text="Move UVs:")
        box_move.prop(context.scene, "uv_offset_value", expand=True)
        row = box_move.row(align=True)
        row.operator("uv.move_uv", text="", icon='TRIA_UP').direction = 'FRONT'
        row.operator("uv.move_uv", text="", icon='TRIA_DOWN').direction = 'BACK'
        row = box_move.row(align=True)
        row.operator("uv.move_uv", text="", icon='TRIA_LEFT').direction = 'LEFT'
        row.operator("uv.move_uv", text="", icon='TRIA_RIGHT').direction = 'RIGHT'

        # Section: Scale UVs to Pixels
        box_scale = layout.box()
        box_scale.label(text="Scale UVs to Pixels:")
        row = box_scale.row(align=True)
        # Uses columns and rows
        col = row.column(align=True)
        for size in [16, 32, 64]:
            col.operator("uv.scale_to_pixels", text=f"Scale to {size}px").target_pixels = str(size)
        col = row.column(align=True)
        for size in [128, 256]:
            col.operator("uv.scale_to_pixels", text=f"Scale to {size}px").target_pixels = str(size)

        # Section: Move to Top-Left
        box_top_left = layout.box()
        box_top_left.operator("uv.move_to_top_left", text="Move to Top Left")

        # Section: Align
        box_align = layout.box()
        box_align.label(text="Align:")
        row = box_align.row(align=True)
        row.operator("uv.align_axis", text="Align X").axis = 'X'
        row.operator("uv.align_axis", text="Align Y").axis = 'Y'


# Operator to move uvs
class MoveUVOperator(bpy.types.Operator):
    bl_idname = "uv.move_uv"
    bl_label = "Move UV"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        items=[
            ('FRONT', "Front", ""),
            ('BACK', "Back", ""),
            ('LEFT', "Left", ""),
            ('RIGHT', "Right", "")
        ]
    )

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.active

        if not uv_layer:
            self.report({'ERROR'}, "No UV map found")
            return {'CANCELLED'}

        image_size = 1024
        tex = obj.active_material.node_tree.nodes.get("Image Texture")
        if tex and tex.image:
            image_size = max(tex.image.size[0], 1)

        move_pixels = int(context.scene.uv_offset_value)
        move_value = move_pixels / image_size

        move_u = 0.0
        move_v = 0.0

        if self.direction == 'FRONT':
            move_v = move_value
        elif self.direction == 'BACK':
            move_v = -move_value
        elif self.direction == 'LEFT':
            move_u = -move_value
        elif self.direction == 'RIGHT':
            move_u = move_value

        for face in bm.faces:
            if face.select:
                for loop in face.loops:
                    loop[uv_layer].uv[0] += move_u
                    loop[uv_layer].uv[1] += move_v

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


# Operator to scale UVs to specific dimensions
class UVScaleToPixelsOperator(bpy.types.Operator):
    bl_idname = "uv.scale_to_pixels"
    bl_label = "Scale UV to Pixels"
    bl_options = {'REGISTER', 'UNDO'}

    target_pixels: bpy.props.EnumProperty(
        name="Target Size",
        items=[(str(x), f"{x}px", f"Scale UVs to {x} pixels") for x in [16, 32, 64, 128, 256]],
        default='64'
    )

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.active

        if not uv_layer:
            self.report({'ERROR'}, "No UV map found")
            return {'CANCELLED'}

        image_size = 1024
        tex = obj.active_material.node_tree.nodes.get("Image Texture")
        if tex and tex.image:
            image_size = max(tex.image.size[0], 1)

        uvs = [loop[uv_layer].uv for face in bm.faces if face.select for loop in face.loops]

        if not uvs:
            self.report({'ERROR'}, "No UVs selected")
            return {'CANCELLED'}

        min_u, max_u = min(uv[0] for uv in uvs), max(uv[0] for uv in uvs)
        min_v, max_v = min(uv[1] for uv in uvs), max(uv[1] for uv in uvs)

        uv_width = (max_u - min_u) * image_size
        uv_height = (max_v - min_v) * image_size

        target_size = int(self.target_pixels)

        scale_factor_u = target_size / uv_width if uv_width > 0 else 1
        scale_factor_v = target_size / uv_height if uv_height > 0 else 1

        center_u = (min_u + max_u) / 2
        center_v = (min_v + max_v) / 2

        for uv in uvs:
            uv[0] = center_u + (uv[0] - center_u) * scale_factor_u
            uv[1] = center_v + (uv[1] - center_v) * scale_factor_v

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


# Operator to move UVs to Top left corner
class MoveUVsTopLeftOperator(bpy.types.Operator):
    bl_idname = "uv.move_to_top_left"
    bl_label = "Move UVs to Top Left"
    bl_options = {'REGISTER', 'UNDO'}

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

        min_u = min(uv[0] for uv in uvs)
        max_v = max(uv[1] for uv in uvs)

        move_u = -min_u
        move_v = 1.0 - max_v

        for uv in uvs:
            uv[0] += move_u
            uv[1] += move_v

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


# Operator to Align uvs S+X+0 o S+Y+0
class UVAlignAxisOperator(bpy.types.Operator):
    bl_idname = "uv.align_axis"
    bl_label = "Align Axis"
    bl_options = {'REGISTER', 'UNDO'}

    axis: bpy.props.EnumProperty(
        items=[
            ('X', "X", "Ejecuta S+X+0"),
            ('Y', "Y", "Ejecuta S+Y+0")
        ]
    )

    def execute(self, context):
        if self.axis == 'X':
            bpy.ops.transform.resize(value=(0, 1, 1), constraint_axis=(True, False, False))
        elif self.axis == 'Y':
            bpy.ops.transform.resize(value=(1, 0, 1), constraint_axis=(False, True, False))
        return {'FINISHED'}


# Registro
def register():
    bpy.utils.register_class(UVResetTexturePanel)
    bpy.utils.register_class(MoveUVOperator)
    bpy.utils.register_class(UVScaleToPixelsOperator)
    bpy.utils.register_class(MoveUVsTopLeftOperator)
    bpy.utils.register_class(UVAlignAxisOperator)

    bpy.types.Scene.uv_offset_value = bpy.props.EnumProperty(
        name="Offset",
        items=[(str(x), f"{x}px", f"Move UVs by {x} pixels") for x in [16, 32, 64, 128, 256]],
        default='64'
    )


def unregister():
    bpy.utils.unregister_class(UVResetTexturePanel)
    bpy.utils.unregister_class(MoveUVOperator)
    bpy.utils.unregister_class(UVScaleToPixelsOperator)
    bpy.utils.unregister_class(MoveUVsTopLeftOperator)
    bpy.utils.unregister_class(UVAlignAxisOperator)

    del bpy.types.Scene.uv_offset_value


if __name__ == "__main__":
    register()
