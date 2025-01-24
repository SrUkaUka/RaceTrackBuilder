import bpy

def setup_materials():
    no_image_objects = []  # List to log objects without image textures

    for obj in bpy.data.objects:
        if obj.type != 'MESH':  # Only process meshes
            continue

        for mat_slot in obj.material_slots:
            mat = mat_slot.material

            if not mat or not mat.node_tree:
                continue

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # Search for image texture node
            image_node = None
            for node in nodes:
                if node.type == 'TEX_IMAGE':
                    image_node = node
                    break

            if not image_node:  # If no image texture, log object
                no_image_objects.append(obj.name)
                continue

            # Set up material
            mat.blend_method = "CLIP"

            # Remove nodes other than the image texture or output
            output_node = nodes.get("Material Output")
            for node in nodes:
                if node != image_node and node != output_node:
                    nodes.remove(node)

            output_node.location = (700, 150)
            image_node.interpolation = "Closest"

            # Create and set up additional nodes
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

            # Create links between nodes
            links.new(image_node.outputs[0], mix_node.inputs[1])
            links.new(col_node.outputs[0], mix_node.inputs[2])
            links.new(mix_node.outputs[0], mult_node.inputs[1])
            links.new(image_node.outputs[1], invert_node.inputs[1])
            links.new(invert_node.outputs[0], rgba_node.inputs[0])
            links.new(mult_node.outputs[0], rgba_node.inputs[1])
            links.new(alpha_node.outputs[0], rgba_node.inputs[2])
            links.new(rgba_node.outputs[0], output_node.inputs[0])

            # Set blend method based on material name
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

    # Show warnings if there are objects without image textures
    if no_image_objects:
        self_report = "\n".join(no_image_objects)
        print(f"Objects without image texture: {self_report}")

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


class OBJECT_OT_SetupMaterials(bpy.types.Operator):
    bl_idname = "object.setup_materials"
    bl_label = "Set up PS1 Materials"
    bl_description = "Set up PS1 style materials for all objects in the scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Search for an existing second area in the current window
        second_area = None
        for area in bpy.context.screen.areas:
            if area != context.area:
                second_area = area
                break

        if second_area:
            # Change the second area to 3D Viewport and set Rendered mode
            second_area.type = 'VIEW_3D'
            for space in second_area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'
                    space.overlay.show_overlays = False

        # Set up materials in PS1 style
        setup_materials()

        return {'FINISHED'}


class OBJECT_OT_DeactivatePS1Render(bpy.types.Operator):
    bl_idname = "object.deactivate_ps1_render"
    bl_label = "Deactivate PS1 Render"
    bl_description = "Switch render area to the Properties panel and clean materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Search for an existing second area in the current window
        second_area = None
        for area in bpy.context.screen.areas:
            if area != context.area:
                second_area = area
                break

        if second_area:
            # Change the second area to Properties
            second_area.type = 'PROPERTIES'

        # Clean materials
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.material_slots:
                for slot in obj.material_slots:
                    material = slot.material

                    if material is not None:
                        # Get the material output node
                        material_output_node = material.node_tree.nodes.get('Material Output')

                        # Create a list of nodes to keep
                        keep_node_types = ['TEX_IMAGE', 'OUTPUT_MATERIAL']

                        # Remove all nodes except those we want to keep
                        for node in material.node_tree.nodes:
                            if node.type not in keep_node_types and node != material_output_node:
                                material.node_tree.nodes.remove(node)

                        # Create a new Principled BSDF node
                        principled_bsdf_node = material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')

                        # If 'Specular' node is not available, handle it this way:
                        if 'Specular' in principled_bsdf_node.inputs:
                            principled_bsdf_node.inputs['Specular'].default_value = 0.0

                        # Get the image texture node
                        image_texture_node = None
                        for node in material.node_tree.nodes:
                            if node.type == 'TEX_IMAGE':
                                image_texture_node = node
                                break

                        if image_texture_node:
                            # Connect the image texture to the Principled BSDF
                            material.node_tree.links.new(image_texture_node.outputs['Color'], principled_bsdf_node.inputs['Base Color'])

                            # Connect the Principled BSDF to the material output node
                            material.node_tree.links.new(principled_bsdf_node.outputs['BSDF'], material_output_node.inputs['Surface'])

                    else:
                        print("Object", obj.name, "does not have a material assigned.")

        return {'FINISHED'}

# Register the classes
classes = [VIEW3D_PT_PS1MaterialsPanel, OBJECT_OT_SetupMaterials, OBJECT_OT_DeactivatePS1Render]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
