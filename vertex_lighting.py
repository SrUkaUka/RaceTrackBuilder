import bpy

def add_vertex_lighting(light_type='SUN'):
    # Obtener el objeto activo
    obj = bpy.context.object
    if obj is None or obj.type != 'MESH':
        print("Select a mesh object to continue.")
        return

    # Crear el atributo de color "Color" si no existe
    if "Color" not in obj.data.color_attributes:
        obj.data.color_attributes.new(name="Color", type='BYTE_COLOR', domain='CORNER')
        print("Color attribute 'Color' created with 'FACE CORNER' domain.")
    else:
        print("Color attribute 'Color' already exists.")

    # Crear la luz seleccionada si no existe ya en la escena
    if not any(o.type == 'LIGHT' and o.data.type == light_type for o in bpy.data.objects):
        bpy.ops.object.light_add(type=light_type, align='WORLD', location=(0, 0, 10))
        print(f"Light of type '{light_type}' created.")
    else:
        print(f"A light of type '{light_type}' already exists in the scene.")

    # Configurar Cycles como motor de render y tipo de bake
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.bake_type = 'COMBINED'
    print("Rendering engine set to Cycles.")

def bake_vertex_lighting():
    # Obtener el objeto activo
    obj = bpy.context.object
    if obj is None or obj.type != 'MESH':
        print("Select a mesh object to continue.")
        return

    # Asegurar que el atributo 'Color' esté activo
    if "Color" in obj.data.color_attributes:
        obj.data.color_attributes.active = obj.data.color_attributes["Color"]
        print("Color attribute 'Color' is active.")
    else:
        print("Color attribute 'Color' doesn't exist. Use 'Add Vertex Lighting' first.")
        return

    # Configurar ajustes para el bake
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.bake_type = 'COMBINED'  # O 'VERTEX_COLORS' si se quiere solo la iluminación de color
    bpy.context.scene.cycles.samples = 64  # Ajusta la cantidad de samples según se necesite
    
    # Establecer el target del bake a 'VERTEX_COLORS'
    bpy.context.scene.render.bake.target = 'VERTEX_COLORS'
    print("Bake target set to 'VERTEX_COLORS'.")

    # Seleccionar únicamente el objeto activo (malla)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    
    # Ejecutar el bake
    bpy.ops.object.bake(type='COMBINED')
    print("Bake completed.")

# Función actualizada para desconectar el nodo "Image Texture" en TODOS los materiales del objeto activo
def disconnect_image_texture(self, context):
    obj = bpy.context.active_object
    if not obj:
        self.report({'WARNING'}, "No hay objeto activo.")
        return
    if not obj.data.materials:
        self.report({'WARNING'}, "El objeto seleccionado no tiene materiales.")
        return

    for mat in obj.data.materials:
        if mat is None:
            continue
        if mat.use_nodes:
            node_tree = mat.node_tree
            image_texture_node = node_tree.nodes.get("Image Texture")
            if image_texture_node:
                # Crear lista de enlaces a remover para evitar modificar la colección durante la iteración
                links_to_remove = [link for link in node_tree.links if link.from_node == image_texture_node]
                for link in links_to_remove:
                    node_tree.links.remove(link)
                self.report({'INFO'}, f"Se desconectó 'Image Texture' en el material '{mat.name}'.")
            else:
                self.report({'WARNING'}, f"Nodo 'Image Texture' no encontrado en el material '{mat.name}'.")
        else:
            self.report({'WARNING'}, f"El material '{mat.name}' no usa nodos.")

# Función actualizada para conectar el nodo "Image Texture" al nodo "Principled BSDF" en TODOS los materiales del objeto activo
def connect_image_texture(self, context):
    obj = bpy.context.active_object
    if not obj:
        self.report({'WARNING'}, "No hay objeto activo.")
        return
    if not obj.data.materials:
        self.report({'WARNING'}, "El objeto seleccionado no tiene materiales.")
        return

    for mat in obj.data.materials:
        if mat is None:
            continue
        if mat.use_nodes:
            node_tree = mat.node_tree
            image_texture_node = node_tree.nodes.get("Image Texture")
            principled_node = node_tree.nodes.get("Principled BSDF")
            if image_texture_node and principled_node:
                # Opcional: remover enlaces previos en el socket "Base Color"
                for link in principled_node.inputs["Base Color"].links:
                    node_tree.links.remove(link)
                # Conectar el socket "Color" del nodo Image Texture al "Base Color" del Principled BSDF
                node_tree.links.new(image_texture_node.outputs["Color"], principled_node.inputs["Base Color"])
                self.report({'INFO'}, f"Se conectó 'Image Texture' en el material '{mat.name}'.")
            else:
                self.report({'WARNING'}, f"Nodos requeridos no encontrados en el material '{mat.name}'.")
        else:
            self.report({'WARNING'}, f"El material '{mat.name}' no usa nodos.")

class VertexLightingPanel(bpy.types.Panel):
    """Panel personalizado para agregar y hornear iluminación en Vertex Colors y conectar/desconectar nodos de textura"""
    bl_label = "Vertex Lighting & Texture Nodes"
    bl_idname = "VIEW3D_PT_vertex_lighting_and_texture"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Vertex Lighting'

    def draw(self, context):
        layout = self.layout

        # Sección de Vertex Lighting
        layout.label(text="Vertex Lighting:")
        layout.prop(context.scene, "light_type", text="Light Type")
        layout.operator("object.add_vertex_lighting", text="Add Vertex Lighting")
        layout.operator("object.bake_vertex_lighting", text="Bake Lighting")

        layout.separator()

        # Sección de Control de Nodos de Textura
        layout.label(text="Texture Node Control:")
        layout.operator("node.disconnect_image_texture", text="Texture Off")
        layout.operator("node.connect_image_texture", text="Texture On")

class AddVertexLightingOperator(bpy.types.Operator):
    """Operador para agregar el atributo de color y la luz"""
    bl_idname = "object.add_vertex_lighting"
    bl_label = "Add Vertex Lighting"

    def execute(self, context):
        light_type = context.scene.light_type
        add_vertex_lighting(light_type)
        return {'FINISHED'}

class BakeVertexLightingOperator(bpy.types.Operator):
    """Operador para hornear la iluminación en Vertex Colors"""
    bl_idname = "object.bake_vertex_lighting"
    bl_label = "Bake Lighting"

    def execute(self, context):
        bake_vertex_lighting()
        return {'FINISHED'}

class DisconnectImageTextureOperator(bpy.types.Operator):
    """Operador para desconectar nodos de textura temporalmente"""
    bl_idname = "node.disconnect_image_texture"
    bl_label = "Desconectar Imagen"
    
    def execute(self, context):
        disconnect_image_texture(self, context)
        return {'FINISHED'}

class ConnectImageTextureOperator(bpy.types.Operator):
    """Operador para conectar los nodos de textura"""
    bl_idname = "node.connect_image_texture"
    bl_label = "Conectar Imagen"
    
    def execute(self, context):
        connect_image_texture(self, context)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(VertexLightingPanel)
    bpy.utils.register_class(AddVertexLightingOperator)
    bpy.utils.register_class(BakeVertexLightingOperator)
    bpy.utils.register_class(DisconnectImageTextureOperator)
    bpy.utils.register_class(ConnectImageTextureOperator)

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
    del bpy.types.Scene.light_type

if __name__ == "__main__":
    register()
