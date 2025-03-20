import bpy

# Nombre del objeto
CUBE_NAME = "Range"

# Propiedad booleana para el checkmark en Tool
bpy.types.Scene.toggle_box = bpy.props.BoolProperty(name="Toggle Box", default=False)

def create_wireframe_cube():
    """Crea un cubo hecho solo de aristas sin caras."""
    # Verificar si el cubo ya existe
    if CUBE_NAME in bpy.data.objects:
        return  

    # Crear una nueva malla y un objeto vacío
    mesh = bpy.data.meshes.new(CUBE_NAME)
    obj = bpy.data.objects.new(CUBE_NAME, mesh)
    bpy.context.collection.objects.link(obj)

    # Definir los vértices del cubo con sus dimensiones
    size_x, size_y, size_z = 930, 980, 860
    verts = [
        (-size_x / 2, -size_y / 2, -size_z / 2),  # 0
        (size_x / 2, -size_y / 2, -size_z / 2),   # 1
        (size_x / 2, size_y / 2, -size_z / 2),    # 2
        (-size_x / 2, size_y / 2, -size_z / 2),   # 3
        (-size_x / 2, -size_y / 2, size_z / 2),   # 4
        (size_x / 2, -size_y / 2, size_z / 2),    # 5
        (size_x / 2, size_y / 2, size_z / 2),     # 6
        (-size_x / 2, size_y / 2, size_z / 2),    # 7
    ]

    # Definir las aristas conectando los vértices
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # Base inferior
        (4, 5), (5, 6), (6, 7), (7, 4),  # Base superior
        (0, 4), (1, 5), (2, 6), (3, 7)   # Aristas verticales
    ]

    # Aplicar geometría al mesh
    mesh.from_pydata(verts, edges, [])
    mesh.update()

    # Ubicar el cubo en Z = -3.84012
    obj.location = (0, 0, -3.84012)

    # Crear un material rojo para las aristas
    material = bpy.data.materials.get("RedWire")
    if material is None:
        material = bpy.data.materials.new(name="RedWire")
        material.use_nodes = True
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (1, 0, 0, 1)  # Rojo

    obj.data.materials.append(material)

    # Mostrar aristas correctamente
    obj.display_type = 'WIRE'  # Ahora se verá siempre en wireframe

def adjust_camera():
    """Ajusta el clip_end de la vista 3D a 9000"""
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':  # Buscar la vista 3D
            for space in area.spaces:
                if space.type == 'VIEW_3D':  # Asegurar que es un espacio 3D
                    space.clip_end = 9000  # Aplicar el cambio
                    break

def toggle_cube(self, context):
    """Función para mostrar u ocultar el cubo con el checkmark"""
    cube = bpy.data.objects.get(CUBE_NAME)

    if not cube:
        create_wireframe_cube()
        cube = bpy.data.objects.get(CUBE_NAME)

    cube.hide_viewport = not context.scene.toggle_box
    cube.hide_render = cube.hide_viewport

    # Ajustamos la cámara cuando el cubo se muestra
    if context.scene.toggle_box:
        adjust_camera()

# Crear un panel en la pestaña "Tool"
class ToggleBoxPanel(bpy.types.Panel):
    bl_label = "Toggle Box"
    bl_idname = "OBJECT_PT_toggle_box"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"  # Pestaña Tool en el panel N

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "toggle_box")  # Agregar checkmark

# Registrar clases en Blender
def register():
    bpy.utils.register_class(ToggleBoxPanel)
    bpy.types.Scene.toggle_box = bpy.props.BoolProperty(
        name="Toggle Box", default=False, update=toggle_cube
    )

def unregister():
    bpy.utils.unregister_class(ToggleBoxPanel)
    del bpy.types.Scene.toggle_box

if __name__ == "__main__":
    register()
