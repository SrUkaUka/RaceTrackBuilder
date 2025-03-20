import bpy
import bmesh
import math
import mathutils


# Panel principal en el UV/Image Editor
class UVResetTexturePanel(bpy.types.Panel):
    bl_label = "UV Tools"
    bl_idname = "UV_PT_reset_texture"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'UV Editing'

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        # Reset Texture: llama al operador nativo de Blender
        box.operator("uv.reset", text="Reset Texture")

        # Rotate Buttons
        box.label(text="Rotation:")
        row = box.row(align=True)
        row.operator("uv.textools_island_rotate_90", text="Rotate 90°")
        row.operator("uv.textools_island_rotate_minus_90", text="Rotate -90°")

        # Mirror Buttons
        box.separator()
        box.label(text="Mirror:")
        row = box.row(align=True)
        row.operator("uv.textools_island_mirror_v", text="Mirror V")
        row.operator("uv.textools_island_mirror_h", text="Mirror H")

        # Fill Button
        box.separator()
        box.operator("uv.textools_uv_fill", text="Fill")

        # Move UVs
        box.separator()
        box.label(text="Move UVs:")
        box.prop(context.scene, "uv_offset_value", expand=True)

        row = box.row(align=True)
        row.operator("uv.move_uv", text="Front").direction = 'FRONT'
        row.operator("uv.move_uv", text="Back").direction = 'BACK'

        row = box.row(align=True)
        row.operator("uv.move_uv", text="Left").direction = 'LEFT'
        row.operator("uv.move_uv", text="Right").direction = 'RIGHT'

        # Scale UVs
        box.separator()
        box.label(text="Scale UVs to Pixels:")
        for size in [16, 32, 64, 128, 256]:
            box.operator("uv.scale_to_pixels", text=f"Scale to {size}px").target_pixels = str(size)

        # Move to Top-Left Button
        box.separator()
        box.operator("uv.move_to_top_left", text="Move to Top Left")
        
        # Align Operators
        box.separator()
        box.label(text="Align:")
        row = box.row(align=True)
        row.operator("uv.align_axis", text="Align X").axis = 'X'
        row.operator("uv.align_axis", text="Align Y").axis = 'Y'


# Operador para rotar 90° la isla UV
class UVIslandRotate90Operator(bpy.types.Operator):
    bl_idname = "uv.textools_island_rotate_90"
    bl_label = "Rotate UV Island 90°"
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

        center = mathutils.Vector((sum(uv[0] for uv in uvs) / len(uvs),
                                     sum(uv[1] for uv in uvs) / len(uvs)))
        angle = math.radians(90)
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        for uv in uvs:
            vec = uv - center
            x_new = vec.x * cos_angle - vec.y * sin_angle
            y_new = vec.x * sin_angle + vec.y * cos_angle
            uv[0] = center.x + x_new
            uv[1] = center.y + y_new

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


# Operador para rotar -90° la isla UV
class UVIslandRotateMinus90Operator(bpy.types.Operator):
    bl_idname = "uv.textools_island_rotate_minus_90"
    bl_label = "Rotate UV Island -90°"
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

        center = mathutils.Vector((sum(uv[0] for uv in uvs) / len(uvs),
                                     sum(uv[1] for uv in uvs) / len(uvs)))
        angle = math.radians(-90)
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        for uv in uvs:
            vec = uv - center
            x_new = vec.x * cos_angle - vec.y * sin_angle
            y_new = vec.x * sin_angle + vec.y * cos_angle
            uv[0] = center.x + x_new
            uv[1] = center.y + y_new

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


# Operador para espejar la isla UV verticalmente (reflejo en U)
class UVIslandMirrorVOperator(bpy.types.Operator):
    bl_idname = "uv.textools_island_mirror_v"
    bl_label = "Mirror UV Island Vertically"
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

        center_x = sum(uv[0] for uv in uvs) / len(uvs)
        for uv in uvs:
            uv[0] = 2 * center_x - uv[0]
        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


# Operador para espejar la isla UV horizontalmente (reflejo en V)
class UVIslandMirrorHOperator(bpy.types.Operator):
    bl_idname = "uv.textools_island_mirror_h"
    bl_label = "Mirror UV Island Horizontally"
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

        center_y = sum(uv[1] for uv in uvs) / len(uvs)
        for uv in uvs:
            uv[1] = 2 * center_y - uv[1]
        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


# Operador para escalar y trasladar la isla UV para que ocupe el área (0 a 1)
class UVIslandFillOperator(bpy.types.Operator):
    bl_idname = "uv.textools_uv_fill"
    bl_label = "Fill UV Island"
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
        max_u = max(uv[0] for uv in uvs)
        min_v = min(uv[1] for uv in uvs)
        max_v = max(uv[1] for uv in uvs)

        width = max_u - min_u
        height = max_v - min_v

        if width == 0 or height == 0:
            self.report({'ERROR'}, "Invalid UV bounds")
            return {'CANCELLED'}

        for uv in uvs:
            uv[0] = (uv[0] - min_u) / width
            uv[1] = (uv[1] - min_v) / height

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


# Operador para mover UVs
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


# Operador para escalar UVs a un tamaño específico
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


# Operador para mover UVs a la esquina superior izquierda
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


# Operador Align
class UVAlignAxisOperator(bpy.types.Operator):
    bl_idname = "uv.align_axis"
    bl_label = "Align Axis"
    bl_options = {'REGISTER', 'UNDO'}

    axis: bpy.props.EnumProperty(
        items=[
            ('X', "X", "Align along X"),
            ('Y', "Y", "Align along Y")
        ]
    )

    def execute(self, context):
        if self.axis == 'X':
            bpy.ops.transform.resize(value=(0, 1, 1), constraint_axis=(True, False, False))
        elif self.axis == 'Y':
            bpy.ops.transform.resize(value=(1, 0, 1), constraint_axis=(False, True, False))
        return {'FINISHED'}


# Registro de clases y propiedades
def register():
    bpy.utils.register_class(UVResetTexturePanel)
    bpy.utils.register_class(UVIslandRotate90Operator)
    bpy.utils.register_class(UVIslandRotateMinus90Operator)
    bpy.utils.register_class(UVIslandMirrorVOperator)
    bpy.utils.register_class(UVIslandMirrorHOperator)
    bpy.utils.register_class(UVIslandFillOperator)
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
    bpy.utils.unregister_class(UVIslandRotate90Operator)
    bpy.utils.unregister_class(UVIslandRotateMinus90Operator)
    bpy.utils.unregister_class(UVIslandMirrorVOperator)
    bpy.utils.unregister_class(UVIslandMirrorHOperator)
    bpy.utils.unregister_class(UVIslandFillOperator)
    bpy.utils.unregister_class(MoveUVOperator)
    bpy.utils.unregister_class(UVScaleToPixelsOperator)
    bpy.utils.unregister_class(MoveUVsTopLeftOperator)
    bpy.utils.unregister_class(UVAlignAxisOperator)

    del bpy.types.Scene.uv_offset_value


if __name__ == "__main__":
    register()
