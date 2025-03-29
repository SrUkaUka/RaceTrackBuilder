import bpy
import os
import math
import colorsys
import bmesh

# ====================================================
# CONSTANTES DE OFFSETS (modificables desde el código)
# ====================================================
# Offsets para el modo "driver"
DRIVER_CUBE_Z_OFFSET   = 4.1
DRIVER_CAMERA_Z_OFFSET = -0.3
DRIVER_CUBE_Y_OFFSET   = 0.0
DRIVER_CAMERA_SCALE    = 0.5
DRIVER_CUBE_X_OFFSET   = -4.8
DRIVER_CAMERA_X_OFFSET = 5.1
DRIVER_CAMERA_Y_OFFSET = 0.0
DRIVER_CUBE_SCALE      = 2.0

# Offsets para el modo "import"
IMPORT_CUBE_Z_OFFSET   = 2.3
IMPORT_CAMERA_Z_OFFSET = -0.2
IMPORT_CUBE_Y_OFFSET   = 0.0
IMPORT_CAMERA_SCALE    = 0.5
IMPORT_CUBE_X_OFFSET   = -2.5
IMPORT_CAMERA_X_OFFSET = 2.8
IMPORT_CAMERA_Y_OFFSET = 0.0
IMPORT_CUBE_SCALE      = 1.0

# ====================================================
# FUNCIONES AUXILIARES Y DE UTILIDAD
# ====================================================
def get_next_name(base_name):
    existing_names = {obj.name for obj in bpy.data.objects}
    index = 0
    new_name = f"{base_name}{index:02d}"
    while new_name in existing_names:
        index += 1
        new_name = f"{base_name}{index:02d}"
    return new_name

def get_next_driver_suffix():
    indices = []
    for obj in bpy.data.objects:
        if obj.name.endswith("_driver00") or "_driver" in obj.name:
            parts = obj.name.split("_driver")
            if len(parts) > 1 and parts[-1].isdigit():
                try:
                    indices.append(int(parts[-1]))
                except ValueError:
                    pass
    next_index = 0 if not indices else max(indices) + 1
    return f"_driver{str(next_index).zfill(2)}"

# ====================================================
# CONFIGURACIÓN DE SNAP
# ====================================================
def toggle_snap(self, context):
    tool_settings = bpy.context.scene.tool_settings
    if self.enable_snap:
        tool_settings.use_snap = True
        tool_settings.snap_elements = {'FACE'}
        tool_settings.snap_elements_individual = {'FACE_PROJECT'}
    else:
        tool_settings.use_snap = False
        tool_settings.snap_elements = {'INCREMENT'}
        tool_settings.snap_elements_individual.clear()

class ImportProperties(bpy.types.PropertyGroup):
    enable_snap: bpy.props.BoolProperty(
        name="Enable Snap",
        description="Toggle Snap Face & Face Project",
        default=False,
        update=toggle_snap
    )

