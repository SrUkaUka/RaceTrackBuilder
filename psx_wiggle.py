import bpy
import bmesh
import random

# Variable global para controlar el temporizador
wiggle_timer = None
# Variable global para recordar el estado previo del wiggle
previous_wiggle_state = False

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
        if bpy.context.mode == 'OBJECT':
            for obj in scene.objects:
                ps1_wiggle(obj, intensity=scene.wiggle_intensity)
        return 1/30  # 30 FPS
    else:
        return None

def monitor_mode_change():
    """Monitorea el cambio de modo y gestiona la activación/desactivación del efecto."""
    global wiggle_timer, previous_wiggle_state
    scene = bpy.context.scene

    if bpy.context.mode != 'OBJECT':
        if scene.wiggle_enabled:
            previous_wiggle_state = True
            bpy.ops.object.mode_set(mode='OBJECT')
            for obj in scene.objects:
                restore_original_positions(obj)
            scene.wiggle_enabled = False
            if wiggle_timer is not None:
                bpy.app.timers.unregister(update_wiggle)
                wiggle_timer = None
            bpy.ops.object.mode_set(mode='EDIT')
    else:
        if previous_wiggle_state:
            scene.wiggle_enabled = True
            previous_wiggle_state = False
            if wiggle_timer is None:
                wiggle_timer = bpy.app.timers.register(update_wiggle)
    return 1/10  # Verifica cada 0.1 segundos

def check_geometry_integrity():
    """Compara la cantidad de vértices actuales con los originales.
    Retorna una lista de nombres de objetos que han cambiado."""
    warnings = []
    for obj_name, original_pos in original_vertices.items():
        obj = bpy.data.objects.get(obj_name)
        if obj is None or obj.type != 'MESH':
            warnings.append(f"{obj_name} (ausente o no mesh)")
        else:
            if len(obj.data.vertices) != len(original_pos):
                warnings.append(obj_name)
    return warnings

def geometry_update_handler(depsgraph):
    """Handler que se ejecuta en cada actualización de la escena para detectar cambios en la geometría."""
    scene = bpy.context.scene
    if scene.wiggle_enabled:
        warns = check_geometry_integrity()
        if warns:
            scene.wiggle_warning = "¡Advertencia! Objetos modificados: " + ", ".join(warns)
        else:
            scene.wiggle_warning = ""
    else:
        scene.wiggle_warning = ""

# Panel de interfaz en la barra lateral de Blender
class SimpleWigglePanel(bpy.types.Panel):
    bl_label = "PS1 Wiggle Effect"
    bl_idname = "OBJECT_PT_ps1_wiggle"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render PS1'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "wiggle_enabled", text="Enable PS1 Wiggle")
        layout.prop(scene, "wiggle_intensity", text="Wiggle Intensity", slider=True)
        
        # Si hay una advertencia, la mostramos dentro de un cuadro amarillo
        if scene.wiggle_warning:
            warning_box = layout.box()  # Crear un cuadro para destacar la advertencia
            warning_row = warning_box.row()
            warning_row.alert = True  # Activar estilo de alerta para el cuadro
            warning_row.label(text=scene.wiggle_warning, icon='ERROR')

def toggle_wiggle(self, context):
    """Activa o desactiva el temporizador y guarda/restaura posiciones según corresponda."""
    global wiggle_timer
    scene = context.scene

    if scene.wiggle_enabled:
        for obj in scene.objects:
            if obj.name not in original_vertices:
                save_original_positions(obj)
        if wiggle_timer is None:
            wiggle_timer = bpy.app.timers.register(update_wiggle)
        bpy.app.timers.register(monitor_mode_change)
    else:
        for obj in scene.objects:
            restore_original_positions(obj)
        if wiggle_timer is not None:
            bpy.app.timers.unregister(update_wiggle)
            wiggle_timer = None

def update_wiggle_intensity(self, context):
    """Forza la actualización al cambiar la intensidad."""
    if context.scene.wiggle_enabled:
        bpy.app.timers.unregister(update_wiggle)
        bpy.app.timers.register(update_wiggle)

def register():
    bpy.types.Scene.wiggle_enabled = bpy.props.BoolProperty(
        name="Enable PS1 Wiggle",
        default=False,
        update=toggle_wiggle
    )
    bpy.types.Scene.wiggle_intensity = bpy.props.FloatProperty(
        name="Wiggle Intensity",
        description="Ajusta la intensidad del efecto PS1 Wiggle",
        default=0.002,
        min=0.0001,
        max=0.02,
        precision=5,
        step=0.0001,
        update=update_wiggle_intensity
    )
    # Propiedad para mostrar mensajes de advertencia en la interfaz
    bpy.types.Scene.wiggle_warning = bpy.props.StringProperty(
        name="Wiggle Warning",
        default=""
    )
    bpy.utils.register_class(SimpleWigglePanel)
    # Registra el handler para monitorizar cambios en la geometría
    bpy.app.handlers.depsgraph_update_post.append(geometry_update_handler)

def unregister():
    global wiggle_timer
    if wiggle_timer is not None:
        bpy.app.timers.unregister(update_wiggle)
        wiggle_timer = None
    bpy.utils.unregister_class(SimpleWigglePanel)
    del bpy.types.Scene.wiggle_enabled
    del bpy.types.Scene.wiggle_intensity
    del bpy.types.Scene.wiggle_warning
    # Remueve el handler de actualización de geometría
    if geometry_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(geometry_update_handler)

if __name__ == "__main__":
    register()
