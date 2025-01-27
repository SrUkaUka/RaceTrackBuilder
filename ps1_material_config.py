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

            # Find image texture node
            image_node = None
            for node in nodes:
                if node.type == 'TEX_IMAGE':
                    image_node = node
                    break

            if not image_node:  # If no image texture, log object
                no_image_objects.append(obj.name)
                continue

            # Set up the material
            mat.blend_method = "CLIP"

            # Remove non-image texture or output nodes
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

            # Set blend methods based on material name
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
        # Use context to display the warning
        bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text=f"Objects without image texture: {self_report}"), title="Warning", icon='ERROR')

    # Switch to rendered mode (commented out to avoid changing screen)
    # bpy.context.space_data.shading.type = 'RENDERED'  # This line is commented to avoid opening a new screen

def deactivate_ps1_render():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.material_slots:
            for slot in obj.material_slots:
                material = slot.material

                if material is not None:
                    material_output_node = material.node_tree.nodes.get('Material Output')
                    keep_node_types = ['TEX_IMAGE', 'OUTPUT_MATERIAL']

                    for node in material.node_tree.nodes:
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

                    if image_texture_node:
                        material.node_tree.links.new(image_texture_node.outputs['Color'], principled_bsdf_node.inputs['Base Color'])
                        material.node_tree.links.new(principled_bsdf_node.outputs['BSDF'], material_output_node.inputs['Surface'])
                else:
                    print("Object", obj.name, "does not have a material assigned.")

def menu_draw(self, context):
    self.layout.operator("object.setup_materials")
    self.layout.operator("object.deactivate_ps1_render")

class OBJECT_OT_SetupMaterials(bpy.types.Operator):
    bl_idname = "object.setup_materials"
    bl_label = "Setup PS1 Materials"
    bl_description = "Sets up PS1-style materials for all objects in the scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        setup_materials()
        return {'FINISHED'}

class OBJECT_OT_DeactivatePS1Render(bpy.types.Operator):
    bl_idname = "object.deactivate_ps1_render"
    bl_label = "Deactivate PS1 Render"
    bl_description = "Deactivates PS1-style render for all objects in the scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        deactivate_ps1_render()
        return {'FINISHED'}

# Register the classes and menu
classes = [OBJECT_OT_SetupMaterials, OBJECT_OT_DeactivatePS1Render]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object.append(menu_draw)

def unregister():
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            # Si ocurre un error al desregistrar, lo ignoramos.
            print(f"Error al desregistrar la clase {cls.__name__}")
    bpy.types.VIEW3D_MT_object.remove(menu_draw)

if __name__ == "__main__":
    register()