# ====================================================
# CREACIÓN DE LA CÁMARA Y EL CUBO
# ====================================================
def create_camera_with_cube(target_object, mode='driver'):
    object_location = target_object.location

    # Definir offsets y escala según el modo
    if mode == 'driver':
        cube_offset_x = DRIVER_CUBE_X_OFFSET
        cube_offset_y = DRIVER_CUBE_Y_OFFSET
        cube_z_offset = DRIVER_CUBE_Z_OFFSET
        camera_offset_x = DRIVER_CAMERA_X_OFFSET
        camera_y_offset = DRIVER_CAMERA_Y_OFFSET
        camera_z_offset = DRIVER_CAMERA_Z_OFFSET
        camera_scale = DRIVER_CAMERA_SCALE
        cube_scale   = DRIVER_CUBE_SCALE
    elif mode == 'import':
        cube_offset_x = IMPORT_CUBE_X_OFFSET
        cube_offset_y = IMPORT_CUBE_Y_OFFSET
        cube_z_offset = IMPORT_CUBE_Z_OFFSET
        camera_offset_x = IMPORT_CAMERA_X_OFFSET
        camera_y_offset = IMPORT_CAMERA_Y_OFFSET
        camera_z_offset = IMPORT_CAMERA_Z_OFFSET
        camera_scale = IMPORT_CAMERA_SCALE
        cube_scale   = IMPORT_CUBE_SCALE

    # Calcular y asignar posición del cubo
    cube_x = object_location.x + cube_offset_x
    cube_y = object_location.y + cube_offset_y
    cube_z = object_location.z + cube_z_offset

    bpy.ops.mesh.primitive_cube_add(size=0.3, location=(cube_x, cube_y, cube_z))
    mesh_object = bpy.context.object
    mesh_object.name = get_next_name("camera_pivot_")
    # Aplicar la escala del cubo
    mesh_object.scale = (cube_scale, cube_scale, cube_scale)

    # Aplicar rotación de 30° en Y y luego aplicar transformación
    mesh_object.rotation_euler = (0, math.radians(30), 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    # Bloquear traslación y escala
    mesh_object.lock_location = (True, True, True)
    mesh_object.lock_scale = (True, True, True)
    # Se dejan las rotaciones desbloqueadas para permitir ajustes
    mesh_object.lock_rotation = (False, False, False)

    # Hacer que el cubo sea hijo del objeto objetivo
    mesh_object.parent = target_object

    # Calcular y asignar posición de la cámara
    camera_x = cube_x + camera_offset_x
    camera_y = cube_y + camera_y_offset
    camera_z = object_location.z + camera_z_offset
    bpy.ops.object.camera_add(location=(camera_x, camera_y, camera_z))
    camera = bpy.context.object
    camera.name = "Camera_Interna"

    # Hacer que la cámara sea hija del cubo
    camera.parent = mesh_object

    # Asignar rotación de la cámara (70° en X y -90° en Z)
    camera.rotation_euler = (math.radians(70), 0, -math.radians(90))
    
    # Aplicar escala a la cámara
    camera.scale = (camera_scale, camera_scale, camera_scale)

    # Configurar Focal Length y resolución
    camera.data.lens = 17
    bpy.context.scene.render.resolution_x = 6000
    bpy.context.scene.render.resolution_y = 4400

    # Bloquear la posición, rotación y escala de la cámara
    for i in range(3):
        camera.lock_location[i] = True
        camera.lock_rotation[i] = True
        camera.lock_scale[i] = True

    # Establecer la cámara como activa en la escena
    bpy.context.scene.camera = camera

    print(f"✅ Jerarquía aplicada: {mesh_object.name} sigue al objeto '{target_object.name}', y la cámara sigue al cubo.")
    return mesh_object

# ====================================================
# OPERADOR: Añadir Driver Reference (Icosphere)
# ====================================================
class AddDriverReferenceOperator(bpy.types.Operator):
    bl_idname = "object.add_driver_reference"
    bl_label = "Add Driver Reference"

    def execute(self, context):
        # Posicionar el cursor en el origen
        bpy.context.scene.cursor.location = (0.008159, -0.000029, 0.094565)

        # Crear la Icosphere y configurar escala y ubicación
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=(0.00818, 0, 0.624553))
        driver_obj = bpy.context.object
        driver_obj.scale = (0.53, 0.53, 0.53)
        driver_obj.name = get_next_name("reference_driver")
        
        # Establecer el origen de la icosfera en el cursor y reubicar el cursor en el origen
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        
        # Bloquear rotación (X e Y) y escala en XYZ
        driver_obj.lock_rotation = (True, True, False)
        driver_obj.lock_scale = (True, True, True)
        
        # Asignar color único basado en la cantidad de objetos "reference_driver"
        count = sum(1 for obj in bpy.data.objects if obj.name.startswith("reference_driver"))
        hue = (count * 0.618033988749895) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.8)
        
        mat = bpy.data.materials.new(name="Mat_" + driver_obj.name)
        mat.diffuse_color = (r, g, b, 1)
        if driver_obj.data.materials:
            driver_obj.data.materials[0] = mat
        else:
            driver_obj.data.materials.append(mat)
        
        # Crear el cubo y la cámara usando los offsets del modo "driver"
        create_camera_with_cube(driver_obj, mode='driver')
        
        # Seleccionar el objeto driver recién añadido y ejecutar Reset Position
        bpy.context.view_layer.objects.active = driver_obj
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        driver_obj.select_set(True)
        bpy.ops.object.reset_position()
        
        self.report({'INFO'}, f"Driver Reference '{driver_obj.name}' added with unique color and camera setup.")
        return {'FINISHED'}

