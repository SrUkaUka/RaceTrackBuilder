import bpy
import json
import bpy_extras.io_utils

global_material_data = {}

class MATERIAL_EDIT_PT_Panel(bpy.types.Panel):
    """Panel personalizado en la pestaña de materiales"""
    bl_label = "Material Edit"
    bl_idname = "MATERIAL_EDIT_PT_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        mat = obj.active_material if obj else None

        if mat:
            # Se eliminó la propiedad "texture_id"
            layout.prop(mat, "terrain_type", text="Terrain Types")

            layout.label(text="Quadflags:")
            for flag in mat.quadflags:
                layout.prop(mat, f"quadflags_{flag}", text=flag.replace("_", " "))

            layout.label(text=f"Quadflag Index: {mat.quadflag_index}")

            layout.label(text="Draw Flags:")
            layout.prop(mat, "double_sided", text="Double Sided")
            layout.prop(mat, "checkpoint", text="Checkpoint")

            layout.operator("material.kill_plane", text="Kill Plane", icon="CANCEL")

        layout.operator("material.store_data", text="Store Data", icon="FILE_TICK")
        layout.operator("material.export_json", text="Export Material Preset", icon="EXPORT")
        layout.operator("material.apply_settings", text="Apply Settings to Materials", icon="FILE_REFRESH")


