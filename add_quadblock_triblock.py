import bpy
import bmesh

def get_new_objects(before_objects):
    """Devuelve una lista de los nuevos objetos creados tras la separación."""
    return [obj for obj in bpy.context.scene.objects if obj not in before_objects and obj.type == 'MESH']

def clean_object(obj):
    """Limpia los vértices y aristas flotantes del objeto."""
    if obj.type != 'MESH':
        return

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(obj.data)

    # Eliminar aristas sin caras
    for edge in bm.edges[:]:
        if len(edge.link_faces) == 0:
            bm.edges.remove(edge)

    # Eliminar vértices sin conexiones
    for vert in bm.verts[:]:
        if len(vert.link_edges) == 0:
            bm.verts.remove(vert)

    bmesh.update_edit_mesh(obj.data)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Si el objeto quedó vacío, eliminarlo
    if len(obj.data.vertices) == 0:
        bpy.data.objects.remove(obj, do_unlink=True)

def insert_block(context, required_verts):
    selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

    if not selected_objects:
        return {'CANCELLED'}

    selected_verts = []
    for obj in selected_objects:
        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
            selected_verts.extend([v for v in bm.verts if v.select])

    if len(selected_verts) != required_verts:
        return {'CANCELLED'}

    # Guardar los objetos antes de la separación
    before_objects = set(bpy.context.scene.objects)

    # Extruir los vértices en la misma posición
    bpy.ops.mesh.extrude_vertices_move(TRANSFORM_OT_translate={"value": (0, 0, 0)})

    # Separar por selección
    bpy.ops.mesh.separate(type='SELECTED')

    # Limpiar los objetos originales para eliminar restos flotantes
    for obj in selected_objects:
        clean_object(obj)

    # Asegurarse de que hay un objeto activo y seleccionado
    if not bpy.context.view_layer.objects.active:
        bpy.context.view_layer.objects.active = selected_objects[0]

    # Salir de Modo Edición para poder unir los objetos
    bpy.ops.object.mode_set(mode='OBJECT')

    # Forzar actualización
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.update()

    # Detectar los nuevos objetos creados
    new_objects = get_new_objects(before_objects)

    if not new_objects:
        return {'CANCELLED'}

    # Seleccionar solo los objetos recién creados y unirlos
    for obj in new_objects:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

    if len(new_objects) > 1:
        bpy.ops.object.join()

    # Obtener el objeto resultante después de la unión
    final_object = bpy.context.object

    if not final_object:
        return {'CANCELLED'}

    # Entrar en modo edición para seleccionar vértices y rellenar con "F"
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.edge_face_add()

    # Subdividir el objeto
    bpy.ops.mesh.subdivide()

    # Volver a Modo Objeto
    bpy.ops.object.mode_set(mode='OBJECT')

    # Limpiar la geometría sobrante en el objeto final
    clean_object(final_object)

    return {'FINISHED'}

class MESH_OT_insert_quadblock(bpy.types.Operator):
    bl_idname = "mesh.insert_quadblock"
    bl_label = "Insert Quadblock"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        result = insert_block(context, 4)
        if result == {'CANCELLED'}:
            self.report({'WARNING'}, "You must select exactly 4 vertices for a Quadblock.")
        return result

class MESH_OT_insert_triblock(bpy.types.Operator):
    bl_idname = "mesh.insert_triblock"
    bl_label = "Insert Triblock"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        result = insert_block(context, 3)
        if result == {'CANCELLED'}:
            self.report({'WARNING'}, "You must select exactly 3 vertices for a Triblock.")
        return result

class VIEW3D_PT_quadtriblock_panel(bpy.types.Panel):
    bl_label = "Quadblock & Triblock"
    bl_idname = "VIEW3D_PT_quadtriblock_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.insert_quadblock")
        layout.operator("mesh.insert_triblock")

def register():
    bpy.utils.register_class(MESH_OT_insert_quadblock)
    bpy.utils.register_class(MESH_OT_insert_triblock)
    bpy.utils.register_class(VIEW3D_PT_quadtriblock_panel)

def unregister():
    bpy.utils.unregister_class(MESH_OT_insert_quadblock)
    bpy.utils.unregister_class(MESH_OT_insert_triblock)
    bpy.utils.unregister_class(VIEW3D_PT_quadtriblock_panel)

if __name__ == "__main__":
    register()