# ====================================================
# HANDLER: Asignar cámara al seleccionar el cubo
# ====================================================
def selection_handler(scene):
    active_obj = bpy.context.view_layer.objects.active
    if active_obj and active_obj.name.startswith("camera_pivot_"):
        for child in active_obj.children:
            if child.type == 'CAMERA':
                if bpy.context.scene.camera != child:
                    bpy.context.scene.camera = child
                    for area in bpy.context.screen.areas:
                        if area.type == 'VIEW_3D':
                            override = {'area': area, 'region': area.regions[-1], 'scene': bpy.context.scene, 'active_object': child}
                            bpy.ops.view3d.object_as_camera(override)
                            print(f"✅ Cámara '{child.name}' asignada a la vista desde el cubo '{active_obj.name}'")
                            break
                break

# ====================================================
# OPERADORES PARA IMPORTAR MODELOS 3D
# ====================================================
# Función update para carpeta_modelos que fuerza redibujar la interfaz y actualiza el enum
def update_carpeta(self, context):
    # Forzar el redraw de todas las áreas 3D
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()
    # Actualizar el valor de modelo_seleccionado tomando el primer elemento disponible
    items = actualizar_modelos(self, context)
    if items:
        context.scene.modelo_seleccionado = items[0][0]
    else:
        context.scene.modelo_seleccionado = ""

# Propiedades para almacenar la ruta de la carpeta y el modelo seleccionado
bpy.types.Scene.carpeta_modelos = bpy.props.StringProperty(name="Carpeta de Modelos", default="", update=update_carpeta)
bpy.types.Scene.modelo_seleccionado = bpy.props.EnumProperty(items=[], name="Modelo Seleccionado")

def actualizar_modelos(self, context):
    modelos_disponibles = []
    carpeta = context.scene.carpeta_modelos
    if carpeta and os.path.isdir(carpeta):
        formatos_permitidos = (".obj", ".fbx", ".stl")
        for archivo in os.listdir(carpeta):
            if archivo.lower().endswith(formatos_permitidos):
                modelos_disponibles.append((archivo, archivo, "Modelo 3D"))
    return modelos_disponibles

# Actualizar la propiedad de modelos disponibles
bpy.types.Scene.modelo_seleccionado = bpy.props.EnumProperty(items=actualizar_modelos, name="Modelo Seleccionado")

