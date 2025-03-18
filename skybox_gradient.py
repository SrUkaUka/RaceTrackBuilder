import bpy
import json
import os
from bpy_extras.io_utils import ExportHelper

# Global variable to store gradient values
saved_gradient_values = []

# Function to create or remove the gradient
def toggle_gradient(enable):
    global saved_gradient_values  # Explicitly declare the global variable
    world = bpy.context.scene.world

    # Check if the world uses nodes, if not, enable them
    if not world.use_nodes:
        world.use_nodes = True

    # If the gradient is disabled, save the current values and clear the nodes
    if not enable:
        color_ramp = get_color_ramp_node(world)
        if color_ramp:
            # Save the complete tuple (position, RGBA) as float (la precisión interna se mantiene)
            saved_gradient_values = [
                (element.position, tuple(element.color)) for element in color_ramp.color_ramp.elements
            ]
        world.use_nodes = False
        return

    # If the gradient is enabled, clear the current nodes
    world.node_tree.nodes.clear()

    # Create nodes for the gradient
    background = world.node_tree.nodes.new(type="ShaderNodeBackground")
    gradient_texture = world.node_tree.nodes.new(type="ShaderNodeTexGradient")
    texture_coord = world.node_tree.nodes.new(type="ShaderNodeTexCoord")
    mapping = world.node_tree.nodes.new(type="ShaderNodeMapping")
    separate_xyz = world.node_tree.nodes.new(type="ShaderNodeSeparateXYZ")
    color_ramp = world.node_tree.nodes.new(type="ShaderNodeValToRGB")
    
    # Set the interpolation of the ColorRamp node to 'LINEAR' (modificado)
    color_ramp.color_ramp.interpolation = 'EASE'

    # Arrange nodes in specific positions
    background.location = (0, 0)
    gradient_texture.location = (140, 0)
    texture_coord.location = (-140, 0)
    mapping.location = (400, 0)
    separate_xyz.location = (600, 0)
    color_ramp.location = (800, 0)

    # Adjust the Z location of the Mapping node to 0.4
    mapping.inputs["Location"].default_value[2] = 0.4  # Z to 0.4

    # Connect the nodes
    world.node_tree.links.new(texture_coord.outputs["Generated"], mapping.inputs["Vector"])
    world.node_tree.links.new(mapping.outputs["Vector"], separate_xyz.inputs["Vector"])
    world.node_tree.links.new(separate_xyz.outputs["Z"], gradient_texture.inputs["Vector"])
    world.node_tree.links.new(gradient_texture.outputs["Color"], color_ramp.inputs["Fac"])
    world.node_tree.links.new(color_ramp.outputs["Color"], background.inputs["Color"])

    # Set the gradient type
    gradient_texture.gradient_type = 'EASING'

    # If there are saved values, restore them
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
        # If there are no saved values, set default values
        elements = color_ramp.color_ramp.elements
        elements[0].position = 0.0
        new_elem = elements.new(0.2)
        new_elem.color = (0.0, 0.5, 1.0, 1.0)  # Light blue
        new_elem = elements.new(0.6)
        new_elem.color = (1.0, 1.0, 0.0, 1.0)  # Yellow

    # Set the Background strength
    background.inputs["Strength"].default_value = 0.600

    # Add the World Output node and connect the Background to it
    world_output = world.node_tree.nodes.new(type="ShaderNodeOutputWorld")
    world.node_tree.links.new(background.outputs["Background"], world_output.inputs["Surface"])

    # Render settings:
    bpy.data.worlds["World"].node_tree.nodes["Color Ramp"].color_ramp.interpolation = 'EASE'
    bpy.context.scene.view_settings.look = 'None'
    bpy.context.scene.view_settings.view_transform = 'Standard'

    print("Gradient activated from bottom to top.")

# Function to get the ColorRamp node
def get_color_ramp_node(world):
    for node in world.node_tree.nodes:
        if isinstance(node, bpy.types.ShaderNodeValToRGB):
            return node
    return None

