import bpy
import json
import os
from collections import OrderedDict  # ✅ Para mantener el orden correcto en el JSON


class MyProperties(bpy.types.PropertyGroup):
    def update_none(self, context):
        """Si se activa 'None', desactiva las demás opciones"""
        if self.none:
            self.turbo_pad = False
            self.super_turbo_pad = False

    def update_turbo_pad(self, context):
        """Si se activa 'Turbo Pad', desactiva las demás opciones"""
        if self.turbo_pad:
            self.none = False
            self.super_turbo_pad = False

    def update_super_turbo_pad(self, context):
        """Si se activa 'Super Turbo Pad', desactiva las demás opciones"""
        if self.super_turbo_pad:
            self.none = False
            self.turbo_pad = False

    none: bpy.props.BoolProperty(
        name="None",
        default=True,
        description="Desactiva el turbo",
        update=update_none
    )
    turbo_pad: bpy.props.BoolProperty(
        name="Turbo Pad",
        default=False,
        description="Activa el modo Turbo Pad",
        update=update_turbo_pad
    )
    super_turbo_pad: bpy.props.BoolProperty(
        name="Super Turbo Pad",
        default=False,
        description="Activa el modo Super Turbo Pad",
        update=update_super_turbo_pad
    )


class OBJECT_PT_turbo_panel(bpy.types.Panel):
    bl_label = "Turbo Settings"
    bl_idname = "OBJECT_PT_turbo_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj and obj.my_props:
            props = obj.my_props
            layout.prop(props, "none", toggle=True, text="None")
            layout.prop(props, "turbo_pad", toggle=True, text="Turbo Pad")
            layout.prop(props, "super_turbo_pad", toggle=True, text="Super Turbo Pad")

        layout.operator("export.turbo_preset", text="Export Preset", icon="EXPORT")


class EXPORT_OT_turbo_preset(bpy.types.Operator):
    """Exporta la configuración de turbo a un archivo JSON"""
    bl_idname = "export.turbo_preset"
    bl_label = "Export Turbo Preset"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="untitled.json")  # ✅ Se sugiere "untitled.json"

    def execute(self, context):
        turbo_data = OrderedDict()  # ✅ Usamos OrderedDict para mantener el orden exacto
        turbopads_list = []

        for obj in bpy.data.objects:
            if hasattr(obj, "my_props") and obj.my_props:
                props = obj.my_props
                if props.super_turbo_pad:
                    turbo_data[f"{obj.name}_trigger"] = 2  # ✅ Modo 2 para Super Turbo
                    turbopads_list.append(obj.name)
                elif props.turbo_pad:
                    turbo_data[f"{obj.name}_trigger"] = 1  # ✅ Modo 1 para Turbo
                    turbopads_list.append(obj.name)

        # ✅ Agregamos "header" y "turbopads" en el orden correcto
        turbo_data["header"] = 4
        turbo_data["turbopads"] = turbopads_list

        # ✅ Asegurar que la extensión sea ".json"
        if not self.filepath.lower().endswith(".json"):
            self.filepath += ".json"

        try:
            with open(self.filepath, "w") as f:
                json.dump(turbo_data, f, indent=4)
            self.report({'INFO'}, f"Preset exportado en {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Error al guardar: {e}")

        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = bpy.path.abspath("//untitled.json")  # ✅ Ahora el nombre sugerido es "untitled.json"
        context.window_manager.fileselect_add(self)  # ✅ Abre el explorador de archivos con el nombre sugerido
        return {'RUNNING_MODAL'}


def register():
    try:
        unregister()  # Evita errores al registrar
    except Exception:
        pass

    bpy.utils.register_class(MyProperties)
    bpy.utils.register_class(OBJECT_PT_turbo_panel)
    bpy.utils.register_class(EXPORT_OT_turbo_preset)
    bpy.types.Object.my_props = bpy.props.PointerProperty(type=MyProperties)


def unregister():
    bpy.utils.unregister_class(MyProperties)
    bpy.utils.unregister_class(OBJECT_PT_turbo_panel)
    bpy.utils.unregister_class(EXPORT_OT_turbo_preset)
    del bpy.types.Object.my_props


if __name__ == "__main__":
    register()
