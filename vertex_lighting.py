import bpy

def add_vertex_lighting(light_type='SUN'):
    # Get the active object
    obj = bpy.context.object
    if obj is None or obj.type != 'MESH':
        print("Select a mesh object to continue.")
        return

    # Create the color attribute "Attribute" if it does not exist
    if "Attribute" not in obj.data.color_attributes:
        obj.data.color_attributes.new(name="Attribute", type='BYTE_COLOR', domain='CORNER')
        print("Color attribute 'Attribute' created with 'FACE CORNER' domain.")
    else:
        print("Color attribute 'Attribute' already exists.")

    # Add the light without checking if one of this type already exists in the scene,
    # which allows inserting multiple lights of the same type.
    bpy.ops.object.light_add(type=light_type, align='WORLD', location=(0, 0, 10))
    print(f"Light of type '{light_type}' created.")

    # Set Cycles as the render engine and set the bake type
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.bake_type = 'COMBINED'
    print("Rendering engine set to Cycles.")

def bake_vertex_lighting():
    # Get the active object
    obj = bpy.context.object
    if obj is None or obj.type != 'MESH':
        print("Select a mesh object to continue.")
        return

    # Ensure that the 'Attribute' attribute is active
    if "Attribute" in obj.data.color_attributes:
        obj.data.color_attributes.active = obj.data.color_attributes["Attribute"]
        print("Color attribute 'Attribute' is active.")
    else:
        print("Color attribute 'Attribute' doesn't exist. Use 'Add Vertex Lighting' first.")
        return

    # Set bake settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.bake_type = 'COMBINED'  # Or 'VERTEX_COLORS' if you want only the color lighting
    bpy.context.scene.cycles.samples = 64  # Adjust the number of samples as needed

    # Set the bake target to 'VERTEX_COLORS'
    bpy.context.scene.render.bake.target = 'VERTEX_COLORS'
    print("Bake target set to 'VERTEX_COLORS'.")

    # Select only the active object (mesh)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    # Execute the bake
    bpy.ops.object.bake(type='COMBINED')
    print("Bake completed.")

# Updated function to disconnect the "Image Texture" node in ALL materials of the active object
def disconnect_image_texture(self, context):
    obj = bpy.context.active_object
    if not obj:
        self.report({'WARNING'}, "No active object.")
        return
    if not obj.data.materials:
        self.report({'WARNING'}, "The selected object has no materials.")
        return

    for mat in obj.data.materials:
        if mat is None:
            continue
        if mat.use_nodes:
            node_tree = mat.node_tree
            image_texture_node = node_tree.nodes.get("Image Texture")
            if image_texture_node:
                # Create a list of links to remove to avoid modifying the collection during iteration
                links_to_remove = [link for link in node_tree.links if link.from_node == image_texture_node]
                for link in links_to_remove:
                    node_tree.links.remove(link)
                self.report({'INFO'}, f"'Image Texture' disconnected in material '{mat.name}'.")
            else:
                self.report({'WARNING'}, f"'Image Texture' node not found in material '{mat.name}'.")
        else:
            self.report({'WARNING'}, f"Material '{mat.name}' does not use nodes.")

# Updated function to connect the "Image Texture" node to the "Principled BSDF" node in ALL materials of the active object
def connect_image_texture(self, context):
    obj = bpy.context.active_object
    if not obj:
        self.report({'WARNING'}, "No active object.")
        return
    if not obj.data.materials:
        self.report({'WARNING'}, "The selected object has no materials.")
        return

    for mat in obj.data.materials:
        if mat is None:
            continue
        if mat.use_nodes:
            node_tree = mat.node_tree
            image_texture_node = node_tree.nodes.get("Image Texture")
            principled_node = node_tree.nodes.get("Principled BSDF")
            if image_texture_node and principled_node:
                # Optionally remove previous links from the "Base Color" socket
                for link in principled_node.inputs["Base Color"].links:
                    node_tree.links.remove(link)
                # Connect the "Color" output of the Image Texture node to the "Base Color" input of the Principled BSDF
                node_tree.links.new(image_texture_node.outputs["Color"], principled_node.inputs["Base Color"])
                self.report({'INFO'}, f"'Image Texture' connected in material '{mat.name}'.")
            else:
                self.report({'WARNING'}, f"Required nodes not found in material '{mat.name}'.")
        else:
            self.report({'WARNING'}, f"Material '{mat.name}' does not use nodes.")

