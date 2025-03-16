import bpy

# Funciones para registrar y eliminar la propiedad
def register_properties():
    # Si ya existe, eliminarla de __annotations__ y del tipo
    if "ps1_split_screen" in bpy.types.Scene.__annotations__:
        del bpy.types.Scene.__annotations__["ps1_split_screen"]
    if hasattr(bpy.types.Scene, "ps1_split_screen"):
        del bpy.types.Scene.ps1_split_screen
    bpy.types.Scene.ps1_split_screen = bpy.props.BoolProperty(
        name="Split Screen",
        description="Activar para usar segunda pantalla, desactivar para aplicar render en el área actual",
        default=True
    )

def unregister_properties():
    if "ps1_split_screen" in bpy.types.Scene.__annotations__:
        del bpy.types.Scene.__annotations__["ps1_split_screen"]
    if hasattr(bpy.types.Scene, "ps1_split_screen"):
        del bpy.types.Scene.ps1_split_screen

def setup_materials():
    # Crear un diccionario que asocia cada material (con node_tree) a la lista de objetos que lo usan
    material_users = {}
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        for slot in obj.material_slots:
            mat = slot.material
            if mat and mat.node_tree:
                material_users.setdefault(mat, []).append(obj.name)

    # Iterar sobre cada material solo una vez
    for mat, users in material_users.items():
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Buscar nodo de textura de imagen
        image_node = None
        for node in nodes:
            if node.type == 'TEX_IMAGE':
                image_node = node
                break

        if not image_node:
            # Si el material no tiene nodo de imagen, avisar para cada objeto que lo usa
            for obj_name in users:
                print(f"Object without image texture: {obj_name}")
            continue

        # Configurar material
        mat.blend_method = "CLIP"

        # Obtener nodo Material Output (si existe)
        output_node = nodes.get("Material Output")
        # Eliminar nodos que no sean la textura de imagen o el output
        for node in list(nodes):
            if node != image_node and node != output_node:
                nodes.remove(node)

        if output_node:
            output_node.location = (700, 150)
        image_node.interpolation = "Closest"

        # Crear y configurar nodos adicionales
        col_node = nodes.new(type="ShaderNodeAttribute")
        col_node.attribute_name = "Color"
        col_node.location = (-350, -150)

        mix_node = nodes.new(type="ShaderNodeMixRGB")
        mix_node.blend_type = "MULTIPLY"
        mix_node.location = (-150, 0)
        mix_node.inputs[0].default_value = 1

        mult_node = nodes.new(type="ShaderNodeMixRGB")
        mult_node.blend_type = "MULTIPLY"
        mult_node.location = (50, 150)
        mult_node.inputs[0].default_value = 1.0
        mult_node.inputs[2].default_value = (4, 4, 4, 1)

        alpha_node = nodes.new(type="ShaderNodeBsdfTransparent")
        alpha_node.location = (250, -100)

        invert_node = nodes.new(type="ShaderNodeInvert")
        invert_node.inputs[0].default_value = 1
        invert_node.location = (250, 300)

        rgba_node = nodes.new(type="ShaderNodeMixShader")
        rgba_node.location = (500, 150)

        # Crear conexiones entre nodos
        links.new(image_node.outputs[0], mix_node.inputs[1])
        links.new(col_node.outputs[0], mix_node.inputs[2])
        links.new(mix_node.outputs[0], mult_node.inputs[1])
        links.new(image_node.outputs[1], invert_node.inputs[1])
        links.new(invert_node.outputs[0], rgba_node.inputs[0])
        links.new(mult_node.outputs[0], rgba_node.inputs[1])
        links.new(alpha_node.outputs[0], rgba_node.inputs[2])
        if output_node:
            links.new(rgba_node.outputs[0], output_node.inputs[0])

        # Configuración adicional según el nombre del material
        if mat.name.endswith("_0"):
            mat.blend_method = "BLEND"

        if mat.name.endswith("_1"):
            mat.blend_method = "BLEND"
            alpha2_node = nodes.new(type="ShaderNodeBsdfTransparent")
            alpha2_node.location = (250, -200)

            add_node = nodes.new(type="ShaderNodeAddShader")
            add_node.location = (500, 0)
            links.new(rgba_node.outputs[0], add_node.inputs[0])
            links.new(alpha2_node.outputs[0], add_node.inputs[1])
            if output_node:
                links.new(add_node.outputs[0], output_node.inputs[0])

