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

        # Sección: Operaciones básicas
        box = layout.box()
        box.operator("uv.reset", text="Reset Texture")
        
        # Rotación
        box.label(text="Rotation:")
        row = box.row(align=True)
        row.operator("uv.textools_island_rotate_90", text="Rotate 90°")
        row.operator("uv.textools_island_rotate_minus_90", text="Rotate -90°")
        
        # Espejado
        box.separator()
        box.label(text="Mirror:")
        row = box.row(align=True)
        row.operator("uv.textools_island_mirror_v", text="Mirror V")
        row.operator("uv.textools_island_mirror_h", text="Mirror H")
        
        # Fill
        box.separator()
        box.operator("uv.textools_uv_fill", text="Fill")
        
        # Movimiento de UVs
        box.separator()
        box.label(text="Move UVs:")
        # Siempre se muestran los botones direccionales
        row = box.row(align=True)
        row.operator("uv.move_uv", text="Front").direction = 'FRONT'
        row.operator("uv.move_uv", text="Back").direction = 'BACK'
        row = box.row(align=True)
        row.operator("uv.move_uv", text="Left").direction = 'LEFT'
        row.operator("uv.move_uv", text="Right").direction = 'RIGHT'
        # Selección de cantidad de movimiento
        box.prop(context.scene, "uv_offset_value", text="Offset")
        if context.scene.uv_offset_value == "Other":
            box.prop(context.scene, "uv_offset_custom_x", text="Custom Offset X")
            box.prop(context.scene, "uv_offset_custom_y", text="Custom Offset Y")
        
        # Escala de UVs
        box.separator()
        box.label(text="Scale UVs to Pixels:")
        box.prop(context.scene, "uv_scale_target", text="Target Size")
        if context.scene.uv_scale_target == "Other":
            box.prop(context.scene, "uv_scale_custom_width", text="Custom Width")
            box.prop(context.scene, "uv_scale_custom_height", text="Custom Height")
        op_scale = box.operator("uv.scale_to_pixels", text="Apply Scale")
        op_scale.target_pixels = context.scene.uv_scale_target
        
        # Botón "Move to Top Left"
        box.separator()
        box.label(text="Extra:")
        box.operator("uv.move_to_top_left", text="Move to Top Left")
        
        # Align operators
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


# Operador para mover UVs con botones direccionales (utilizando valores predefinidos o personalizados)
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
        
        # Si se selecciona "Other", usamos los valores personalizados correspondientes
        if context.scene.uv_offset_value == "Other":
            # Para movimientos verticales se usa el custom Y, y horizontal el custom X
            if self.direction in ('FRONT', 'BACK'):
                move_pixels = context.scene.uv_offset_custom_y
            else:
                move_pixels = context.scene.uv_offset_custom_x
        else:
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


# Operador para escalar UVs a un tamaño específico o personalizado
class UVScaleToPixelsOperator(bpy.types.Operator):
    bl_idname = "uv.scale_to_pixels"
    bl_label = "Scale UV to Pixels"
    bl_options = {'REGISTER', 'UNDO'}

    target_pixels: bpy.props.EnumProperty(
        name="Target Size",
        items=[
            ("16", "16px", "Scale UVs to 16 pixels"),
            ("32", "32px", "Scale UVs to 32 pixels"),
            ("64", "64px", "Scale UVs to 64 pixels"),
            ("128", "128px", "Scale UVs to 128 pixels"),
            ("256", "256px", "Scale UVs to 256 pixels"),
            ("Other", "Other", "Custom scale value")
        ],
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
        if self.target_pixels == "Other":
            target_width = context.scene.uv_scale_custom_width
            target_height = context.scene.uv_scale_custom_height
        else:
            target_size = int(self.target_pixels)
            target_width = target_size
            target_height = target_size
        scale_factor_u = target_width / uv_width if uv_width > 0 else 1
        scale_factor_v = target_height / uv_height if uv_height > 0 else 1
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

    # Propiedades para mover UVs
    bpy.types.Scene.uv_offset_value = bpy.props.EnumProperty(
        name="Offset",
        items=[
            ("16", "16px", "Move UVs by 16 pixels"),
            ("32", "32px", "Move UVs by 32 pixels"),
            ("64", "64px", "Move UVs by 64 pixels"),
            ("128", "128px", "Move UVs by 128 pixels"),
            ("256", "256px", "Move UVs by 256 pixels"),
            ("Other", "Other", "Custom offset value")
        ],
        default='64'
    )
    bpy.types.Scene.uv_offset_custom_x = bpy.props.IntProperty(
        name="Custom Offset X",
        default=0,
        min=0,
        description="Custom offset in pixels for X (only whole, positive numbers)"
    )
    bpy.types.Scene.uv_offset_custom_y = bpy.props.IntProperty(
        name="Custom Offset Y",
        default=0,
        min=0,
        description="Custom offset in pixels for Y (only whole, positive numbers)"
    )

    # Propiedades para escalar UVs
    bpy.types.Scene.uv_scale_target = bpy.props.EnumProperty(
        name="Scale Target",
        items=[
            ("16", "16px", "Scale UVs to 16 pixels"),
            ("32", "32px", "Scale UVs to 32 pixels"),
            ("64", "64px", "Scale UVs to 64 pixels"),
            ("128", "128px", "Scale UVs to 128 pixels"),
            ("256", "256px", "Scale UVs to 256 pixels"),
            ("Other", "Other", "Custom scale value")
        ],
        default='64'
    )
    bpy.types.Scene.uv_scale_custom_width = bpy.props.FloatProperty(
        name="Custom Scale Width",
        default=64.0,
        min=0.0,
        description="Custom width in pixels"
    )
    bpy.types.Scene.uv_scale_custom_height = bpy.props.FloatProperty(
        name="Custom Scale Height",
        default=64.0,
        min=0.0,
        description="Custom height in pixels"
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
    del bpy.types.Scene.uv_offset_custom_x
    del bpy.types.Scene.uv_offset_custom_y
    del bpy.types.Scene.uv_scale_target
    del bpy.types.Scene.uv_scale_custom_width
    del bpy.types.Scene.uv_scale_custom_height


if __name__ == "__main__":
    register()
