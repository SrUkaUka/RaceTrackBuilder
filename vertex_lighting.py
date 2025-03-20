import bpy

def add_vertex_lighting(light_type='SUN'):
    obj = bpy.context.object
    if obj is None or obj.type != 'MESH':
        print("Select a mesh object to continue.")
        return

    if "Attribute" not in obj.data.color_attributes:
        obj.data.color_attributes.new(name="Attribute", type='BYTE_COLOR', domain='CORNER')
        print("Color attribute 'Attribute' created with 'FACE CORNER' domain.")
    else:
        print("Color attribute 'Attribute' already exists.")

    bpy.ops.object.light_add(type=light_type, align='WORLD', location=(0, 0, 10))
    print(f"Light of type '{light_type}' created.")

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.bake_type = 'COMBINED'
    print("Rendering engine set to Cycles.")

def bake_vertex_lighting():
    obj = bpy.context.object
    if obj is None or obj.type != 'MESH':
        print("Select a mesh object to continue.")
        return

    if "Attribute" in obj.data.color_attributes:
        obj.data.color_attributes.active = obj.data.color_attributes["Attribute"]
        print("Color attribute 'Attribute' is active.")
    else:
        print("Color attribute 'Attribute' doesn't exist. Use 'Add Vertex Lighting' first.")
        return

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.bake_type = 'COMBINED'
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.render.bake.target = 'VERTEX_COLORS'
    print("Bake target set to 'VERTEX_COLORS'.")

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.bake(type='COMBINED')
    print("Bake completed.")

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
                links_to_remove = [link for link in node_tree.links if link.from_node == image_texture_node]
                for link in links_to_remove:
                    node_tree.links.remove(link)
                self.report({'INFO'}, f"'Image Texture' disconnected in material '{mat.name}'.")
            else:
                self.report({'WARNING'}, f"'Image Texture' node not found in material '{mat.name}'.")
        else:
            self.report({'WARNING'}, f"Material '{mat.name}' does not use nodes.")

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
                for link in principled_node.inputs["Base Color"].links:
                    node_tree.links.remove(link)
                node_tree.links.new(image_texture_node.outputs["Color"], principled_node.inputs["Base Color"])
                self.report({'INFO'}, f"'Image Texture' connected in material '{mat.name}'.")
            else:
                self.report({'WARNING'}, f"Required nodes not found in material '{mat.name}'.")
        else:
            self.report({'WARNING'}, f"Material '{mat.name}' does not use nodes.")

class BackToEeveeOperator(bpy.types.Operator):
    """Operator to change from Cycles to Eevee"""
    bl_idname = "object.back_to_eevee"
    bl_label = "Back to Eevee"
    
    def execute(self, context):
        bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
        self.report({'INFO'}, "Render engine changed to Eevee")
        print("Render engine changed to Eevee.")
        return {'FINISHED'}

# Funciones de actualización para Transmission usando los índices 26 y 27
def update_transmission_color(self, context):
    obj = context.active_object
    if obj and obj.data and obj.data.materials:
        for mat in obj.data.materials:
            if mat and mat.use_nodes:
                node_tree = mat.node_tree
                principled = node_tree.nodes.get("Principled BSDF")
                if principled and len(principled.inputs) > 26:
                    # Se asigna el valor con alfa fijo en 1.0
                    principled.inputs[26].default_value = (*context.scene.transmission_color, 1.0)
    return None

def update_transmission_strength(self, context):
    obj = context.active_object
    if obj and obj.data and obj.data.materials:
        for mat in obj.data.materials:
            if mat and mat.use_nodes:
                node_tree = mat.node_tree
                principled = node_tree.nodes.get("Principled BSDF")
                if principled and len(principled.inputs) > 27:
                    principled.inputs[27].default_value = context.scene.transmission_strength
    return None

class VertexLightingPanel(bpy.types.Panel):
    """Panel to control Vertex Lighting, Texture Nodes, and Transmission Settings"""
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

        # Sección de control de nodos de textura
        layout.label(text="Texture Node Control:")
        layout.operator("node.disconnect_image_texture", text="Texture Off")
        layout.operator("node.connect_image_texture", text="Texture On")
        
        layout.separator()
        # Sección de Transmission
        layout.label(text="Transmission Settings:")
        layout.prop(context.scene, "transmission_color", text="Color")
        layout.prop(context.scene, "transmission_strength", text="Strength")
        # Con los callbacks, al cambiar se actualiza dinámicamente

        layout.separator()
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
    """Operator to disconnect texture nodes"""
    bl_idname = "node.disconnect_image_texture"
    bl_label = "Disconnect Image"
    
    def execute(self, context):
        disconnect_image_texture(self, context)
        return {'FINISHED'}

class ConnectImageTextureOperator(bpy.types.Operator):
    """Operator to connect texture nodes"""
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
    bpy.types.Scene.transmission_color = bpy.props.FloatVectorProperty(
        name="Transmission Color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0, max=1.0,
        description="Transmission color",
        update=update_transmission_color
    )
    bpy.types.Scene.transmission_strength = bpy.props.FloatProperty(
        name="Transmission Strength",
        default=1.0,
        min=0.0,
        description="Transmission strength",
        update=update_transmission_strength
    )

def unregister():
    bpy.utils.unregister_class(VertexLightingPanel)
    bpy.utils.unregister_class(AddVertexLightingOperator)
    bpy.utils.unregister_class(BakeVertexLightingOperator)
    bpy.utils.unregister_class(DisconnectImageTextureOperator)
    bpy.utils.unregister_class(ConnectImageTextureOperator)
    bpy.utils.unregister_class(BackToEeveeOperator)
    del bpy.types.Scene.light_type
    del bpy.types.Scene.transmission_color
    del bpy.types.Scene.transmission_strength

if __name__ == "__main__":
    register()
