import bpy

# Variable global para guardar los valores del gradiente
saved_gradient_values = []

# Función para crear o eliminar el gradiente
def toggle_gradient(enable):
    global saved_gradient_values
    world = bpy.context.scene.world

    # Verificar si hay nodos en el mundo
    if not world.use_nodes:
        world.use_nodes = True

    # Eliminar nodos actuales si hay y el gradiente está desactivado
    if not enable:
        # Guardar los valores actuales del ColorRamp antes de desactivarlo
        color_ramp = get_color_ramp_node(world)
        if color_ramp:
            saved_gradient_values = [(element.position, element.color) for element in color_ramp.color_ramp.elements]

        world.use_nodes = False
        return

    # Si el gradiente está habilitado, crear los nodos
    world.node_tree.nodes.clear()  # Limpiar nodos actuales

    # Crear los nodos para el gradiente
    background = world.node_tree.nodes.new(type="ShaderNodeBackground")
    gradient_texture = world.node_tree.nodes.new(type="ShaderNodeTexGradient")
    texture_coord = world.node_tree.nodes.new(type="ShaderNodeTexCoord")
    mapping = world.node_tree.nodes.new(type="ShaderNodeMapping")
    separate_xyz = world.node_tree.nodes.new(type="ShaderNodeSeparateXYZ")
    color_ramp = world.node_tree.nodes.new(type="ShaderNodeValToRGB")

    # Organizar nodos en posiciones específicas
    background.location = (0, 0)
    gradient_texture.location = (220, 0)
    texture_coord.location = (-220, 0)
    mapping.location = (400, 0)
    separate_xyz.location = (600, 0)
    color_ramp.location = (800, 0)

    # Establecer la ubicación en Z del nodo Mapping a 0.4
    mapping.inputs["Location"].default_value[2] = 0.4  # Establecer Z en 0.4

    # Conectar los nodos
    world.node_tree.links.new(texture_coord.outputs["Generated"], mapping.inputs["Vector"])
    world.node_tree.links.new(mapping.outputs["Vector"], separate_xyz.inputs["Vector"])
    world.node_tree.links.new(separate_xyz.outputs["Z"], gradient_texture.inputs["Vector"])
    world.node_tree.links.new(gradient_texture.outputs["Color"], color_ramp.inputs["Fac"])
    world.node_tree.links.new(color_ramp.outputs["Color"], background.inputs["Color"])

    # Configurar el tipo de gradiente
    gradient_texture.gradient_type = 'LINEAR'

    # Si existen valores guardados, restaurarlos
    if saved_gradient_values:
        elements = color_ramp.color_ramp.elements
        for i, (position, color) in enumerate(saved_gradient_values):
            if i < len(elements):
                elements[i].position = position
                elements[i].color = color
            else:
                new_element = elements.new(position)
                new_element.color = color
    else:
        # Si no hay valores guardados, establecer valores predeterminados
        elements = color_ramp.color_ramp.elements
        elements[0].position = 0.0
        elements[0].color = (0.0, 0.0, 1.0, 1.0)  # Azul
        elements.new(0.2).color = (0.0, 0.5, 1.0, 1.0)  # Azul claro
        elements.new(0.4).color = (0.0, 1.0, 1.0, 1.0)  # Cian
        elements.new(0.6).color = (1.0, 1.0, 0.0, 1.0)  # Amarillo
        elements.new(0.8).color = (1.0, 0.5, 0.0, 1.0)  # Naranja

    # Establecer el valor predeterminado de 'Background' a 0.600
    background.inputs["Strength"].default_value = 0.600

    # Añadir el nodo World Output y conectar el nodo Background a este
    world_output = world.node_tree.nodes.new(type="ShaderNodeOutputWorld")
    world.node_tree.links.new(background.outputs["Background"], world_output.inputs["Surface"])

    print("Gradiente activado de abajo hacia arriba.")

# Función para obtener el nodo ColorRamp
def get_color_ramp_node(world):
    for node in world.node_tree.nodes:
        if isinstance(node, bpy.types.ShaderNodeValToRGB):
            return node
    return None

# Operador para alternar el gradiente
class ToggleGradientOperator(bpy.types.Operator):
    bl_idname = "world.toggle_gradient"
    bl_label = "Activar/Desactivar Gradiente"
    
    is_gradient_enabled: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        toggle_gradient(self.is_gradient_enabled)
        self.is_gradient_enabled = not self.is_gradient_enabled
        return {'FINISHED'}

