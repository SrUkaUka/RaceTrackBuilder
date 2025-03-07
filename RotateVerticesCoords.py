import bpy

# Diccionario global para almacenar listas de vértices por objeto
object_vertex_lists = {}

# Propiedad global para controlar el modo TriBlock (6 vértices) o QuadBlock (8 vértices)
bpy.types.Scene.use_quadblock = bpy.props.BoolProperty(
    name="QuadBlock",
    description="Usar 8 vértices (QuadBlock) en lugar de 6 (TriBlock)",
    default=False
)

def get_active_object():
    """Devuelve el objeto activo de la escena."""
    return bpy.context.object if bpy.context.object and bpy.context.object.type == 'MESH' else None

def get_vertex_list():
    """Obtiene la lista de vértices del objeto activo."""
    obj = get_active_object()
    if obj is None:
        return None
    return object_vertex_lists.setdefault(obj.name, [])

def add_selected_vertex():
    """Agrega manualmente un vértice seleccionado a la lista del objeto activo."""
    obj = get_active_object()
    if obj is None:
        return

    vertex_list = get_vertex_list()
    bpy.ops.object.mode_set(mode='OBJECT')  # Cambiar a modo objeto para acceder a vértices
    selected_verts = [v for v in obj.data.vertices if v.select]

    if len(selected_verts) != 1:
        return

    v = selected_verts[0]
    vertex_data = (v.index, v.co.copy())

    if vertex_data in vertex_list:
        return  # No permitir duplicados

    max_verts = 8 if bpy.context.scene.use_quadblock else 6
    if len(vertex_list) >= max_verts:
        return  

    vertex_list.append(vertex_data)
    bpy.ops.object.mode_set(mode='EDIT')  # Volver a edición
    bpy.context.area.tag_redraw()  # Refrescar UI

def rotate_indices(step):
    """Rota los índices de los vértices en la malla."""
    obj = get_active_object()
    if obj is None:
        return

    vertex_list = get_vertex_list()
    num_verts = len(vertex_list)
    expected_verts = 8 if bpy.context.scene.use_quadblock else 6

    if num_verts != expected_verts:
        print(f"❌ Debes tener exactamente {expected_verts} vértices en la lista.")
        return

    bpy.ops.object.mode_set(mode='OBJECT')  # Cambiar a modo objeto para modificar vértices

    original_indices = [v[0] for v in vertex_list]
    original_coords = [v[1] for v in vertex_list]

    # Rotación circular según el valor de 'step' (positivo o negativo)
    step = step % num_verts  # Asegura que la rotación es válida dentro del tamaño de la lista
    rotated_indices = original_indices[-step:] + original_indices[:-step]

    # Aplicar las nuevas coordenadas en la malla
    for new_index, old_coord in zip(rotated_indices, original_coords):
        obj.data.vertices[new_index].co = old_coord

    # Actualizar la lista con los nuevos índices
    object_vertex_lists[obj.name] = list(zip(rotated_indices, original_coords))

    bpy.ops.object.mode_set(mode='EDIT')  # Volver a edición
    bpy.context.area.tag_redraw()  # Refrescar UI

def clear_selected_list():
    """Limpia la lista de vértices seleccionados del objeto activo."""
    obj = get_active_object()
    if obj and obj.name in object_vertex_lists:
        object_vertex_lists[obj.name] = []
        bpy.context.area.tag_redraw()

def remove_last_vertex():
    """Elimina el último vértice agregado en el objeto activo."""
    vertex_list = get_vertex_list()
    if vertex_list:
        vertex_list.pop()
        bpy.context.area.tag_redraw()

# Interfaz en Blender
class OBJECT_PT_Rotate90(bpy.types.Panel):
    bl_label = "Rotar Índices"
    bl_idname = "OBJECT_PT_rotate_90"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Herramientas"

    def draw(self, context):
        layout = self.layout
        obj = get_active_object()
        vertex_list = get_vertex_list()

        if obj is None:
            layout.label(text="Selecciona un objeto de malla")
            return

        layout.label(text=f"Objeto: {obj.name}")

        # Checkbox para elegir entre TriBlock (6) y QuadBlock (8)
        layout.prop(context.scene, "use_quadblock", text="QuadBlock")

        # Botones principales
        row = layout.row()
        row.operator("object.add_selected_vertex", text="Agregar Vértice")

        row = layout.row()
        row.operator("object.rotate_indices_90", text="R90")
        row.operator("object.rotate_indices_neg90", text="R-90")

        # Mostrar lista de vértices
        layout.label(text="Lista de Vértices Seleccionados:")

        if vertex_list:
            for i, (index, coord) in enumerate(vertex_list):
                layout.label(text=f"{i+1}. Índice: {index} - {tuple(coord)}")

            layout.operator("object.remove_last_vertex", text="Eliminar Último")
            layout.operator("object.clear_selected_list", text="Borrar Todo")
        else:
            layout.label(text="(Lista Vacía)")

class OBJECT_OT_AddVertex(bpy.types.Operator):
    bl_idname = "object.add_selected_vertex"
    bl_label = "Agregar Vértice"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        add_selected_vertex()
        return {'FINISHED'}

class OBJECT_OT_Rotate90(bpy.types.Operator):
    bl_idname = "object.rotate_indices_90"
    bl_label = "R90"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rotate_indices(2)  # Rota dos posiciones abajo (horario)
        return {'FINISHED'}

class OBJECT_OT_RotateNeg90(bpy.types.Operator):
    bl_idname = "object.rotate_indices_neg90"
    bl_label = "R-90"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rotate_indices(-2)  # Rota dos posiciones arriba (antihorario)
        return {'FINISHED'}

class OBJECT_OT_ClearList(bpy.types.Operator):
    bl_idname = "object.clear_selected_list"
    bl_label = "Borrar Todo"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        clear_selected_list()
        return {'FINISHED'}

class OBJECT_OT_RemoveLast(bpy.types.Operator):
    bl_idname = "object.remove_last_vertex"
    bl_label = "Eliminar Último"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        remove_last_vertex()
        return {'FINISHED'}

# Registrar en Blender con atajo de teclado
addon_keymaps = []

def register():
    global addon_keymaps
    bpy.utils.register_class(OBJECT_PT_Rotate90)
    bpy.utils.register_class(OBJECT_OT_AddVertex)
    bpy.utils.register_class(OBJECT_OT_Rotate90)
    bpy.utils.register_class(OBJECT_OT_RotateNeg90)
    bpy.utils.register_class(OBJECT_OT_ClearList)
    bpy.utils.register_class(OBJECT_OT_RemoveLast)

    # Añadir atajo de teclado SHIFT + W
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="Mesh", space_type="EMPTY")
    kmi = km.keymap_items.new("object.add_selected_vertex", "W", "PRESS", shift=True)
    addon_keymaps.append((km, kmi))

def unregister():
    global addon_keymaps
    bpy.utils.unregister_class(OBJECT_PT_Rotate90)
    bpy.utils.unregister_class(OBJECT_OT_AddVertex)
    bpy.utils.unregister_class(OBJECT_OT_Rotate90)
    bpy.utils.unregister_class(OBJECT_OT_RotateNeg90)
    bpy.utils.unregister_class(OBJECT_OT_ClearList)
    bpy.utils.unregister_class(OBJECT_OT_RemoveLast)

    # Eliminar atajo de teclado
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