class AbrirCarpetaOperator(bpy.types.Operator):
    bl_idname = "importador.seleccionar_carpeta"
    bl_label = "Seleccionar Carpeta"
    bl_description = "Abrir explorador de archivos para seleccionar una carpeta"
    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        # Asegurarse de que la propiedad existe, si no, se vuelve a definir
        if not hasattr(context.scene, "carpeta_modelos"):
            bpy.types.Scene.carpeta_modelos = bpy.props.StringProperty(name="Carpeta de Modelos", default="", update=update_carpeta)
        context.scene.carpeta_modelos = self.directory
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def procesar_modelo():
    # Verificar que se haya seleccionado algún objeto tras la importación
    if not bpy.context.selected_objects:
        print("❌ No se seleccionó ningún objeto después de la importación.")
        return None

    # Asignar el primer objeto seleccionado como objeto activo y renombrarlo
    obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = obj
    suffix = get_next_driver_suffix()
    obj.name = obj.name + suffix

    # Bloquear escala y rotación (solo se deja libre Z) y ubicación
    obj.lock_scale = (True, True, True)
    obj.lock_rotation = (True, True, False)
    obj.lock_location = (False, False, False)

    try:
        bpy.ops.geometry.attribute_convert(domain='CORNER', data_type='BYTE_COLOR')
    except RuntimeError:
        print("⚠️ Advertencia: No se pudo convertir los atributos de color.")

    # Realizar merge de vértices en modo Edit y restaurar el modo
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()

    bpy.ops.object.mode_set(mode='EDIT')
    mesh = bmesh.from_edit_mesh(obj.data)
    for v in mesh.verts:
        v.select = True
    bpy.ops.mesh.remove_doubles(threshold=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Ajustar rotación y ubicación del modelo importado
    obj.rotation_euler[2] += 1.5708  # 90° en radianes
    obj.location = (0.0, 0.0, 0.0)
    
    # Ajustar cursor y origen en bloque para ordenarlos
    bpy.context.scene.cursor.location = (0.013982, -0.000019, 0.094004)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)

    # Renombrar atributo de color a "Attribute"
    for attr in obj.data.attributes:
        if attr.data_type == 'BYTE_COLOR':
            attr.name = "Attribute"
            print("✅ Atributo de color renombrado a 'Attribute'.")
            break

    # Crear la Icosphere para referencia y configurar sus propiedades
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=(0.00818, 0, 0.624553))
    driver_obj = bpy.context.object
    driver_obj.scale = (0.53, 0.53, 0.53)
    driver_obj.name = get_next_name("reference_driver")
    
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.context.scene.cursor.location = (0.013982, -0.000019, 0.094004)
    
    driver_obj.lock_rotation = (True, True, False)
    driver_obj.lock_scale = (True, True, True)
    
    count = sum(1 for o in bpy.data.objects if o.name.startswith("reference_driver"))
    hue = (count * 0.618033988749895) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.8)
    
    mat = bpy.data.materials.new(name="Mat_" + driver_obj.name)
    mat.diffuse_color = (r, g, b, 1)
    if driver_obj.data.materials:
        driver_obj.data.materials[0] = mat
    else:
        driver_obj.data.materials.append(mat)
    
    # Crear cubo y cámara para el modelo importado (modo 'import')
    cube_obj = create_camera_with_cube(driver_obj, mode='import')
    
    print("✅ Registro de nombres:")
    print(" - Modelo importado: ", obj.name)
    print(" - Icosfera (reference_driver): ", driver_obj.name)
    print(" - Cubo hijo de la icosfera: ", cube_obj.name)
    print("✅ Modelo procesado: atributos, merge de vértices, rotación, movimiento y ajuste del origen completados.")

    # Guardar nombre y eliminar la icosfera
    driver_name = driver_obj.name
    bpy.data.objects.remove(driver_obj, do_unlink=True)
    print(f"✅ Icosfera '{driver_name}' removida del escenario.")

    # Reparentar el cubo: quitar padre actual y asignar como hijo del modelo importado
    cube_obj.parent = None
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    cube_obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.parent_set(type='OBJECT')
    print(f"✅ El cubo '{cube_obj.name}' ahora es hijo del modelo importado '{obj.name}'.")

    # Seleccionar el modelo importado y ejecutar Reset Position
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.ops.object.reset_position()

# ====================================================
# OPERADOR: Importar Modelo
# ====================================================
class ImportarModeloOperator(bpy.types.Operator):
    bl_idname = "importador.importar_modelo"
    bl_label = "Importar Modelo"
    bl_description = "Importar el modelo seleccionado y procesarlo"

    def execute(self, context):
        # Asegurarse de que la propiedad existe, si no, se vuelve a definir
        if not hasattr(context.scene, "modelo_seleccionado"):
            bpy.types.Scene.modelo_seleccionado = bpy.props.EnumProperty(items=actualizar_modelos, name="Modelo Seleccionado")
        modelo = context.scene.modelo_seleccionado
        carpeta = context.scene.carpeta_modelos
        ruta_completa = os.path.join(carpeta, modelo)
        try:
            if modelo.endswith(".obj"):
                bpy.ops.wm.obj_import(filepath=ruta_completa)
            elif modelo.endswith(".fbx"):
                bpy.ops.import_scene.fbx(filepath=ruta_completa)
            elif modelo.endswith(".stl"):
                bpy.ops.wm.stl_import(filepath=ruta_completa)
            else:
                self.report({'ERROR'}, f"Formato no soportado: {modelo}")
                return {'CANCELLED'}

            bpy.app.timers.register(procesar_modelo, first_interval=0.1)
            self.report({'INFO'}, f"Importado y procesado: {modelo}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error al importar {modelo}: {str(e)}")
            return {'CANCELLED'}