# Panel en la nueva pestaña
class VIEW3D_PT_PS1MaterialsPanel(bpy.types.Panel):
    bl_label = "PS1 Materials"
    bl_idname = "VIEW3D_PT_PS1MaterialsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render PS1'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.setup_materials")
        layout.operator("object.deactivate_ps1_render")
        # Añadir checkbox de Split Screen
        layout.prop(context.scene, "ps1_split_screen", text="Split Screen")

class OBJECT_OT_SetupMaterials(bpy.types.Operator):
    bl_idname = "object.setup_materials"
    bl_label = "Set up PS1 Materials"
    bl_description = "Configura materiales estilo PS1 para todos los objetos de la escena"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.scene.ps1_split_screen:
            # Buscar una segunda área en la ventana actual
            second_area = None
            for area in bpy.context.screen.areas:
                if area != context.area:
                    second_area = area
                    break

            if second_area:
                # Cambiar la segunda área a 3D Viewport y configurar en modo Rendered
                second_area.type = 'VIEW_3D'
                for space in second_area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'RENDERED'
                        space.overlay.show_overlays = False
        else:
            # Si no se usa split screen, cambiar el área actual a 3D y modo Rendered
            if context.area.type == 'VIEW_3D':
                for space in context.area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'RENDERED'
                        space.overlay.show_overlays = False

        # Configurar materiales en estilo PS1 (procesa cada material una sola vez)
        setup_materials()

        return {'FINISHED'}

class OBJECT_OT_DeactivatePS1Render(bpy.types.Operator):
    bl_idname = "object.deactivate_ps1_render"
    bl_label = "Deactivate PS1 Render"
    bl_description = "Cambia el área de render a la pestaña Properties (o modo layout) y limpia los materiales"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.scene.ps1_split_screen:
            # Buscar una segunda área en la ventana actual
            second_area = None
            for area in bpy.context.screen.areas:
                if area != context.area:
                    second_area = area
                    break

            if second_area:
                # Cambiar la segunda área a Properties
                second_area.type = 'PROPERTIES'
        else:
            # Si no se usa split screen, restaurar el modo layout en el área actual
            if context.area.type == 'VIEW_3D':
                for space in context.area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'SOLID'
                        space.overlay.show_overlays = True

        # Limpiar materiales: procesar cada material solo una vez
        processed_materials = set()
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.material_slots:
                for slot in obj.material_slots:
                    material = slot.material
                    if material and material.node_tree and material not in processed_materials:
                        processed_materials.add(material)
                        material_output_node = material.node_tree.nodes.get('Material Output')

                        # Lista de tipos de nodos a conservar
                        keep_node_types = ['TEX_IMAGE', 'OUTPUT_MATERIAL']
                        for node in list(material.node_tree.nodes):
                            if node.type not in keep_node_types and node != material_output_node:
                                material.node_tree.nodes.remove(node)

                        # Crear un nuevo nodo Principled BSDF
                        principled_bsdf_node = material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
                        if 'Specular' in principled_bsdf_node.inputs:
                            principled_bsdf_node.inputs['Specular'].default_value = 0.0

                        # Buscar nodo de textura de imagen
                        image_texture_node = None
                        for node in material.node_tree.nodes:
                            if node.type == 'TEX_IMAGE':
                                image_texture_node = node
                                break

                        if image_texture_node and material_output_node:
                            # Conectar la textura al Principled BSDF
                            material.node_tree.links.new(
                                image_texture_node.outputs['Color'],
                                principled_bsdf_node.inputs['Base Color']
                            )
                            # Conectar el Principled BSDF al nodo de salida
                            material.node_tree.links.new(
                                principled_bsdf_node.outputs['BSDF'],
                                material_output_node.inputs['Surface']
                            )
                    else:
                        print("El objeto", obj.name, "no tiene material asignado o no posee node_tree.")

        return {'FINISHED'}

# Registrar las clases
classes = [
    VIEW3D_PT_PS1MaterialsPanel,
    OBJECT_OT_SetupMaterials,
    OBJECT_OT_DeactivatePS1Render,
]

def register():
    register_properties()
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    unregister_properties()

if __name__ == "__main__":
    register()
