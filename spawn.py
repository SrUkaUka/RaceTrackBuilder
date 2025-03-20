import bpy
import json
import os
from bpy_extras.io_utils import ExportHelper
import math

# Almacena posiciones y rotaciones de los 8 conductores
driver_spawns = [
    {"pos": (0.0, 0.0, 0.0), "rot": (0.0, 0.0, 0.0)}
    for _ in range(8)
]

# Lista de nombres válidos de conductores
VALID_DRIVER_NAMES = [
    "cortex_driver", "crash_driver", "coco_driver", "tiny_driver",
    "ngin_driver", "dingodile_driver", "polar_driver", "pura_driver"
]

# Propiedad para seleccionar el driver y el objeto de referencia
class SpawnProperties(bpy.types.PropertyGroup):
    driver_index: bpy.props.EnumProperty(
        name="Select Driver",
        description="Choose a driver to assign a spawn point",
        items=[(str(i), f"Driver {i}", f"Assign position to Driver {i}") for i in range(8)]
    )
    
    save_rotation: bpy.props.BoolProperty(
        name="Rotation",
        description="Enable to save rotation, disable to keep (0,0,0)",
        default=True
    )

# Operador para asignar la posición y rotación del conductor
class AssignSpawnOperator(bpy.types.Operator):
    bl_idname = "object.assign_spawn"
    bl_label = "Assign Spawn"

    def execute(self, context):
        selected_driver = int(context.scene.spawn_properties.driver_index)
        save_rotation = context.scene.spawn_properties.save_rotation

        obj = context.active_object  # Obtener el objeto seleccionado
        if obj is None:
            self.report({'ERROR'}, "No object selected. Select an object in the viewport.")
            return {'CANCELLED'}

        # Verifica si el nombre del objeto es válido
        valid = any(obj.name.startswith(name) for name in VALID_DRIVER_NAMES)
        if not valid:
            self.report({'ERROR'}, f"Invalid object '{obj.name}'. Select a driver object (e.g., cortex_driver00).")
            return {'CANCELLED'}

        # Guardar posición (X, Y, Z)
        global_position = obj.matrix_world.translation
        converted_position = (global_position.x, global_position.z, -global_position.y)
        driver_spawns[selected_driver]["pos"] = converted_position

        if save_rotation:
            # Obtener la rotación en Euler
            global_rotation = obj.matrix_world.to_euler('XYZ')
            raw_angle = global_rotation.z
            angle = raw_angle % (2 * math.pi)
            normalized_angle = angle / (2 * math.pi)
            
            rot_x_deg = math.degrees(obj.rotation_euler.x)
            rot_x_steps = round(rot_x_deg / 180, 3)

            # Mantiene la rotación Z actual y actualiza solo X e Y
            current_z = driver_spawns[selected_driver]["rot"][2]
            converted_rotation = (0.0, normalized_angle, current_z)
        else:
            # Mantiene la rotación Z y pone X, Y en 0
            converted_rotation = (0.0, 0.0, driver_spawns[selected_driver]["rot"][2])

        driver_spawns[selected_driver]["rot"] = converted_rotation
        self.report({'INFO'}, f"Assigned spawn for Driver {selected_driver} using '{obj.name}'")
        return {'FINISHED'}

# Operador para asignar la rotación de la cámara en el eje Z de CTR
class AssignCameraOperator(bpy.types.Operator):
    bl_idname = "object.assign_camera"
    bl_label = "Assign Camera"

    def execute(self, context):
        selected_driver = int(context.scene.spawn_properties.driver_index)

        obj = context.active_object  # Obtener el objeto seleccionado
        if obj is None:
            self.report({'ERROR'}, "No object selected. Select a camera pivot object.")
            return {'CANCELLED'}

        # Verifica que el nombre del objeto comience con "camera_pivot_"
        if not obj.name.startswith("camera_pivot_"):
            self.report({'ERROR'}, "Selected object is not a valid camera pivot (must start with 'camera_pivot_').")
            return {'CANCELLED'}

        # Obtener la rotación en el eje X de Blender
        rot_x_deg = math.degrees(obj.rotation_euler.x)

        # Convertir a formato CTR (1 unidad = 180°)
        camera_rot_z = round(rot_x_deg / 180, 3)

        # Solo modificamos el eje Z de la rotación en driver_spawns
        driver_spawns[selected_driver]["rot"] = (
            driver_spawns[selected_driver]["rot"][0],  # Mantiene X
            driver_spawns[selected_driver]["rot"][1],  # Mantiene Y
            camera_rot_z  # Asigna la nueva rotación Z
        )

        self.report({'INFO'}, f"Assigned camera rotation for Driver {selected_driver}: Z={camera_rot_z}")
        return {'FINISHED'}

# Operador para exportar los spawns en formato JSON
class ExportPresetOperator(bpy.types.Operator, ExportHelper):
    bl_idname = "object.export_preset"
    bl_label = "Export Preset"

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        file_path = self.filepath  # Ruta seleccionada por el usuario

        export_data = {
            "header": 0,
            "spawn": [
                {
                    "pos": {"x": d["pos"][0], "y": d["pos"][1], "z": d["pos"][2]},
                    "rot": {"x": d["rot"][0], "y": d["rot"][1], "z": d["rot"][2]}  # Z modificado por "Assign Camera"
                }
                for d in driver_spawns
            ]
        }

        try:
            with open(file_path, "w") as f:
                json.dump(export_data, f, indent=4)
            self.report({'INFO'}, f"Preset exported to {file_path}")
        except Exception as e:
            self.report({'ERROR'}, f"Error saving file: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

# Operador para restablecer los valores de los spawns
class ResetPresetOperator(bpy.types.Operator):
    bl_idname = "object.reset_preset"
    bl_label = "Reset Preset"

    def execute(self, context):
        global driver_spawns
        driver_spawns = [
            {"pos": (0.0, 0.0, 0.0), "rot": (0.0, 0.0, 0.0)}
            for _ in range(8)
        ]
        self.report({'INFO'}, "Preset reset to default values")
        return {'FINISHED'}

# Panel en la barra lateral de Blender
class SpawnPanel(bpy.types.Panel):
    bl_label = "Driver Spawns"
    bl_idname = "OBJECT_PT_spawn_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Spawn"

    def draw(self, context):
        layout = self.layout
        props = context.scene.spawn_properties

        layout.prop(props, "driver_index")
        layout.prop(props, "save_rotation")
        layout.operator("object.assign_spawn")
        layout.operator("object.assign_camera")

        selected_driver = int(props.driver_index)
        pos = driver_spawns[selected_driver]["pos"]
        rot = driver_spawns[selected_driver]["rot"]

        layout.label(text=f"Position: X={pos[0]:.3f}, Y={pos[1]:.3f}, Z={pos[2]:.3f}")
        layout.label(text=f"Rotation: X={rot[0]:.2f}, Y={rot[1]:.3f}, Z={rot[2]:.3f}")

        layout.separator()
        layout.operator("object.export_preset")
        layout.operator("object.reset_preset")

# Registrar clases en Blender
classes = [SpawnProperties, AssignSpawnOperator, AssignCameraOperator, ExportPresetOperator, ResetPresetOperator, SpawnPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.spawn_properties = bpy.props.PointerProperty(type=SpawnProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.spawn_properties

if __name__ == "__main__":
    register()
