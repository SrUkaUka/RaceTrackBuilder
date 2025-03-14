import bpy
import json
import os
import bpy_extras.io_utils

# Variable global que almacena los valores del gradiente
saved_gradient_values = []

# Función para obtener los valores actuales del ColorRamp
def update_saved_gradient_values():
    global saved_gradient_values
    world = bpy.context.scene.world
    color_ramp = None

    # Buscar el nodo ColorRamp
    if world and world.use_nodes and world.node_tree:
        for node in world.node_tree.nodes:
            if isinstance(node, bpy.types.ShaderNodeValToRGB):
                color_ramp = node
                break

    # Si encontramos el nodo, guardamos sus valores
    if color_ramp:
        saved_gradient_values.clear()  # Limpiar la lista antes de actualizar
        for element in color_ramp.color_ramp.elements:
            position = (element.position * 440.0) - 220.0  # Conversión de rango
            rgb = element.color[:3]  # Obtener solo RGB
            saved_gradient_values.append((position, rgb))

# Función para exportar el preset en formato JSON con el orden correcto
def export_preset(filepath):
    global saved_gradient_values

    # Asegurar que los valores están actualizados
    update_saved_gradient_values()

    # Verificar si hay suficientes valores antes de exportar
    if len(saved_gradient_values) < 2:
        print("Error: No hay suficientes datos en saved_gradient_values para exportar.")
        return

    # Estructura del JSON
    preset_data = {
        "clearColor": {
            "r": 0.0,
            "g": 0.0,
            "b": 0.0,
            "a": False
        },
        "configFlags": 1,
        "header": 1,
        "skyGradient": []
    }

    # Iterar sobre los valores del gradiente
    for i in range(len(saved_gradient_values) - 1):
        pos_from, color_from = saved_gradient_values[i]
        pos_to, color_to = saved_gradient_values[i + 1]

        # **El primer par se mantiene en orden natural**
        if i == 0:
            pass  # No hacemos nada, ya está correcto
        else:
            # **Todos los demás pares se invierten si es necesario**
            if pos_from < pos_to:
                pos_from, pos_to = pos_to, pos_from  # Intercambiar posiciones
                color_from, color_to = color_to, color_from  # Intercambiar colores

        # Agregar al JSON
        gradient_entry = {
            "colorFrom": {
                "r": round(float(color_from[0]), 10),
                "g": round(float(color_from[1]), 10),
                "b": round(float(color_from[2]), 10),
                "a": False
            },
            "colorTo": {
                "r": round(float(color_to[0]), 10),
                "g": round(float(color_to[1]), 10),
                "b": round(float(color_to[2]), 10),
                "a": False
            },
            "posFrom": round(float(pos_from), 10),
            "posTo": round(float(pos_to), 10)
        }
        
        preset_data["skyGradient"].append(gradient_entry)

    # Guardar en un archivo JSON
    with open(filepath, "w", encoding="utf-8") as json_file:
        json.dump(preset_data, json_file, indent=4)

    print(f"Preset exportado en: {filepath}")

# Operador de Blender para abrir el explorador de archivos y guardar el JSON
class ExportPresetOperator(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "export.preset"
    bl_label = "Export Preset"

    # Opciones del archivo
    filename_ext = ".json"

    def execute(self, context):
        export_preset(self.filepath)
        return {'FINISHED'}

# Panel de Blender con solo el botón "Export Preset"
class ExportGradientPanel(bpy.types.Panel):
    bl_label = "Export Gradient Preset"  # Nuevo título
    bl_idname = "VIEW3D_PT_export_gradient_panel"  # Nuevo ID único
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Gradient"  # Se mantiene en la misma pestaña

    def draw(self, context):
        layout = self.layout
        layout.operator("export.preset", text="Export Preset")  # Único botón

# Registrar clases en Blender
def register():
    bpy.utils.register_class(ExportPresetOperator)
    bpy.utils.register_class(ExportGradientPanel)  # Registrar el nuevo panel

def unregister():
    bpy.utils.unregister_class(ExportPresetOperator)
    bpy.utils.unregister_class(ExportGradientPanel)  # Desregistrar el nuevo panel

if __name__ == "__main__":
    register()