# ====================================================
# OPERADOR: Reset Position
# ====================================================
class ResetPositionOperator(bpy.types.Operator):
    bl_idname = "object.reset_position"
    bl_label = "Reset Position"
    bl_description = "Resetea la posición del 3D Cursor al centro, ajusta el origen del objeto activo y aplica All Transforms. Solo se permite para objetos con sufijo '_driverXX'."

    def execute(self, context):
        # Obtener el objeto activo (únicamente se resetea el objeto activo)
        obj = context.object
        if obj is None:
            self.report({'WARNING'}, "No hay ningún objeto seleccionado.")
            return {'CANCELLED'}
        
        # Verificar que el objeto tenga el sufijo '_driver' seguido de dos dígitos
        suffix = obj.name.split("_driver")[-1]
        if not (suffix.isdigit() and len(suffix) == 2):
            self.report({'WARNING'}, "Solo se puede resetear objetos con sufijo '_driverXX'.")
            return {'CANCELLED'}

        # Guardar la selección actual y luego aislar el objeto activo
        original_selection = [o for o in context.selected_objects]
        for o in original_selection:
            if o != obj:
                o.select_set(False)
        
        # Posicionar el cursor al centro de la escena
        context.scene.cursor.location = (0.0, 0.0, 0.0)
        
        # Calcular la diferencia entre el 3D Cursor y el objeto activo
        delta = context.scene.cursor.location - obj.location
        
        # Mover el objeto activo al nuevo origen
        obj.location += delta
        
        # Establecer el nuevo origen en el 3D Cursor (aplica solo al objeto activo)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        
        # Aplicar todos los transforms (equivalente a CTRL+A All Transforms) solo al objeto activo
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        # Restaurar la selección original
        for o in original_selection:
            o.select_set(True)
        
        self.report({'INFO'}, "El origen y el objeto activo se han movido al 3D Cursor y se han aplicado All Transforms.")
        return {'FINISHED'}

# ====================================================
# PANEL ÚNICO: Integración de Funcionalidades
# ====================================================
class ImportPanel(bpy.types.Panel):
    bl_label = "Import Models"
    bl_idname = "OBJECT_PT_import_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Spawn"

    def draw(self, context):
        layout = self.layout

        # Sección 1: Snap y Driver Reference
        props = context.scene.import_properties
        layout.prop(props, "enable_snap")
        layout.operator("object.add_driver_reference")
        layout.separator()

        # Sección 2: Importador de Modelos 3D
        layout.operator("importador.seleccionar_carpeta", text="Select Folder")
        # Se agrega comprobación para evitar error si las propiedades ya no existen
        if hasattr(context.scene, "carpeta_modelos") and context.scene.carpeta_modelos:
            layout.label(text="Path: " + context.scene.carpeta_modelos)
            layout.prop(context.scene, "modelo_seleccionado", text="Model")
            layout.operator("importador.importar_modelo", text="Import Model")
        layout.separator()
        # Sección 3: Reset Position
        layout.operator("object.reset_position", text="Reset Position")

# ====================================================
# REGISTRO Y DESREGISTRO DE CLASES Y HANDLERS
# ====================================================
classes = [
    ImportProperties,
    AddDriverReferenceOperator,
    AbrirCarpetaOperator,
    ImportarModeloOperator,
    ResetPositionOperator,
    ImportPanel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.import_properties = bpy.props.PointerProperty(type=ImportProperties)
    bpy.app.handlers.depsgraph_update_post.append(selection_handler)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "import_properties"):
        del bpy.types.Scene.import_properties
    if selection_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(selection_handler)
    # Eliminar propiedades personalizadas
    for prop in ["carpeta_modelos", "modelo_seleccionado"]:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)

if __name__ == "__main__":
    register()
    # Posicionar el cursor en el origen final
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
