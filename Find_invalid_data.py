import bpy
import bmesh
from mathutils import Vector

# Función para extruir los vértices seleccionados sin moverlos
def extrude_vertices(obj):
    # Cambiar a Modo de Edición
    bpy.ops.object.mode_set(mode='EDIT')

    # Seleccionar todos los vértices
    bpy.ops.mesh.select_all(action='SELECT')

    # Extruir los vértices pero manteniéndolos en la misma posición
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, 0)})

    # Volver al Modo de Objeto
    bpy.ops.object.mode_set(mode='OBJECT')

# Función para separar los vértices extruidos por selección
def separate_by_selection(obj):
    # Cambiar a Modo de Edición
    bpy.ops.object.mode_set(mode='EDIT')

    # Seleccionar todos los vértices
    bpy.ops.mesh.select_all(action='SELECT')

    # Separar por selección
    bpy.ops.mesh.separate(type='SELECTED')

    # Volver al Modo de Objeto
    bpy.ops.object.mode_set(mode='OBJECT')

# Función para unir dos objetos
def join_objects(obj1, obj2):
    # Renombrar objetos antes de unir para evitar duplicación de sufijos
    base_name1 = obj1.name.split(".")[0]  # Tomar el nombre base sin sufijos
    base_name2 = obj2.name.split(".")[0]

    rename_object(obj1, base_name1)
    rename_object(obj2, base_name2)

    # Establecer el objeto activo
    bpy.context.view_layer.objects.active = obj1

    # Seleccionar ambos objetos
    obj1.select_set(True)
    obj2.select_set(True)

    # Unir los objetos
    bpy.ops.object.join()

# Función para renombrar objetos sin duplicar sufijos
def rename_object(obj, base_name):
    """
    Renombra un objeto asegurándose de que no se dupliquen los sufijos.
    """
    if base_name in obj.name:
        new_name = base_name
    else:
        new_name = base_name
    obj.name = new_name

# Función para crear una cara y subdividir la geometría
def fill_and_subdivide(obj):
    # Cambiar a Modo de Edición
    bpy.ops.object.mode_set(mode='EDIT')

    # Seleccionar todos los vértices
    bpy.ops.mesh.select_all(action='SELECT')

    # Llenar los vértices seleccionados (creando una cara)
    bpy.ops.mesh.face_make_planar()

    # Volver al Modo de Objeto
    bpy.ops.object.mode_set(mode='OBJECT')

    # Subdividir el objeto
    subdivide_new_object(obj)

# Función para subdividir solo el objeto recién creado
def subdivide_new_object(new_obj):
    # Asegurarse de estar en Modo Objeto antes de las operaciones
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Deseleccionar todos los objetos
    bpy.ops.object.select_all(action='DESELECT')

    # Seleccionar y activar el nuevo objeto creado
    new_obj.select_set(True)
    bpy.context.view_layer.objects.active = new_obj

    # Cambiar a Modo de Edición y subdividir
    bpy.ops.object.mode_set(mode='EDIT')  # Entrar en Modo de Edición
    bpy.ops.mesh.select_all(action='SELECT')  # Seleccionar toda la geometría
    bpy.ops.mesh.subdivide(number_cuts=1)  # Subdividir
    bpy.ops.object.mode_set(mode='OBJECT')  # Volver al Modo de Objeto

# Función para obtener las coordenadas de los vértices seleccionados
def get_selected_vertices():
    """
    Recupera las coordenadas mundiales de los vértices seleccionados en Modo de Edición.

    Returns:
        list of Vector: Las coordenadas mundiales de los vértices seleccionados.
    """
    selected_verts = []
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH' and obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
            selected_verts.extend([obj.matrix_world @ v.co for v in bm.verts if v.select])
    return selected_verts

# Operador para el proceso de extrusión
class OBJECT_OT_ExtrudeAndSubdivide(bpy.types.Operator):
    """
    Extruye los vértices seleccionados, separa, une los objetos y crea una cara con subdivisión.
    """
    bl_idname = "mesh.extrude_and_subdivide"
    bl_label = "Extruir y Subdividir"

    def execute(self, context):
        # Obtener los vértices seleccionados
        selected_verts = get_selected_vertices()
        
        # Asegurarse de tener exactamente 3 o 4 vértices seleccionados
        if len(selected_verts) == 3 or len(selected_verts) == 4:
            # Extruir los vértices seleccionados
            extrude_vertices(context.active_object)

            # Separar los vértices extruidos
            separate_by_selection(context.active_object)

            # Obtener los nuevos objetos creados después de la separación
            obj1 = context.active_object
            obj2 = bpy.context.view_layer.objects.active

            # Unir los dos objetos
            join_objects(obj1, obj2)

            # Crear una cara y subdividir la geometría
            fill_and_subdivide(obj1)

            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Selecciona exactamente 3 o 4 vértices.")
            return {'CANCELLED'}

# Panel para los botones en la pestaña "Tools"
class VIEW3D_PT_InsertShapesPanel(bpy.types.Panel):
    """
    Panel de UI para insertar formas en el viewport 3D.
    """
    bl_label = "Extruir y Subdividir"
    bl_idname = "VIEW3D_PT_extrude_subdivide"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.extrude_and_subdivide")

# Registro de operadores y panel
def register():
    bpy.utils.register_class(OBJECT_OT_ExtrudeAndSubdivide)
    bpy.utils.register_class(VIEW3D_PT_InsertShapesPanel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_ExtrudeAndSubdivide)
    bpy.utils.unregister_class(VIEW3D_PT_InsertShapesPanel)

if __name__ == "__main__":
    register()