class MATERIAL_OT_ExportJSON(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Exporta los datos de materiales como JSON"""
    bl_idname = "material.export_json"
    bl_label = "Export Material Preset"

    filename_ext = ".json"

    def execute(self, context):
        global global_material_data

        if not global_material_data:
            self.report({'WARNING'}, "No data to export. Please store data first!")
            return {'CANCELLED'}

        export_data = {}

        for mat_name, mat_info in global_material_data.items():
            export_data[f"{mat_name}_checkpoint"] = mat_info["Checkpoint"]
            export_data[f"{mat_name}_drawflags"] = mat_info["Double Sided"]
            export_data[f"{mat_name}_quadflags"] = mat_info["Quadflag Index"]
            export_data[f"{mat_name}_terrain"] = mat_info["Terrain Type"].capitalize()  # Primera letra en mayúscula

        export_data["header"] = 3  # Se fuerza a que siempre sea 3
        export_data["materials"] = list(global_material_data.keys())

        with open(self.filepath, "w") as json_file:
            json.dump(export_data, json_file, indent=4)

        self.report({'INFO'}, f"Material preset exported: {self.filepath}")
        return {'FINISHED'}


class MATERIAL_OT_KillPlane(bpy.types.Operator):
    """Acción para el botón Kill Plane"""
    bl_idname = "material.kill_plane"
    bl_label = "Kill Plane"

    def execute(self, context):
        mat = context.object.active_material
        if mat:
            kill_plane_flags = {"Wall", "Out_of_Bounds", "Mask_Grab", "No_Collision", "Invisible_Trigger"}
            # Activa solo los flags de kill plane y desactiva el resto
            for flag in mat.quadflags:
                setattr(mat, f"quadflags_{flag}", flag in kill_plane_flags)

            update_quadflag_index(mat, context)
            self.report({'INFO'}, "Kill Plane applied!")
            
        return {'FINISHED'}


class MATERIAL_OT_StoreData(bpy.types.Operator):
    """Guarda los datos de los materiales en uso en una variable global"""
    bl_idname = "material.store_data"
    bl_label = "Store Data"

    def execute(self, context):
        global global_material_data
        global_material_data.clear()

        used_materials = set()
        for obj in bpy.data.objects:
            if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
                for slot in obj.material_slots:
                    if slot.material:
                        used_materials.add(slot.material)

        for mat in used_materials:
            global_material_data[mat.name] = {
                "Terrain Type": mat.terrain_type,
                "Quadflag Index": mat.quadflag_index,
                "Double Sided": mat.double_sided,
                "Checkpoint": mat.checkpoint,
            }

        self.report({'INFO'}, f"Stored {len(global_material_data)} materials!")
        print("Stored Material Data:", json.dumps(global_material_data, indent=4))

        return {'FINISHED'}


# Clase auxiliar para la lista de selección de materiales
class MaterialSelectionItem(bpy.types.PropertyGroup):
    material_name: bpy.props.StringProperty(name="Material Name")
    select: bpy.props.BoolProperty(name="Apply", default=False)


class MATERIAL_OT_ApplySettings(bpy.types.Operator):
    """Muestra una lista de materiales para aplicar la configuración del material activo"""
    bl_idname = "material.apply_settings"
    bl_label = "Apply Settings to Materials"
    
    # Colección de materiales para seleccionar
    materials: bpy.props.CollectionProperty(type=MaterialSelectionItem)
    material_index: bpy.props.IntProperty(name="Index", default=0)
    
    def invoke(self, context, event):
        # Limpia la colección
        self.materials.clear()
        
        # Recopila los materiales que están en uso en la escena
        used_materials = set()
        for obj in bpy.data.objects:
            if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
                for slot in obj.material_slots:
                    if slot.material:
                        used_materials.add(slot.material)
                        
        # Agrega a la colección solo los materiales en uso
        for mat in used_materials:
            item = self.materials.add()
            item.material_name = mat.name
            item.select = False
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Seleccione los materiales a los que aplicar la configuración:")
        for item in self.materials:
            row = box.row()
            row.prop(item, "select", text="")
            row.label(text=item.material_name)
    
    def execute(self, context):
        active_mat = context.object.active_material
        if not active_mat:
            self.report({'WARNING'}, "No hay material activo en el objeto!")
            return {'CANCELLED'}
        
        # Recorre la lista de materiales seleccionados y aplica las propiedades del material activo
        for item in self.materials:
            if item.select:
                target_mat = bpy.data.materials.get(item.material_name)
                if target_mat:
                    # Copia las propiedades personalizadas
                    target_mat.terrain_type = active_mat.terrain_type
                    target_mat.quadflag_index = active_mat.quadflag_index
                    target_mat.double_sided = active_mat.double_sided
                    target_mat.checkpoint = active_mat.checkpoint
                    # Copia cada uno de los quadflags
                    for flag in active_mat.quadflags:
                        setattr(target_mat, f"quadflags_{flag}", getattr(active_mat, f"quadflags_{flag}", False))
        self.report({'INFO'}, "Configuración aplicada a los materiales seleccionados.")
        return {'FINISHED'}


def update_quadflag_index(self, context):
    """Calcula el índice total basado en los checkboxes activados"""
    quadflag_values = {
        "Invisible": 1,  # Se cambia de 6144 a 1
        "Trigger_Script": 64,
        "Moon_Gravity": 2,
        "Reflection": 4,
        "Reverb": 128,
        "Wall": 8192,
        "Kickers": 8,
        "Out_of_Bounds": 16,
        "Never_Used": 32,
        "Kickers_Two": 256,
        "Mask_Grab": 512,
        "Tiger_Temple_Door": 1024,
        "Collision_Trigger": 2048,
        "Ground": 4096,
        "No_Collision": 16384,
        "Invisible_Trigger": 32768
    }

    mat = context.object.active_material
    if mat:
        total_index = sum(value for key, value in quadflag_values.items() if getattr(mat, f"quadflags_{key}", False))
        mat.quadflag_index = total_index


def register():
    # Se eliminó la propiedad "texture_id"
    bpy.types.Material.terrain_type = bpy.props.EnumProperty(
        name="Terrain Types",
        items=[('ASPHALT', "Asphalt", ""), ('TRACK', "Track", ""), ('ICE', "Ice", ""), ('WATER', "Water", ""),
               ('WOOD', "Wood", ""), ('DIRT', "Dirt", ""), ('GRASS', "Grass", ""), ('ICY_ROAD', "Icy Road", ""),
               ('STONE', "Stone", ""), ('SNOW', "Snow", ""), ('NONE', "None", ""), ('HARD_PACK', "Hard Pack", ""),
               ('SIDE_SLIP', "Side Slip", ""), ('METAL', "Metal", ""), ('FAST_WATER', "Fast Water", ""),
               ('MUD', "Mud", ""), ('OCEAN_ASPHALT', "Ocean Asphalt", ""), ('RIVER_ASPHALT', "River Asphalt", ""),
               ('STEAM_ASPHALT', "Steam Asphalt", ""), ('SLOW_GRASS', "Slow Grass", ""), ('SLOW_DIRT', "Slow Dirt", "")]
    )

    bpy.types.Material.quadflags = ["Invisible", "Trigger_Script", "Moon_Gravity", "Reflection", "Reverb", "Wall",
                                    "Kickers", "Out_of_Bounds", "Never_Used", "Kickers_Two", "Mask_Grab",
                                    "Tiger_Temple_Door", "Collision_Trigger", "Ground", "No_Collision",
                                    "Invisible_Trigger"]

    for flag in bpy.types.Material.quadflags:
        setattr(bpy.types.Material, f"quadflags_{flag}",
                bpy.props.BoolProperty(name=flag.replace("_", " "), update=update_quadflag_index))

    bpy.types.Material.quadflag_index = bpy.props.IntProperty(name="Quadflag Index", default=0)
    bpy.types.Material.double_sided = bpy.props.BoolProperty(name="Double Sided", default=False)
    bpy.types.Material.checkpoint = bpy.props.BoolProperty(name="Checkpoint", default=False)

    bpy.utils.register_class(MaterialSelectionItem)
    bpy.utils.register_class(MATERIAL_EDIT_PT_Panel)
    bpy.utils.register_class(MATERIAL_OT_KillPlane)
    bpy.utils.register_class(MATERIAL_OT_StoreData)
    bpy.utils.register_class(MATERIAL_OT_ExportJSON)
    bpy.utils.register_class(MATERIAL_OT_ApplySettings)


def unregister():
    bpy.utils.unregister_class(MATERIAL_OT_ApplySettings)
    bpy.utils.unregister_class(MaterialSelectionItem)
    bpy.utils.unregister_class(MATERIAL_EDIT_PT_Panel)
    bpy.utils.unregister_class(MATERIAL_OT_KillPlane)
    bpy.utils.unregister_class(MATERIAL_OT_StoreData)
    bpy.utils.unregister_class(MATERIAL_OT_ExportJSON)


if __name__ == "__main__":
    register()
