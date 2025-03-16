import bpy
import os
import math

# Función para alternar Snap entre Face Project e Incremental
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

# Propiedades para importar modelos y activar Snap
class ImportProperties(bpy.types.PropertyGroup):
    folder_path: bpy.props.StringProperty(
        name="Folder Path",
        description="Select the folder where models are stored",
        subtype='DIR_PATH',
    )
    
    import_choice: bpy.props.EnumProperty(
        name="Select Model to Import",
        description="Choose the model to import",
        items=[
            ('Crash', 'Crash', 'Import Crash.fbx'),
            ('Cortex', 'Cortex', 'Import Cortex.fbx'),
            ('Tiny', 'Tiny', 'Import Tiny.fbx'),
            ('Coco', 'Coco', 'Import Coco.fbx'),
            ('Ngin', 'Ngin', 'Import Ngin.fbx'),
            ('Dingodile', 'Dingodile', 'Import Dingodile.fbx'),
            ('Polar', 'Polar', 'Import Polar.fbx'),
            ('Pura', 'Pura', 'Import Pura.fbx'),
            ('Other', 'Other', 'Import any other file')
        ]
    )

    enable_snap: bpy.props.BoolProperty(
        name="Enable Snap",
        description="Toggle Snap Face & Face Project",
        default=False,
        update=toggle_snap
    )

# Obtener el siguiente nombre disponible para objetos en la escena
def get_next_name(base_name):
    existing_names = {obj.name for obj in bpy.data.objects}
    index = 0
    new_name = f"{base_name}{index:02d}"
    while new_name in existing_names:
        index += 1
        new_name = f"{base_name}{index:02d}"
    return new_name

# Operador para importar un modelo, bloquear ejes de rotación y crear la cámara
class ImportReferenceOperator(bpy.types.Operator):
    bl_idname = "object.import_reference"
    bl_label = "Import Reference Model"

    def execute(self, context):
        folder_path = context.scene.import_properties.folder_path
        import_choice = context.scene.import_properties.import_choice

        if not folder_path:
            self.report({'ERROR'}, "Please select a folder path.")
            return {'CANCELLED'}

        if import_choice == 'Other':
            self.report({'ERROR'}, "Please specify a model file to import.")
            return {'CANCELLED'}

        model_file = f"{import_choice}.fbx"
        file_path = os.path.join(folder_path, model_file)

        if not os.path.exists(file_path):
            self.report({'ERROR'}, f"Model file '{model_file}' not found in {folder_path}.")
            return {'CANCELLED'}

        # Importar el modelo
        bpy.ops.import_scene.fbx(filepath=file_path)

        # Obtener el último objeto importado
        imported_objects = bpy.context.selected_objects
        if not imported_objects:
            self.report({'ERROR'}, "No objects were imported.")
            return {'CANCELLED'}

        imported_obj = imported_objects[0]

        # Asignar nombre con sufijo _driverXX
        imported_obj.name = get_next_name(f"{import_choice.lower()}_driver")

        # Bloquear rotaciones en X e Y, permitir en Z
        imported_obj.lock_rotation[0] = True
        imported_obj.lock_rotation[1] = True
        imported_obj.lock_rotation[2] = False

        # 📌 Bloquear la escala en XYZ para _driver
        imported_obj.lock_scale[0] = True
        imported_obj.lock_scale[1] = True
        imported_obj.lock_scale[2] = True

        # 📌 CREAR EL CUBO Y LA CÁMARA, HACIENDO QUE SIGAN AL MODELO IMPORTADO
        create_camera_with_cube(imported_obj)

        self.report({'INFO'}, f"Imported {model_file} as {imported_obj.name}, locked X/Y rotation, and added camera setup.")
        return {'FINISHED'}

# Función para crear el cubo con restricciones de transformación y la cámara alineada
def create_camera_with_cube(target_object):
    object_location = target_object.location

    # Obtener un nombre único para el cubo
    cube_name = get_next_name("camera_pivot_")

    # 📌 Crear el cubo y rotarlo 30° en Y
    cube_x = object_location.x - 7.0  
    cube_z = object_location.z + 5.0  
    bpy.ops.mesh.primitive_cube_add(size=1.5, location=(cube_x, object_location.y, cube_z))
    mesh_object = bpy.context.object
    mesh_object.name = cube_name

    # Rotar el cubo 30° en Y y aplicar la transformación
    mesh_object.rotation_euler = (0, math.radians(30), 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    # 📌 Bloquear la traslación en X, Y y Z
    mesh_object.lock_location[0] = True
    mesh_object.lock_location[1] = True
    mesh_object.lock_location[2] = True

    # 📌 Bloquear la escala en XYZ para el cubo
    mesh_object.lock_scale[0] = True
    mesh_object.lock_scale[1] = True
    mesh_object.lock_scale[2] = True

    # 📌 Asegurar que todas las rotaciones estén activas
    mesh_object.lock_rotation[0] = False
    mesh_object.lock_rotation[1] = False
    mesh_object.lock_rotation[2] = False

    # 📌 Hacer que el cubo sea hijo del objeto importado
    mesh_object.parent = target_object

    # 📌 Crear la cámara
    camera_x = cube_x + 7.8  
    camera_z = object_location.z  
    bpy.ops.object.camera_add(location=(camera_x, object_location.y, camera_z))
    camera = bpy.context.object
    camera.name = "Camera_Interna"

    # 📌 Hacer que la cámara sea hija del cubo
    camera.parent = mesh_object

    # 📌 Rotar la cámara 70° en X
    camera.rotation_euler = (math.radians(70), 0, -math.radians(90))

    # 📌 Modificar el Focal Length
    camera.data.lens = 20  

    # Configurar la resolución de la cámara
    bpy.context.scene.render.resolution_x = 3000
    bpy.context.scene.render.resolution_y = 4400

    # 📌 Bloquear TODO en la cámara
    for i in range(3):
        camera.lock_location[i] = True
        camera.lock_rotation[i] = True
        camera.lock_scale[i] = True

    # Establecer la cámara como la activa
    bpy.context.scene.camera = camera

    print(f"✅ Jerarquía aplicada: {mesh_object.name} sigue al modelo importado, la cámara sigue al cubo.")

# Panel en la barra lateral de Blender
class ImportPanel(bpy.types.Panel):
    bl_label = "Import Models"
    bl_idname = "OBJECT_PT_import_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Spawn"

    def draw(self, context):
        layout = self.layout
        props = context.scene.import_properties

        layout.prop(props, "folder_path")
        layout.prop(props, "import_choice")
        layout.operator("object.import_reference")
        layout.separator()
        layout.prop(props, "enable_snap")

# Registro de clases
classes = [ImportProperties, ImportReferenceOperator, ImportPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.import_properties = bpy.props.PointerProperty(type=ImportProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.import_properties

if __name__ == "__main__":
    register()
