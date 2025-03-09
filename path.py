import bpy
import json
import os

# =============================
# Variables globales
# =============================
global_paths = {}         # Registro global: cada path (principal o subpath) se guarda aquí
GLOBAL_PATH_TOTAL = 0     # Contador global total de paths (incluye subpaths)

# =============================
# Función auxiliar para dibujar el contenido de un Path (o sub-panel)
# =============================
def draw_path_content(layout, context, path_identifier):
    for category in ["start", "end", "ignore"]:
        box = layout.box()
        box.label(text=category.capitalize())
        
        row = box.row()
        row.operator(f"wm.add_{category}_{path_identifier}", text="Add")
        row.operator(f"wm.remove_selected_{path_identifier}", text="Remove Selected")
        
        col = box.column()
        for obj_name in context.scene.get(f"{category}_objects_{path_identifier}", "").split(','):
            if obj_name:
                prop_name = f"{category}_object_{path_identifier}_{obj_name}"
                col.prop(context.scene, prop_name, text=obj_name)
                
    # Botones para agregar subpaths (Left/Right)
    row = layout.row()
    row.operator(f"wm.add_left_{path_identifier}", text="Add Left Path")
    row.operator(f"wm.add_right_{path_identifier}", text="Add Right Path")

# =============================
# Panel principal
# =============================
class MYADDON_PT_Generate(bpy.types.Panel):
    bl_label = "Generate"
    bl_idname = "MYADDON_PT_generate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Generate"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Path Operator")
        layout.operator("wm.create_path", text="Create Path", icon="PLUS")
        if context.scene.path_count > 0:
            layout.operator("wm.remove_path", text="Remove Last Path", icon="X")
        # Se eliminó el botón "Store Data"

# =============================
# Panel base para cada Path (principal o subpath)
# =============================
class MYADDON_PT_PathBase(bpy.types.Panel):
    """Clase base para generar Paths dinámicamente"""
    bl_label = "Path Base"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Generate"

    def draw(self, context):
        layout = self.layout
        # Se asume que el bl_idname tiene el formato MYADDON_PT_path_<identificador>
        path_identifier = self.bl_idname.split("_")[-1]
        layout.label(text=f"Path {path_identifier}")
        
        # Si es un path principal (sin "_" en el identificador) se añade el botón para remover subpaths
        if "_" not in path_identifier:
            row = layout.row()
            row.operator("wm.remove_subpaths", text="Remove Subpaths").path_identifier = path_identifier

        # Dibujar los subpaths (si existen) usando el identificador guardado en la propiedad del path principal
        sub_panels_str = context.scene.get(f"sub_panels_{path_identifier}", "")
        if sub_panels_str:
            for sub_path_identifier in sub_panels_str.split(','):
                box = layout.box()
                box.label(text=f"Path {sub_path_identifier}")
                draw_path_content(box, context, sub_path_identifier)
                
        # Dibujar el contenido del path principal (o subpath) en sí
        draw_path_content(layout, context, path_identifier)

