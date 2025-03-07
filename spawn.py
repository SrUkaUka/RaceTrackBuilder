import bpy
import json
import os
from bpy_extras.io_utils import ExportHelper
import mathutils  # Para manejar matrices y rotaciones

# Almacena posiciones y rotaciones de los 8 conductores
driver_spawns = [{"pos": (0.0, 0.0, 0.0), "rot": (0.0, 0.0, 0.0)} for _ in range(8)]

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

# Operador para asignar la posición de un objeto seleccionado al driver
class AssignSpawnOperator(bpy.types.Operator):
    bl_idname = "object.assign_spawn"
    bl_label = "Assign Spawn"

    def execute(self, context):
        selected_driver = int(context.scene.spawn_properties.driver_index)
        save_rotation = context.scene.spawn_properties.save_rotation

        obj = context.active_object  # Obtener el objeto seleccionado

        if obj is None:  # Si no hay objeto seleccionado
            self.report({'ERROR'}, "No object selected. Select an object in the viewport.")
            return {'CANCELLED'}

        # Obtener la posición global del objeto
        global_position = obj.matrix_world.translation

        # Convertir Blender → CTR (mantener X igual, invertir solo Z)
        converted_position = (global_position.x, global_position.z, -global_position.y)

        driver_spawns[selected_driver]["pos"] = converted_position

        # Obtener la rotación global en euler
        global_rotation = obj.matrix_world.to_euler('XYZ')

        # Convertir rotación Blender → CTR (mantener X igual, invertir solo Z)
        converted_rotation = (global_rotation.x, global_rotation.z, -global_rotation.y)

        driver_spawns[selected_driver]["rot"] = converted_rotation if save_rotation else (0.0, 0.0, 0.0)

        self.report({'INFO'}, f"Assigned spawn for Driver {selected_driver} using '{obj.name}'")
        return {'FINISHED'}

# Operador para exportar los spawns en formato JSON
class ExportPresetOperator(bpy.types.Operator, ExportHelper):
    bl_idname = "object.export_preset"
    bl_label = "Export Preset"

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        file_path = self.filepath  # Ruta seleccionada por el usuario

        # Formatear la información para exportar
        export_data = {
            "header": 0,
            "spawn": [
                {
                    "pos": {"x": d["pos"][0], "y": d["pos"][1], "z": d["pos"][2]},
                    "rot": {"x": d["rot"][0], "y": d["rot"][1], "z": d["rot"][2]}
                }
                for d in driver_spawns
            ]
        }

        # Guardar el archivo JSON
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
        driver_spawns = [{"pos": (0.0, 0.0, 0.0), "rot": (0.0, 0.0, 0.0)} for _ in range(8)]
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
        layout.prop(props, "save_rotation")  # Checkbox para la rotación
        layout.operator("object.assign_spawn")

        selected_driver = int(props.driver_index)
        pos = driver_spawns[selected_driver]["pos"]
        rot = driver_spawns[selected_driver]["rot"]

        layout.label(text=f"Position: X={pos[0]:.2f}, Y={pos[1]:.2f}, Z={pos[2]:.2f}")
        layout.label(text=f"Rotation: X={rot[0]:.2f}, Y={rot[1]:.2f}, Z={rot[2]:.2f}")

        layout.separator()
        layout.operator("object.export_preset")  # Botón para exportar
        layout.operator("object.reset_preset")   # Botón para resetear

# Registrar clases en Blender
classes = [SpawnProperties, AssignSpawnOperator, ExportPresetOperator, ResetPresetOperator, SpawnPanel]

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