# Operador para cambiar el área activa a ShaderNodeTree y configurar el shader en 'WORLD'
class SwitchToShaderNodeTreeOperator(bpy.types.Operator):
    bl_idname = "wm.switch_to_shader_nodetree"
    bl_label = "Abrir Editor de Nodos de Shaders"

    def execute(self, context):
        # Cambiar el área activa al tipo 'NODE_EDITOR'
        for area in bpy.context.screen.areas:
            if area.type == 'OUTLINER':  # Buscar el área 'OUTLINER' (o cualquier área que puedas estar usando)
                area.ui_type = 'ShaderNodeTree'  # Cambiar el tipo a 'ShaderNodeTree'
                # Asegurarse de que estamos en el editor de nodos
                if area.spaces:
                    for space in area.spaces:
                        if space.type == 'NODE_EDITOR':  # Asegúrate de estar en un editor de nodos
                            space.shader_type = 'WORLD'  # Cambiar tipo de shader a 'WORLD'
                break

        return {'FINISHED'}

# Operador para finalizar el skybox y volver al Outliner
class FinishSkyboxOperator(bpy.types.Operator):
    bl_idname = "world.finish_skybox"
    bl_label = "Finalizar Skybox"

    def execute(self, context):
        # Cambiar el espacio de UI al 'OUTLINER' en el área secundaria
        screen = bpy.context.screen
        areas = screen.areas

        # Si hay más de un área, cambiar la segunda área a 'OUTLINER'
        if len(areas) > 1:
            secondary_area = areas[1]
            secondary_area.ui_type = 'OUTLINER'
        
        return {'FINISHED'}

# Operador para imprimir los valores del gradiente
class PrintGradientValuesOperator(bpy.types.Operator):
    bl_idname = "world.print_gradient_values"
    bl_label = "Imprimir Valores del Gradiente"

    def execute(self, context):
        world = bpy.context.scene.world
        color_ramp = get_color_ramp_node(world)

        # Si existe el nodo ColorRamp, imprimir los valores en formato RGB
        if color_ramp:
            for element in color_ramp.color_ramp.elements:
                position = (element.position * 440.0) - 220.0  # Convertir de 0.0:1.0 a -220:220
                # Convertir los valores de color a enteros (0-255)
                rgb = tuple(int(c * 255) for c in element.color[:3])
                print(f"Posición: {position:.2f}, RGB: {rgb[0]}, {rgb[1]}, {rgb[2]}")
        return {'FINISHED'}

# Panel para mostrar los valores RGB y la actualización del gradiente
class GradientPanel(bpy.types.Panel):
    bl_label = "Configuración de Gradiente"
    bl_idname = "VIEW3D_PT_gradient_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Gradiente"

    def draw(self, context):
        layout = self.layout
        world = bpy.context.scene.world

        # Mostrar siempre el botón para activar el gradiente
        layout.operator("world.toggle_gradient", text="Activar/Desactivar Gradiente")
        
        # Si el gradiente ha sido activado, mostrar los otros botones
        if world.use_nodes:
            color_ramp = get_color_ramp_node(world)

            # Si existe el nodo ColorRamp, mostrar los valores
            if color_ramp:
                # Colocar el botón para abrir el editor de nodos de shaders
                layout.operator("wm.switch_to_shader_nodetree", text="Abrir Editor de Nodos de Shaders")
                
                layout.operator("world.finish_skybox", text="Finalizar Skybox")
                layout.operator("world.print_gradient_values", text="Imprimir Valores")

                layout.label(text="Valores RGB actuales:")
                for element in color_ramp.color_ramp.elements:
                    position = (element.position * 440.0) - 220.0  # Convertir de 0.0:1.0 a -220:220
                    # Convertir los valores de color a enteros (0-255)
                    rgb = tuple(int(c * 255) for c in element.color[:3])
                    layout.label(text=f"Posición: {position:.2f}, RGB: {rgb[0]}, {rgb[1]}, {rgb[2]}")

            else:
                layout.label(text="No se ha creado un gradiente")
        else:
            layout.label(text="Gradiente desactivado. Presione 'Activar Gradiente' para comenzar.")

# Registrar las clases
def register():
    bpy.utils.register_class(ToggleGradientOperator)
    bpy.utils.register_class(SwitchToShaderNodeTreeOperator)
    bpy.utils.register_class(FinishSkyboxOperator)
    bpy.utils.register_class(PrintGradientValuesOperator)
    bpy.utils.register_class(GradientPanel)

def unregister():
    bpy.utils.unregister_class(ToggleGradientOperator)
    bpy.utils.unregister_class(SwitchToShaderNodeTreeOperator)
    bpy.utils.unregister_class(FinishSkyboxOperator)
    bpy.utils.unregister_class(PrintGradientValuesOperator)
    bpy.utils.unregister_class(GradientPanel)

if __name__ == "__main__":
    register()