# =============================
# Operadores base para agregar y eliminar objetos
# =============================
class AddObjectsBase(bpy.types.Operator):
    """Clase base para agregar objetos evitando duplicados"""
    list_name: str
    prefix: str
    path_identifier: str  # Ej: "1" o "1_left"

    def execute(self, context):
        selected_objs = [obj.name for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objs:
            self.report({'WARNING'}, "No hay objetos MESH seleccionados")
            return {'CANCELLED'}
        
        current_objects = context.scene.get(self.list_name, "")
        current_list = set(current_objects.split(',')) if current_objects else set()
        new_objects = set(selected_objs) - current_list  # Evitar duplicados
        
        if new_objects:
            context.scene[self.list_name] = ",".join(current_list | new_objects)
            for obj_name in new_objects:
                setattr(bpy.types.Scene, f"{self.prefix}_{obj_name}", 
                        bpy.props.BoolProperty(name=obj_name, default=False))
            self.report({'INFO'}, "Objetos añadidos correctamente")
        else:
            self.report({'INFO'}, "Todos los objetos ya estaban en la lista")
        
        # Actualizar el registro global para este path
        for category in ["start", "end", "ignore"]:
            prop_val = context.scene.get(f"{category}_objects_{self.path_identifier}", "")
            global_paths[self.path_identifier][category] = [x for x in prop_val.split(',') if x]
        return {'FINISHED'}

class RemoveSelectedObjectsBase(bpy.types.Operator):
    """Clase base para eliminar objetos marcados en la checkbox"""
    path_identifier: str  # Ej: "1" o "1_left"

    def execute(self, context):
        for category in ["start", "end", "ignore"]:
            list_name = f"{category}_objects_{self.path_identifier}"
            updated_list = []
            for obj_name in context.scene.get(list_name, "").split(','):
                prop_name = f"{category}_object_{self.path_identifier}_{obj_name}"
                if obj_name and not getattr(context.scene, prop_name, False):
                    updated_list.append(obj_name)
            context.scene[list_name] = ",".join(updated_list)
            global_paths[self.path_identifier][category] = updated_list
        self.report({'INFO'}, "Selected objects removed")
        return {'FINISHED'}

# =============================
# Operador para añadir un nuevo subpath (Left o Right)
# =============================
class AddPathBoxOperator(bpy.types.Operator):
    """Operador para añadir un nuevo subpath de forma independiente"""
    bl_idname = "wm.add_path_box"  # bl_idname base; se crea dinámicamente
    bl_label = "Add Path Box"
    path_index: str  # Identificador del path principal (ej: "1")
    side: str        # "left" o "right"

    def execute(self, context):
        global GLOBAL_PATH_TOTAL, global_paths
        sub_path_identifier = f"{self.path_index}_{self.side}"
        
        prop_name = f"sub_panels_{self.path_index}"
        sub_panels = context.scene.get(prop_name, "")
        panels = sub_panels.split(',') if sub_panels else []
        if sub_path_identifier not in panels:
            panels.append(sub_path_identifier)
            context.scene[prop_name] = ",".join(panels)
        
        new_class = type(
            f"MYADDON_PT_path_{sub_path_identifier}",
            (MYADDON_PT_PathBase,),
            {
                "bl_label": f"Path {sub_path_identifier}",
                "bl_idname": f"MYADDON_PT_path_{sub_path_identifier}",
                "bl_parent_id": f"MYADDON_PT_path_{self.path_index}",
            }
        )
        if not hasattr(bpy.types, new_class.__name__):
            bpy.utils.register_class(new_class)
            for category in ["start", "end", "ignore"]:
                setattr(bpy.types.Scene, f"{category}_objects_{sub_path_identifier}",
                        bpy.props.StringProperty(default=""))
                add_class = type(
                    f"WM_OT_Add{category.capitalize()}_{sub_path_identifier}",
                    (AddObjectsBase,),
                    {
                        "bl_idname": f"wm.add_{category}_{sub_path_identifier}",
                        "bl_label": f"Add {category.capitalize()} {sub_path_identifier}",
                        "list_name": f"{category}_objects_{sub_path_identifier}",
                        "prefix": f"{category}_object_{sub_path_identifier}",
                        "path_identifier": sub_path_identifier,
                    }
                )
                remove_class = type(
                    f"WM_OT_RemoveSelected_{sub_path_identifier}",
                    (RemoveSelectedObjectsBase,),
                    {
                        "bl_idname": f"wm.remove_selected_{sub_path_identifier}",
                        "bl_label": f"Remove Selected {sub_path_identifier}",
                        "path_identifier": sub_path_identifier,
                    }
                )
                bpy.utils.register_class(add_class)
                bpy.utils.register_class(remove_class)
            
            global_paths[sub_path_identifier] = {
                "id": sub_path_identifier,
                "parent": self.path_index,
                "start": [],
                "end": [],
                "ignore": []
            }
            GLOBAL_PATH_TOTAL += 1

        self.report({'INFO'}, f"{self.side.capitalize()} Path added to Path {self.path_index}")
        return {'FINISHED'}

# =============================
# Operador para crear Paths dinámicos (Paths principales)
# =============================
class WM_OT_CreatePath(bpy.types.Operator):
    bl_idname = "wm.create_path"
    bl_label = "Create Path"

    def execute(self, context):
        global GLOBAL_PATH_TOTAL, global_paths
        path_count = context.scene.path_count  # Path principal
        path_identifier = str(path_count)
        path_idname = f"MYADDON_PT_path_{path_identifier}"

        new_class = type(
            path_idname,
            (MYADDON_PT_PathBase,),
            {
                "bl_label": f"Path {path_identifier}",
                "bl_idname": path_idname,
                "bl_parent_id": "MYADDON_PT_generate",
            }
        )

        if not hasattr(bpy.types, path_identifier):
            bpy.utils.register_class(new_class)
            for category in ["start", "end", "ignore"]:
                setattr(bpy.types.Scene, f"{category}_objects_{path_identifier}",
                        bpy.props.StringProperty(default=""))
                add_class = type(
                    f"WM_OT_Add{category.capitalize()}_{path_identifier}",
                    (AddObjectsBase,),
                    {
                        "bl_idname": f"wm.add_{category}_{path_identifier}",
                        "bl_label": f"Add {category.capitalize()} {path_identifier}",
                        "list_name": f"{category}_objects_{path_identifier}",
                        "prefix": f"{category}_object_{path_identifier}",
                        "path_identifier": path_identifier,
                    }
                )
                remove_class = type(
                    f"WM_OT_RemoveSelected_{path_identifier}",
                    (RemoveSelectedObjectsBase,),
                    {
                        "bl_idname": f"wm.remove_selected_{path_identifier}",
                        "bl_label": f"Remove Selected {path_identifier}",
                        "path_identifier": path_identifier,
                    }
                )
                bpy.utils.register_class(add_class)
                bpy.utils.register_class(remove_class)
            
            left_class = type(
                f"WM_OT_AddLeft_{path_identifier}",
                (AddPathBoxOperator,),
                {
                    "bl_idname": f"wm.add_left_{path_identifier}",
                    "bl_label": f"Add Left Path {path_identifier}",
                    "path_index": path_identifier,
                    "side": "left",
                }
            )
            right_class = type(
                f"WM_OT_AddRight_{path_identifier}",
                (AddPathBoxOperator,),
                {
                    "bl_idname": f"wm.add_right_{path_identifier}",
                    "bl_label": f"Add Right Path {path_identifier}",
                    "path_index": path_identifier,
                    "side": "right",
                }
            )
            bpy.utils.register_class(left_class)
            bpy.utils.register_class(right_class)

            setattr(bpy.types.Scene, f"sub_panels_{path_identifier}",
                    bpy.props.StringProperty(default=""))
            
            global_paths[path_identifier] = {
                "id": path_identifier,
                "parent": None,
                "start": [],
                "end": [],
                "ignore": []
            }
            GLOBAL_PATH_TOTAL += 1
            context.scene.path_count += 1

            self.report({'INFO'}, f"Path {path_identifier} created!")
        else:
            self.report({'WARNING'}, f"Path {path_identifier} already exists!")
        return {'FINISHED'}

# =============================
# Operador para eliminar el último Path principal (junto con sus subpaths)
# =============================
class WM_OT_RemovePath(bpy.types.Operator):
    bl_idname = "wm.remove_path"
    bl_label = "Remove Last Path"

    def execute(self, context):
        global GLOBAL_PATH_TOTAL, global_paths
        if context.scene.path_count == 0:
            self.report({'WARNING'}, "No paths to remove!")
            return {'CANCELLED'}

        path_count = context.scene.path_count - 1
        path_identifier = str(path_count)
        path_idname = f"MYADDON_PT_path_{path_identifier}"

        if hasattr(bpy.types, path_idname):
            # Eliminar subpaths asociados
            sub_panels_str = context.scene.get(f"sub_panels_{path_identifier}", "")
            if sub_panels_str:
                for sub_path_identifier in sub_panels_str.split(','):
                    sub_panel_idname = f"MYADDON_PT_path_{sub_path_identifier}"
                    if hasattr(bpy.types, sub_panel_idname):
                        bpy.utils.unregister_class(getattr(bpy.types, sub_panel_idname))
                    for category in ["start", "end", "ignore"]:
                        add_op = f"WM_OT_Add{category.capitalize()}_{sub_path_identifier}"
                        remove_op = f"WM_OT_RemoveSelected_{sub_path_identifier}"
                        if hasattr(bpy.types, add_op):
                            bpy.utils.unregister_class(getattr(bpy.types, add_op))
                        if hasattr(bpy.types, remove_op):
                            bpy.utils.unregister_class(getattr(bpy.types, remove_op))
                    for category in ["start", "end", "ignore"]:
                        prop_name = f"{category}_objects_{sub_path_identifier}"
                        if hasattr(bpy.types.Scene, prop_name):
                            delattr(bpy.types.Scene, prop_name)
                    if sub_path_identifier in global_paths:
                        del global_paths[sub_path_identifier]
                    GLOBAL_PATH_TOTAL -= 1

            # Eliminar propiedades y operadores del path principal
            for category in ["start", "end", "ignore"]:
                prop_name = f"{category}_objects_{path_identifier}"
                if hasattr(bpy.types.Scene, prop_name):
                    delattr(bpy.types.Scene, prop_name)
                add_op = f"WM_OT_Add{category.capitalize()}_{path_identifier}"
                remove_op = f"WM_OT_RemoveSelected_{path_identifier}"
                if hasattr(bpy.types, add_op):
                    bpy.utils.unregister_class(getattr(bpy.types, add_op))
                if hasattr(bpy.types, remove_op):
                    bpy.utils.unregister_class(getattr(bpy.types, remove_op))
            left_op = f"WM_OT_AddLeft_{path_identifier}"
            right_op = f"WM_OT_AddRight_{path_identifier}"
            if hasattr(bpy.types, left_op):
                bpy.utils.unregister_class(getattr(bpy.types, left_op))
            if hasattr(bpy.types, right_op):
                bpy.utils.unregister_class(getattr(bpy.types, right_op))
            prop_sub = f"sub_panels_{path_identifier}"
            if hasattr(bpy.types.Scene, prop_sub):
                delattr(bpy.types.Scene, prop_sub)
            bpy.utils.unregister_class(getattr(bpy.types, path_idname))
            if path_identifier in global_paths:
                del global_paths[path_identifier]
            context.scene.path_count -= 1
            GLOBAL_PATH_TOTAL -= 1

            if context.scene.path_count == 0:
                global_paths.clear()
                self.report({'INFO'}, "Todos los paths eliminados. Nuevo path se creará sin subpaths previos.")
            else:
                self.report({'INFO'}, f"Last Path ({path_identifier}) removed!")
        else:
            self.report({'WARNING'}, "No Paths found to remove!")
        return {'FINISHED'}

# =============================
# Operador para remover subpaths de un path principal
# =============================
class WM_OT_RemoveSubPaths(bpy.types.Operator):
    bl_idname = "wm.remove_subpaths"
    bl_label = "Remove Subpaths"
    
    path_identifier: bpy.props.StringProperty()

    def execute(self, context):
        global GLOBAL_PATH_TOTAL, global_paths
        prop_name = f"sub_panels_{self.path_identifier}"
        sub_panels_str = context.scene.get(prop_name, "")
        if sub_panels_str:
            for sub_path_identifier in sub_panels_str.split(','):
                sub_panel_idname = f"MYADDON_PT_path_{sub_path_identifier}"
                if hasattr(bpy.types, sub_panel_idname):
                    bpy.utils.unregister_class(getattr(bpy.types, sub_panel_idname))
                for category in ["start", "end", "ignore"]:
                    add_op = f"WM_OT_Add{category.capitalize()}_{sub_path_identifier}"
                    remove_op = f"WM_OT_RemoveSelected_{sub_path_identifier}"
                    if hasattr(bpy.types, add_op):
                        bpy.utils.unregister_class(getattr(bpy.types, add_op))
                    if hasattr(bpy.types, remove_op):
                        bpy.utils.unregister_class(getattr(bpy.types, remove_op))
                    prop_cat = f"{category}_objects_{sub_path_identifier}"
                    if hasattr(bpy.types.Scene, prop_cat):
                        delattr(bpy.types.Scene, prop_cat)
                if sub_path_identifier in global_paths:
                    del global_paths[sub_path_identifier]
                GLOBAL_PATH_TOTAL -= 1
            context.scene[prop_name] = ""
            self.report({'INFO'}, f"All subpaths removed for Path {self.path_identifier}")
        else:
            self.report({'INFO'}, f"No subpaths found for Path {self.path_identifier}")
        return {'FINISHED'}

# =============================
# Operador para almacenar y mostrar los datos en consola en el nuevo formato JSON
# (Operador conservado, pero el botón ya no se muestra en la UI)
# =============================
class WM_OT_StoreData(bpy.types.Operator):
    bl_idname = "wm.store_data"
    bl_label = "Store Data"

    def execute(self, context):
        global global_paths  # Asegurarse de referenciar la variable global

        try:
            # (Opcional) Actualizar global_paths leyendo los valores actuales de la escena...
            for path_id in list(global_paths.keys()):
                for category in ["start", "end", "ignore"]:
                    prop_val = context.scene.get(f"{category}_objects_{path_id}", "")
                    global_paths[path_id][category] = [x for x in prop_val.split(',') if x]

            # Sólo consideramos los paths principales (sin "parent")
            main_paths = [key for key, data in global_paths.items() if data.get("parent") is None]
            try:
                main_paths.sort(key=lambda x: int(x))
            except Exception:
                pass

            # Construimos el diccionario de exportación en el formato deseado
            export_data = {"header": 2}
            for main_id in main_paths:
                data = global_paths[main_id]
                export_data[f"path{main_id}"] = {
                    "hasLeft": f"{main_id}_left" in global_paths,
                    "hasRight": f"{main_id}_right" in global_paths,
                    "index": int(main_id),
                    "quadEnd": data.get("end", []),
                    "quadIgnore": data.get("ignore", []),
                    "quadStart": data.get("start", [])
                }
            export_data["pathCount"] = len(main_paths)

            # Convertimos a JSON y lo mostramos en la consola
            json_output = json.dumps(export_data, indent=4)
            print(json_output)
        except Exception as e:
            print("Error al almacenar datos:", e)
        
        self.report({'INFO'}, "Data stored and printed in console (JSON format).")
        return {'FINISHED'}

# =============================
# Registro y Desregistro
# =============================
classes = [
    MYADDON_PT_Generate,
    WM_OT_CreatePath,
    WM_OT_RemovePath,
    WM_OT_RemoveSubPaths,
    WM_OT_StoreData
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.path_count = bpy.props.IntProperty(default=0)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.path_count

if __name__ == "__main__":
    register()
