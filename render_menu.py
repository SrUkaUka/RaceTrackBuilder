import bpy

# Functions to register and remove the property
def register_properties():
    if "ps1_split_screen" in bpy.types.Scene.__annotations__:
        del bpy.types.Scene.__annotations__["ps1_split_screen"]
    if hasattr(bpy.types.Scene, "ps1_split_screen"):
        del bpy.types.Scene.ps1_split_screen
    bpy.types.Scene.ps1_split_screen = bpy.props.BoolProperty(
        name="Split Screen",
        description="Activate to use second screen, deactivate to apply render in the current area",
        default=True
    )

def unregister_properties():
    if "ps1_split_screen" in bpy.types.Scene.__annotations__:
        del bpy.types.Scene.__annotations__["ps1_split_screen"]
    if hasattr(bpy.types.Scene, "ps1_split_screen"):
        del bpy.types.Scene.ps1_split_screen

def setup_materials():
    # Create a dictionary that associates each material (with node_tree) to the list of objects using it
    material_users = {}
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        for slot in obj.material_slots:
            mat = slot.material
            if mat and mat.node_tree:
                material_users.setdefault(mat, []).append(obj.name)

    # Iterate over each material only once
    for mat, users in material_users.items():
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Find image texture node
        image_node = None
        for node in nodes:
            if node.type == 'TEX_IMAGE':
                image_node = node
                break

        if not image_node:
            # If the material doesn't have an image node, notify for each object using it
            for obj_name in users:
                print(f"Object without image texture: {obj_name}")
            continue

        # Set up material
        mat.blend_method = "CLIP"

        # Get Material Output node (if exists)
        output_node = nodes.get("Material Output")
        # Remove nodes that are not the image texture or the output
        for node in list(nodes):
            if node != image_node and node != output_node:
                nodes.remove(node)

        if output_node:
            output_node.location = (700, 150)
        image_node.interpolation = "Closest"

        # Create and set up additional nodes
        attr_node = nodes.new(type="ShaderNodeAttribute")
        attr_node.attribute_name = "Attribute"
        attr_node.location = (-350, -150)

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

        # Create connections between nodes
        links.new(image_node.outputs[0], mix_node.inputs[1])
        links.new(attr_node.outputs[0], mix_node.inputs[2])
        links.new(mix_node.outputs[0], mult_node.inputs[1])
        links.new(image_node.outputs[1], invert_node.inputs[1])
        links.new(invert_node.outputs[0], rgba_node.inputs[0])
        links.new(mult_node.outputs[0], rgba_node.inputs[1])
        links.new(alpha_node.outputs[0], rgba_node.inputs[2])
        if output_node:
            links.new(rgba_node.outputs[0], output_node.inputs[0])

        # Additional setup based on the material name
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

# Panel in the new tab
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
        layout.prop(context.scene, "ps1_split_screen", text="Split Screen")

class OBJECT_OT_SetupMaterials(bpy.types.Operator):
    bl_idname = "object.setup_materials"
    bl_label = "Set up PS1 Materials"
    bl_description = "Set up PS1 style materials for all objects in the scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.scene.ps1_split_screen:
            # Find a second area in the current window
            second_area = None
            for area in bpy.context.screen.areas:
                if area != context.area:
                    second_area = area
                    break

            if second_area:
                second_area.type = 'VIEW_3D'
                for space in second_area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'RENDERED'
                        space.overlay.show_overlays = False
        else:
            if context.area.type == 'VIEW_3D':
                for space in context.area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'RENDERED'
                        space.overlay.show_overlays = False

        setup_materials()

        # Change view_transform and look to Standard and Medium Contrast
        bpy.context.scene.view_settings.view_transform = 'Standard'
        bpy.context.scene.view_settings.look = 'None'

        return {'FINISHED'}

class OBJECT_OT_DeactivatePS1Render(bpy.types.Operator):
    bl_idname = "object.deactivate_ps1_render"
    bl_label = "Deactivate PS1 Render"
    bl_description = "Switch render area to Properties tab (or layout mode) and clean up materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.scene.ps1_split_screen:
            second_area = None
            for area in bpy.context.screen.areas:
                if area != context.area:
                    second_area = area
                    break

            if second_area:
                second_area.type = 'PROPERTIES'
        else:
            if context.area.type == 'VIEW_3D':
                for space in context.area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'SOLID'
                        space.overlay.show_overlays = True

        # Clean up materials: process each material only once
        processed_materials = set()
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.material_slots:
                for slot in obj.material_slots:
                    material = slot.material
                    if material and material.node_tree and material not in processed_materials:
                        processed_materials.add(material)
                        material_output_node = material.node_tree.nodes.get('Material Output')

                        keep_node_types = ['TEX_IMAGE', 'OUTPUT_MATERIAL']
                        for node in list(material.node_tree.nodes):
                            if node.type not in keep_node_types and node != material_output_node:
                                material.node_tree.nodes.remove(node)

                        principled_bsdf_node = material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
                        if 'Specular' in principled_bsdf_node.inputs:
                            principled_bsdf_node.inputs['Specular'].default_value = 0.0

                        image_texture_node = None
                        for node in material.node_tree.nodes:
                            if node.type == 'TEX_IMAGE':
                                image_texture_node = node
                                break

                        if image_texture_node and material_output_node:
                            material.node_tree.links.new(
                                image_texture_node.outputs['Color'],
                                principled_bsdf_node.inputs['Base Color']
                            )
                            material.node_tree.links.new(
                                principled_bsdf_node.outputs['BSDF'],
                                material_output_node.inputs['Surface']
                            )
                    else:
                        print(f"The object {obj.name} does not have an assigned material or does not have a node_tree.")

        return {'FINISHED'}

# Register classes
classes = [
    VIEW3D_PT_PS1MaterialsPanel,
    OBJECT_OT_SetupMaterials,
    OBJECT_OT_DeactivatePS1Render
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_properties()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    unregister_properties()

if __name__ == "__main__":
    register()