# New operator to change the render engine to Eevee
class BackToEeveeOperator(bpy.types.Operator):
    """Operator to change from Cycles to Eevee"""
    bl_idname = "object.back_to_eevee"
    bl_label = "Back to Eevee"
    
    def execute(self, context):
        bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
        self.report({'INFO'}, "Render engine changed to Eevee")
        print("Render engine changed to Eevee.")
        return {'FINISHED'}

class VertexLightingPanel(bpy.types.Panel):
    """Custom panel to add and bake Vertex Colors lighting and to connect/disconnect texture nodes"""
    bl_label = "Vertex Lighting & Texture Nodes"
    bl_idname = "VIEW3D_PT_vertex_lighting_and_texture"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Vertex Lighting'

    def draw(self, context):
        layout = self.layout

        # Vertex Lighting section
        layout.label(text="Vertex Lighting:")
        layout.prop(context.scene, "light_type", text="Light Type")
        layout.operator("object.add_vertex_lighting", text="Add Vertex Lighting")
        layout.operator("object.bake_vertex_lighting", text="Bake Lighting")

        layout.separator()

        # Texture Node Control section
        layout.label(text="Texture Node Control:")
        layout.operator("node.disconnect_image_texture", text="Texture Off")
        layout.operator("node.connect_image_texture", text="Texture On")
        
        layout.separator()
        # Button to change from Cycles to Eevee
        layout.operator("object.back_to_eevee", text="Back to Eevee")

class AddVertexLightingOperator(bpy.types.Operator):
    """Operator to add the color attribute and the light"""
    bl_idname = "object.add_vertex_lighting"
    bl_label = "Add Vertex Lighting"

    def execute(self, context):
        light_type = context.scene.light_type
        add_vertex_lighting(light_type)
        return {'FINISHED'}

class BakeVertexLightingOperator(bpy.types.Operator):
    """Operator to bake the lighting into Vertex Colors"""
    bl_idname = "object.bake_vertex_lighting"
    bl_label = "Bake Lighting"

    def execute(self, context):
        bake_vertex_lighting()
        return {'FINISHED'}

class DisconnectImageTextureOperator(bpy.types.Operator):
    """Operator to temporarily disconnect texture nodes"""
    bl_idname = "node.disconnect_image_texture"
    bl_label = "Disconnect Image"
    
    def execute(self, context):
        disconnect_image_texture(self, context)
        return {'FINISHED'}

class ConnectImageTextureOperator(bpy.types.Operator):
    """Operator to connect the texture nodes"""
    bl_idname = "node.connect_image_texture"
    bl_label = "Connect Image"
    
    def execute(self, context):
        connect_image_texture(self, context)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(VertexLightingPanel)
    bpy.utils.register_class(AddVertexLightingOperator)
    bpy.utils.register_class(BakeVertexLightingOperator)
    bpy.utils.register_class(DisconnectImageTextureOperator)
    bpy.utils.register_class(ConnectImageTextureOperator)
    bpy.utils.register_class(BackToEeveeOperator)

    bpy.types.Scene.light_type = bpy.props.EnumProperty(
        name="Light Type",
        description="Choose the light type",
        items=[('SUN', "Sun", "Sunlight"),
               ('POINT', "Point", "Point light"),
               ('SPOT', "Spot", "Spotlight"),
               ('AREA', "Area", "Area light")],
        default='SUN'
    )

def unregister():
    bpy.utils.unregister_class(VertexLightingPanel)
    bpy.utils.unregister_class(AddVertexLightingOperator)
    bpy.utils.unregister_class(BakeVertexLightingOperator)
    bpy.utils.unregister_class(DisconnectImageTextureOperator)
    bpy.utils.unregister_class(ConnectImageTextureOperator)
    bpy.utils.unregister_class(BackToEeveeOperator)
    del bpy.types.Scene.light_type

if __name__ == "__main__":
    register()
