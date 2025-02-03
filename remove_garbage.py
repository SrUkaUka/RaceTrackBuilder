import bpy
import bmesh

# Función para limpiar vértices y aristas flotantes
def clean_objects(context):
    # Recorrer todos los objetos en la escena
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':  # Solo objetos de tipo MESH
            # Aseguramos que el objeto esté en modo objeto para que funcione correctamente
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Crear un BMesh para acceder a la geometría
            bm = bmesh.from_edit_mesh(obj.data)
            
            # Eliminar vértices que no están conectados a ninguna arista
            for vert in bm.verts[:]:
                if len(vert.link_edges) == 0:  # El vértice no está conectado a ninguna arista
                    bm.verts.remove(vert)
            
            # Eliminar aristas flotantes (aristas que no están conectadas a caras)
            for edge in bm.edges[:]:
                if len(edge.link_faces) == 0:  # La arista no está conectada a ninguna cara
                    bm.edges.remove(edge)

            # Actualizamos la malla
            bmesh.update_edit_mesh(obj.data)
            
            # Volver a modo objeto para hacer otras modificaciones si es necesario
            bpy.ops.object.mode_set(mode='OBJECT')

            # Después de limpiar en modo edición, revisar si el objeto está vacío
            if is_empty_or_floating(obj):
                bpy.data.objects.remove(obj, do_unlink=True)  # Elimina el objeto si está vacío

# Función que verifica si un objeto está vacío o sólo tiene geometría flotante
def is_empty_or_floating(obj):
    mesh = obj.data

    # Verificamos si el objeto tiene geometría válida (vértices, aristas y caras)
    if len(mesh.vertices) == 0 or len(mesh.edges) == 0 or len(mesh.polygons) == 0:
        return True

    # Verificamos si el objeto solo tiene vértices o aristas flotantes sin caras
    if len(mesh.polygons) == 0:  # Si no tiene caras
        if len(mesh.vertices) == 0 or len(mesh.edges) == 0:  # Si no tiene vértices ni aristas
            return True

        # Verificar si todas las aristas están flotantes (sin caras)
        for edge in mesh.edges:
            if len(edge.link_faces) == 0:  # Arista sin caras
                return True

        # Verificar si todos los vértices están flotantes (sin aristas)
        for vert in mesh.vertices:
            if len(vert.link_edges) == 0:  # Vértice sin aristas
                return True

    return False  # El objeto tiene geometría válida (caras o aristas conectadas)

# Clase del Panel
class OBJECT_PT_clean_objects(bpy.types.Panel):
    bl_label = "Clean Objects"
    bl_idname = "OBJECT_PT_clean_objects"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    
    def draw(self, context):
        layout = self.layout
        layout.operator("object.clean_objects", text="Clean All Objects")

# Operador para ejecutar la limpieza
class OBJECT_OT_clean_objects(bpy.types.Operator):
    bl_idname = "object.clean_objects"
    bl_label = "Clean Floating Objects"
    
    def execute(self, context):
        clean_objects(context)
        return {'FINISHED'}

# Registro de las clases
def register():
    bpy.utils.register_class(OBJECT_OT_clean_objects)
    bpy.utils.register_class(OBJECT_PT_clean_objects)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_clean_objects)
    bpy.utils.unregister_class(OBJECT_PT_clean_objects)

if __name__ == "__main__":
    register()