# Operator to toggle the gradient
class ToggleGradientOperator(bpy.types.Operator):
    bl_idname = "world.toggle_gradient"
    bl_label = "Enable/Disable Gradient"
    
    is_gradient_enabled: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        toggle_gradient(self.is_gradient_enabled)
        self.is_gradient_enabled = not self.is_gradient_enabled
        return {'FINISHED'}

# Operator to switch the active area to ShaderNodeTree and set the shader to 'WORLD'
class SwitchToShaderNodeTreeOperator(bpy.types.Operator):
    bl_idname = "wm.switch_to_shader_nodetree"
    bl_label = "Open Shader Node Editor"

    def execute(self, context):
        # Change the active area to 'NODE_EDITOR'
        for area in bpy.context.screen.areas:
            if area.type == 'OUTLINER':  # Look for the 'OUTLINER' area (or the currently used area)
                area.ui_type = 'ShaderNodeTree'  # Switch to 'ShaderNodeTree'
                # Ensure we are in the node editor
                if area.spaces:
                    for space in area.spaces:
                        if space.type == 'NODE_EDITOR':
                            space.shader_type = 'WORLD'  # Set shader to 'WORLD'
                break

        return {'FINISHED'}

# Operator to finish the skybox setup and return to the Outliner
class FinishSkyboxOperator(bpy.types.Operator):
    bl_idname = "world.finish_skybox"
    bl_label = "Finish Skybox"

    def execute(self, context):
        # Change the UI space to 'OUTLINER' in the secondary area
        screen = bpy.context.screen
        areas = screen.areas

        # If there is more than one area, change the second one to 'OUTLINER'
        if len(areas) > 1:
            secondary_area = areas[1]
            secondary_area.ui_type = 'OUTLINER'
        
        return {'FINISHED'}

# Operator to print the gradient values with 17 decimales
class PrintGradientValuesOperator(bpy.types.Operator):
    bl_idname = "world.print_gradient_values"
    bl_label = "Print Gradient Values"

    def execute(self, context):
        world = bpy.context.scene.world
        color_ramp = get_color_ramp_node(world)

        # Si existe el nodo ColorRamp, imprime y guarda los valores con alta precisión
        if color_ramp:
            global saved_gradient_values
            saved_gradient_values = []  # Limpiar valores previos
            for i, element in enumerate(color_ramp.color_ramp.elements):
                # Se convierte la posición al rango deseado, pero se formatea a 17 dígitos decimales en la impresión
                position = (element.position * 280.0) - 140.0
                rgba = tuple(element.color)  # Se obtienen los 4 componentes (RGBA)
                saved_gradient_values.append((element.position, rgba))
                # Se imprimen los valores RGB con 17 dígitos decimales
                print(f"Position: {position:.17f}, RGB: {rgba[0]:.17f}, {rgba[1]:.17f}, {rgba[2]:.17f}")
        return {'FINISHED'}

# Panel to display RGB values and gradient options
class GradientPanel(bpy.types.Panel):
    bl_label = "Gradient Settings"
    bl_idname = "VIEW3D_PT_gradient_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Gradient"

    def draw(self, context):
        layout = self.layout
        world = bpy.context.scene.world

        # Always show the button to enable/disable the gradient
        layout.operator("world.toggle_gradient", text="Enable/Disable Gradient")
        
        # If the gradient is enabled, show other buttons
        if world.use_nodes:
            color_ramp = get_color_ramp_node(world)

            if color_ramp:
                layout.operator("wm.switch_to_shader_nodetree", text="Open Node Editor")
                layout.operator("world.finish_skybox", text="Finish Skybox")
                layout.operator("world.print_gradient_values", text="Print Values")

                layout.label(text="Current RGB Values:")
                for i, element in enumerate(color_ramp.color_ramp.elements):
                    position = (element.position * 280.0) - 140.0  # Convert to range -140:140
                    rgb = tuple(int(c * 255) for c in element.color[:3])  # Convert color values to integers (0-255)
                    label_text = "From" if i % 2 == 0 else "To"
                    layout.label(text=f"{label_text} Position: {position:.2f}, RGB: {rgb[0]}, {rgb[1]}, {rgb[2]}")
            else:
                layout.label(text="No gradient has been created")
        else:
            layout.label(text="The gradient is disabled. Press 'Enable Gradient' to start.")

# Class registration
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
