import bpy

# Panel de la UI en la barra lateral
class ApplyPanel(bpy.types.Panel):
    bl_label = "Apply"
    bl_idname = "PT_Apply"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Apply'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.separate_by_loose_parts", text="Separate by Loose Parts")
        layout.operator("object.separate_by_material", text="Separate by Material")
        layout.operator("object.apply_all_modifiers", text="Apply Modifiers")
        layout.operator("object.join", text="Join")
        layout.operator("object.add_to_collection", text="Add to Collection")

# 🔹 Separar por partes sueltas
class OBJECT_OT_separate_by_loose_parts(bpy.types.Operator):
    bl_idname = "object.separate_by_loose_parts"
    bl_label = "Separate by Loose Parts"
    
    def execute(self, context):
        obj = context.object
        if obj and obj.type == 'MESH':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.separate(type='LOOSE')
            bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'INFO'}, "Separación por partes sueltas completada.")
        else:
            self.report({'WARNING'}, "Seleccione un objeto de tipo MESH.")
        
        return {'FINISHED'}

# 🔹 Separar por material
class OBJECT_OT_separate_by_material(bpy.types.Operator):
    bl_idname = "object.separate_by_material"
    bl_label = "Separate by Material"
    
    def execute(self, context):
        obj = context.object
        if obj and obj.type == 'MESH':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.separate(type='MATERIAL')
            bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'INFO'}, "Separación por material completada.")
        else:
            self.report({'WARNING'}, "Seleccione un objeto de tipo MESH.")

        return {'FINISHED'}

# 🔹 Aplicar modificadores a todos los objetos en la escena
class OBJECT_OT_apply_all_modifiers(bpy.types.Operator):
    bl_idname = "object.apply_all_modifiers"
    bl_label = "Apply Modifiers"
    
    def execute(self, context):
        """Aplica todos los modificadores a los objetos visibles en la escena."""
        mesh_objects = [obj for obj in bpy.context.view_layer.objects if obj.type == 'MESH' and obj.visible_get()]
        count = 0  # Contador de modificadores aplicados

        for obj in mesh_objects:
            bpy.context.view_layer.objects.active = obj  # Establecer como activo
            for mod in obj.modifiers:
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                    count += 1
                except RuntimeError:
                    self.report({'WARNING'}, f"No se pudo aplicar el modificador '{mod.name}' en '{obj.name}'")

        self.report({'INFO'}, f"Se aplicaron {count} modificadores a los objetos visibles.")
        return {'FINISHED'}

# 🔹 Agregar objetos seleccionados a una nueva colección
class OBJECT_OT_add_to_collection(bpy.types.Operator):
    bl_idname = "object.add_to_collection"
    bl_label = "Add to Collection"

    def execute(self, context):
        """Crea una nueva colección y mueve los objetos seleccionados a ella."""
        new_collection = bpy.data.collections.new("New Collection")
        bpy.context.scene.collection.children.link(new_collection)

        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No hay objetos seleccionados.")
            return {'CANCELLED'}

        for obj in selected_objects:
            for col in obj.users_collection:
                col.objects.unlink(obj)  # Remueve el objeto de sus colecciones actuales
            new_collection.objects.link(obj)  # Agregar a la nueva colección

        self.report({'INFO'}, "Objetos movidos a la nueva colección correctamente.")
        return {'FINISHED'}

# 🔹 Registrar las clases
def register():
    bpy.utils.register_class(ApplyPanel)
    bpy.utils.register_class(OBJECT_OT_separate_by_loose_parts)
    bpy.utils.register_class(OBJECT_OT_separate_by_material)
    bpy.utils.register_class(OBJECT_OT_apply_all_modifiers)
    bpy.utils.register_class(OBJECT_OT_add_to_collection)

# 🔹 Desregistrar las clases
def unregister():
    bpy.utils.unregister_class(ApplyPanel)
    bpy.utils.unregister_class(OBJECT_OT_separate_by_loose_parts)
    bpy.utils.unregister_class(OBJECT_OT_separate_by_material)
    bpy.utils.unregister_class(OBJECT_OT_apply_all_modifiers)
    bpy.utils.unregister_class(OBJECT_OT_add_to_collection)

# Si el script se ejecuta directamente, registrar las clases
if __name__ == "__main__":
    register()
