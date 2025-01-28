import bpy

def add_vertex_lighting(light_type='SUN'):
    # Get the active object
    obj = bpy.context.object

    if obj is None or obj.type != 'MESH':
        print("Select a mesh object to continue.")
        return

    # Create a color attribute named "Color" if it doesn't exist
    if "Color" not in obj.data.color_attributes:
        obj.data.color_attributes.new(name="Color", type='BYTE_COLOR', domain='CORNER')
        print("Color attribute 'Color' created with 'FACE CORNER' domain.")
    else:
        print("Color attribute 'Color' already exists.")

    # Create the selected light if it doesn't exist
    if not any(obj.type == 'LIGHT' and obj.data.type == light_type for obj in bpy.data.objects):
        bpy.ops.object.light_add(type=light_type, align='WORLD', location=(0, 0, 10))
        print(f"Light of type '{light_type}' created.")
    else:
        print(f"A light of type '{light_type}' already exists in the scene.")

    # Set Cycles as the rendering engine
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.bake_type = 'COMBINED'
    print("Rendering engine set to Cycles.")

def bake_vertex_lighting():
    # Get the active object
    obj = bpy.context.object

    if obj is None or obj.type != 'MESH':
        print("Select a mesh object to continue.")
        return

    # Ensure the 'Color' attribute is active
    if "Color" in obj.data.color_attributes:
        obj.data.color_attributes.active = obj.data.color_attributes["Color"]
        print("Color attribute 'Color' is active.")
    else:
        print("Color attribute 'Color' doesn't exist. Use 'Add Vertex Lighting' first.")
        return

    # Set the bake settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.bake_type = 'COMBINED'  # Or 'VERTEX_COLORS' if you want only color lighting
    bpy.context.scene.cycles.samples = 64  # Adjust the number of samples as needed
    
    # Set the bake target to 'VERTEX_COLORS'
    bpy.context.scene.render.bake.target = 'VERTEX_COLORS'
    print("Bake target set to 'VERTEX_COLORS'.")

    # Ensure only the active mesh object is selected
    bpy.ops.object.select_all(action='DESELECT')  # Deselect all
    obj.select_set(True)  # Select the active object (mesh)
    
    # Perform the bake
    bpy.ops.object.bake(type='COMBINED')
    print("Bake completed.")

# Función para desconectar el nodo Image Texture
def disconnect_image_texture(self, context):
    # Obtener el material activo del objeto seleccionado
    obj = bpy.context.active_object
    if obj and obj.active_material:
        node_tree = obj.active_material.node_tree
        image_texture_node = node_tree.nodes.get("Image Texture")
        
        if image_texture_node:
            # Recorremos los enlaces y desconectamos cualquier enlace de salida del nodo de imagen
            for link in node_tree.links:
                if link.from_node == image_texture_node:
                    node_tree.links.remove(link)
            self.report({'INFO'}, "Image texture node disconnected")
        else:
            self.report({'WARNING'}, "Image texture node not found.")
    else:
        self.report({'WARNING'}, "Selected object does not have a material.")

# Función para conectar el nodo Image Texture a Principled BSDF
def connect_image_texture(self, context):
    # Obtener el material activo del objeto seleccionado
    obj = bpy.context.active_object
    if obj and obj.active_material:
        node_tree = obj.active_material.node_tree
        image_texture_node = node_tree.nodes.get("Image Texture")
        principled_node = node_tree.nodes.get("Principled BSDF")
        
        if image_texture_node and principled_node:
            # Aseguramos que los sockets estén bien definidos
            image_texture_socket = image_texture_node.outputs["Color"]
            principled_socket = principled_node.inputs["Base Color"]
            
            # Creamos el enlace
            node_tree.links.new(image_texture_socket, principled_socket)
            self.report({'INFO'}, "Image Texture connected.")
        else:
            self.report({'WARNING'}, "Disable PS1 Render mode first.")
    else:
        self.report({'WARNING'}, "Selected object does not have a material.")

class VertexLightingPanel(bpy.types.Panel):
    """Custom panel for adding and baking lighting in Vertex Colors and connecting/disconnecting image textures"""
    bl_label = "Vertex Lighting & Texture Nodes"
    bl_idname = "VIEW3D_PT_vertex_lighting_and_texture"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Vertex Lighting'

    def draw(self, context):
        layout = self.layout

        # Section for Vertex Lighting
        layout.label(text="Vertex Lighting:")
        layout.prop(context.scene, "light_type", text="Light Type")

        layout.operator("object.add_vertex_lighting", text="Add Vertex Lighting")
        layout.operator("object.bake_vertex_lighting", text="Bake Lighting")

        layout.separator()

        # Section for Texture Node Control
        layout.label(text="Texture Node Control:")
        layout.operator("node.disconnect_image_texture", text="Texture Off")
        layout.operator("node.connect_image_texture", text="Texture On")

class AddVertexLightingOperator(bpy.types.Operator):
    """Operator to add the color attribute and sun light"""
    bl_idname = "object.add_vertex_lighting"
    bl_label = "Add Vertex Lighting"

    def execute(self, context):
        light_type = context.scene.light_type
        add_vertex_lighting(light_type)
        return {'FINISHED'}

class BakeVertexLightingOperator(bpy.types.Operator):
    """Operator to bake lighting in Vertex Colors"""
    bl_idname = "object.bake_vertex_lighting"
    bl_label = "Bake Lighting"

    def execute(self, context):
        bake_vertex_lighting()
        return {'FINISHED'}

# Operador para desconectar
class DisconnectImageTextureOperator(bpy.types.Operator):
    """Operator to disable textures temoporaly"""
    bl_idname = "node.disconnect_image_texture"
    bl_label = "Desconectar Imagen"
    
    def execute(self, context):
        disconnect_image_texture(self, context)
        return {'FINISHED'}

# Operador para conectar
class ConnectImageTextureOperator(bpy.types.Operator):
    """Operator to enable textures"""
    bl_idname = "node.connect_image_texture"
    bl_label = "Conectar Imagen"
    
    def execute(self, context):
        connect_image_texture(self, context)
        return {'FINISHED'}

# Register the classes
def register():
    bpy.utils.register_class(VertexLightingPanel)
    bpy.utils.register_class(AddVertexLightingOperator)
    bpy.utils.register_class(BakeVertexLightingOperator)
    bpy.utils.register_class(DisconnectImageTextureOperator)
    bpy.utils.register_class(ConnectImageTextureOperator)

    # Register the enum to choose the light type
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

    # Remove the enum property when unregistering the addon
    del bpy.types.Scene.light_type

if __name__ == "__main__":
    register()
