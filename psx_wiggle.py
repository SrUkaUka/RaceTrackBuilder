import bpy
import bmesh
import random

# Variable global para controlar el temporizador
wiggle_timer = None

# Diccionario para guardar las posiciones originales de los vértices
original_vertices = {}

def quantize(value, step=1/16):
    """Cuantiza un valor a un paso fijo, simulando precisión de PS1."""
    return round(value / step) * step

def save_original_positions(obj):
    """Guarda la posición original de los vértices de un objeto."""
    if obj.type != 'MESH':
        return

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    original_vertices[obj.name] = [(vert.co.x, vert.co.y, vert.co.z) for vert in bm.verts]
    
    bm.free()

def restore_original_positions(obj):
    """Restaura la posición original de los vértices de un objeto."""
    if obj.type != 'MESH' or obj.name not in original_vertices:
        return

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    for vert, original_pos in zip(bm.verts, original_vertices[obj.name]):
        vert.co.x, vert.co.y, vert.co.z = original_pos

    bm.to_mesh(mesh)
    bm.free()

def ps1_wiggle(obj, step=1/16, intensity=0.002):
    """Aplica el efecto de 'wiggle' dinámico a los vértices."""
    if obj.type != 'MESH':
        return

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    for vert in bm.verts:
        vert.co.x = quantize(vert.co.x, step) + random.uniform(-intensity, intensity)
        vert.co.y = quantize(vert.co.y, step) + random.uniform(-intensity, intensity)
        vert.co.z = quantize(vert.co.z, step) + random.uniform(-intensity, intensity)

    bm.to_mesh(mesh)
    bm.free()

def update_wiggle():
    """Actualiza el wiggle constantemente si está activado."""
    scene = bpy.context.scene
    if scene.wiggle_enabled:
        for obj in scene.objects:
            ps1_wiggle(obj, intensity=scene.wiggle_intensity)
        return 1/30  # Mantiene el temporizador activo (30 FPS)
    else:
        return None  # Detiene el temporizador cuando el wiggle está desactivado

# Panel de interfaz en la barra lateral de Blender
class SimpleWigglePanel(bpy.types.Panel):
    bl_label = "PS1 Wiggle Effect"
    bl_idname = "OBJECT_PT_ps1_wiggle"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'PS1 Tools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Checkbox para activar/desactivar el wiggle
        layout.prop(scene, "wiggle_enabled", text="Enable PS1 Wiggle")
        
        # Deslizador para controlar la intensidad del temblor
        layout.prop(scene, "wiggle_intensity", text="Wiggle Intensity", slider=True)

# Función para activar/desactivar el temporizador correctamente
def toggle_wiggle(self, context):
    global wiggle_timer

    if context.scene.wiggle_enabled:
        # Guardamos la posición original de los objetos la primera vez que se activa
        for obj in context.scene.objects:
            if obj.name not in original_vertices:
                save_original_positions(obj)

        # Inicia el temporizador
        if wiggle_timer is None:
            wiggle_timer = bpy.app.timers.register(update_wiggle)
    else:
        # Restaura las posiciones originales cuando se desactiva
        for obj in context.scene.objects:
            restore_original_positions(obj)

        # Detiene el temporizador
        if wiggle_timer is not None:
            bpy.app.timers.unregister(update_wiggle)
            wiggle_timer = None

# Función para actualizar el wiggle en tiempo real al cambiar la intensidad
def update_wiggle_intensity(self, context):
    """Forza una actualización cuando se cambia la intensidad."""
    if context.scene.wiggle_enabled:
        bpy.app.timers.unregister(update_wiggle)  # Detiene el temporizador temporalmente
        bpy.app.timers.register(update_wiggle)  # Lo reinicia para que el cambio se note

# Registrar propiedades y panel
def register():
    bpy.types.Scene.wiggle_enabled = bpy.props.BoolProperty(
        name="Enable PS1 Wiggle", 
        default=False,
        update=toggle_wiggle
    )
    
    bpy.types.Scene.wiggle_intensity = bpy.props.FloatProperty(
        name="Wiggle Intensity",
        description="Adjust the intensity of the PS1 wiggle effect",
        default=0.002,
        min=0.0001,
        max=0.02,
        precision=5,  # Asegura que los valores pequeños sean reconocidos
        step=0.0001,   # Cambios suaves en el deslizador
        update=update_wiggle_intensity  # Llama a la función al cambiar el valor
    )

    bpy.utils.register_class(SimpleWigglePanel)

def unregister():
    global wiggle_timer

    if wiggle_timer is not None:
        bpy.app.timers.unregister(update_wiggle)
        wiggle_timer = None

    bpy.utils.unregister_class(SimpleWigglePanel)
    del bpy.types.Scene.wiggle_enabled
    del bpy.types.Scene.wiggle_intensity

# Activar el script
if __name__ == "__main__":
    register()
