import bpy
import json

# =============================
# OPERADOR PARA GUARDAR LOS DATOS DEL USUARIO
# =============================
class WM_OT_StoreData_Generate(bpy.types.Operator):
    """Guarda los datos en la escena"""
    bl_idname = "wm.store_data_generate"
    bl_label = "Store Data"

    def execute(self, context):
        global global_paths

        try:
            # Crear un diccionario ordenado
            ordered_paths = {}

            # PRIMERO, agregar "header"
            ordered_paths["header"] = 2

            # LUEGO, agregar todos los "pathX"
            for i in range(context.scene.path_count):
                path_id = str(i)
                ordered_paths[f"path{path_id}"] = {
                    "hasLeft": f"{path_id}_left" in context.scene,
                    "hasRight": f"{path_id}_right" in context.scene,
                    "index": int(path_id),
                    "quadEnd": context.scene.get(f"end_objects_{path_id}", "").split(',') if context.scene.get(f"end_objects_{path_id}") else [],
                    "quadIgnore": context.scene.get(f"ignore_objects_{path_id}", "").split(',') if context.scene.get(f"ignore_objects_{path_id}") else [],
                    "quadStart": context.scene.get(f"start_objects_{path_id}", "").split(',') if context.scene.get(f"start_objects_{path_id}") else []
                }

            # FINALMENTE, agregar "pathCount" AL FINAL
            ordered_paths["pathCount"] = context.scene.path_count

            # Guardamos en `bpy.types.Scene.global_paths`
            bpy.types.Scene.global_paths = ordered_paths

            # Imprimir en consola para verificar
            print(json.dumps(ordered_paths, indent=4))

            self.report({'INFO'}, "Datos guardados correctamente en memoria.")
        except Exception as e:
            self.report({'ERROR'}, f"Error al guardar datos: {str(e)}")
            print(f"❌ Error al guardar datos: {e}")

        return {'FINISHED'}

# =============================
# OPERADOR PARA EXPORTAR JSON
# =============================
class WM_OT_ExportPreset_Generate(bpy.types.Operator):
    """Exporta los datos tal cual están en memoria"""
    bl_idname = "wm.export_preset_generate"
    bl_label = "Export Preset"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        if not hasattr(bpy.types.Scene, "global_paths"):
            self.report({'ERROR'}, "No hay datos guardados.")
            return {'CANCELLED'}

        global_paths = bpy.types.Scene.global_paths

        if not global_paths:
            self.report({'ERROR'}, "No hay datos para exportar.")
            return {'CANCELLED'}

        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(json.dumps(global_paths, indent=4))

            self.report({'INFO'}, f"Preset exportado correctamente: {self.filepath}")
            print(f"✅ Preset exportado exitosamente en: {self.filepath}")

        except Exception as e:
            self.report({'ERROR'}, f"Error al exportar: {str(e)}")
            print(f"❌ Error al exportar: {e}")

        return {'FINISHED'}

    def invoke(self, context, event):
        # Asignar un nombre de archivo por defecto
        self.filepath = "untitled.json"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# =============================
# PANEL "Generate"
# =============================
class MYADDON_PT_Generate_Panel(bpy.types.Panel):
    """Panel de Blender con los botones"""
    bl_label = "Generate Panel"
    bl_idname = "MYADDON_PT_generate_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Generate"

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.store_data_generate", text="Store Data", icon="FILE_TICK")
        layout.operator("wm.export_preset_generate", text="Export Preset", icon="EXPORT")

# =============================
# REGISTRO Y DESREGISTRO
# =============================
classes = [WM_OT_StoreData_Generate, WM_OT_ExportPreset_Generate, MYADDON_PT_Generate_Panel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    if not hasattr(bpy.types.Scene, "global_paths"):
        bpy.types.Scene.global_paths = {}

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    if hasattr(bpy.types.Scene, "global_paths"):
        del bpy.types.Scene.global_paths

if __name__ == "__main__":
    register()
