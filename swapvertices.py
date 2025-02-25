import bpy

# Función para intercambiar las posiciones de los vértices seleccionados
def swap_vertex_positions(self, context):
    # Verificar si estamos en Modo Edición
    if bpy.context.object.mode != 'EDIT':
        self.report({'WARNING'}, "Debes estar en Modo Edición.")
        return
    
    # Cambiar a Modo Objeto temporalmente para modificar las coordenadas
    bpy.ops.object.mode_set(mode='OBJECT')

    # Obtener los vértices seleccionados
    selected_vertices = [v for v in bpy.context.active_object.data.vertices if v.select]
    
    # Verificar que haya exactamente tres vértices seleccionados
    if len(selected_vertices) == 3:
        # Ordenar los vértices según su posición en el espacio (en el eje X, Y o Z, dependiendo del caso)
        selected_vertices.sort(key=lambda v: v.co.x)  # Aquí estamos ordenando por el eje X, pero puedes cambiarlo si lo necesitas
        
        # El vértice medio será el del medio en la lista ordenada
        middle_vertex = selected_vertices[1]
        
        # Intercambiar las posiciones de los vértices adyacentes (el primero y el tercero)
        selected_vertices[0].co, selected_vertices[2].co = selected_vertices[2].co.copy(), selected_vertices[0].co.copy()
    else:
        self.report({'WARNING'}, "Por favor selecciona exactamente tres vértices.")
    
    # Volver a Modo Edición
    bpy.ops.object.mode_set(mode='EDIT')

# Operador que se ejecuta al presionar el botón
class OBJECT_OT_mirror_operator(bpy.types.Operator):
    bl_idname = "object.mirror_operator"
    bl_label = "Swap Adjacents Vertices"
    
    def execute(self, context):
        swap_vertex_positions(self, context)
        return {'FINISHED'}

# Panel con el botón en la pestaña de herramientas
class OBJECT_PT_mirror_panel(bpy.types.Panel):
    bl_label = "Mirror Vertices"
    bl_idname = "OBJECT_PT_mirror_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    
    def draw(self, context):
        layout = self.layout
        
        # Botón para ejecutar el intercambio de vértices
        layout.operator("object.mirror_operator")

# Registro de las clases
def register():
    bpy.utils.register_class(OBJECT_OT_mirror_operator)
    bpy.utils.register_class(OBJECT_PT_mirror_panel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_mirror_operator)
    bpy.utils.unregister_class(OBJECT_PT_mirror_panel)

if __name__ == "__main__":
    register()
