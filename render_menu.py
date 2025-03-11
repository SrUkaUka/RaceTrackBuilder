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
    no_image_objects = []  # Lista para registrar objetos sin textura de imagen

    for obj in bpy.data.objects:
        if obj.type != 'MESH':  # Solo procesar mallas
            continue

        for mat_slot in obj.material_slots:
            mat = mat_slot.material

            if not mat or not mat.node_tree:
                continue

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # Buscar nodo de textura de imagen
            image_node = None
            for node in nodes:
                if node.type == 'TEX_IMAGE':
                    image_node = node
                    break

            if not image_node:  # Si no hay nodo de imagen, registrar objeto
                no_image_objects.append(obj.name)
                continue

            # Configurar material
            mat.blend_method = "CLIP"

            # Eliminar nodos que no sean la textura de imagen o el output
            output_node = nodes.get("Material Output")
            for node in list(nodes):
                if node != image_node and node != output_node:
                    nodes.remove(node)

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
                links.new(add_node.outputs[0], output_node.inputs[0])

    # Mostrar advertencias si hay objetos sin textura de imagen
    if no_image_objects:
        self_report = "\n".join(no_image_objects)
        print(f"Objects without image texture: {self_report}")

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

        # Configurar materiales en estilo PS1
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

        # Limpiar materiales
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.material_slots:
                for slot in obj.material_slots:
                    material = slot.material

                    if material is not None and material.node_tree:
                        # Obtener el nodo Material Output
                        material_output_node = material.node_tree.nodes.get('Material Output')

                        # Lista de tipos de nodos a conservar
                        keep_node_types = ['TEX_IMAGE', 'OUTPUT_MATERIAL']

                        # Eliminar nodos que no se quieren conservar
                        for node in list(material.node_tree.nodes):
                            if node.type not in keep_node_types and node != material_output_node:
                                material.node_tree.nodes.remove(node)

                        # Crear un nuevo nodo Principled BSDF
                        principled_bsdf_node = material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')

                        # Ajuste de Specular si está disponible
                        if 'Specular' in principled_bsdf_node.inputs:
                            principled_bsdf_node.inputs['Specular'].default_value = 0.0

                        # Buscar nodo de textura de imagen
                        image_texture_node = None
                        for node in material.node_tree.nodes:
                            if node.type == 'TEX_IMAGE':
                                image_texture_node = node
                                break

                        if image_texture_node:
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
