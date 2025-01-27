import bpy

# Función para habilitar el proporcional editing
def enable_proportional_editing(self, context):
    selected_objects = bpy.context.selected_objects
    
    # Asegurarse de que hay objetos seleccionados
    if selected_objects:
        # Cambiar a modo objeto
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Unir objetos seleccionados
        bpy.ops.object.join()
        
        # Activar el proporcional editing para objetos seleccionados
        bpy.context.scene.tool_settings.use_proportional_edit = True
        
        # Cambiar a modo de edición
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Cambiar al modo de selección de caras
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

# Función para deshabilitar el proporcional editing
def disable_proportional_editing(self, context):
    # Cambiar a modo objeto antes de separar
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Separar por partes sueltas
    bpy.ops.mesh.separate(type='LOOSE')
    
    # Establecer el origen a la geometría
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    
    # Desactivar el proporcional editing
    bpy.context.scene.tool_settings.use_proportional_edit = False
    
    # Volver al modo objeto
    bpy.ops.object.mode_set(mode='OBJECT')

# Crear un panel para los botones en la pestaña 'Tools'
class SimplePanel(bpy.types.Panel):
    bl_label = "Proportional Editing Tool"
    bl_idname = "PT_ProportionalEditing"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout

        # Botón para habilitar proporcional editing
        layout.operator("object.enable_proportional_editing", text="Enable Proportional Editing to Selected")

        # Botón para deshabilitar proporcional editing
        layout.operator("object.disable_proportional_editing", text="Finish Proportional Editing")

# Operadores para activar y desactivar proporcional editing
class EnableProportionalEditingOperator(bpy.types.Operator):
    bl_idname = "object.enable_proportional_editing"
    bl_label = "Enable Proportional Editing to Selected"
    
    def execute(self, context):
        enable_proportional_editing(self, context)
        return {'FINISHED'}

class DisableProportionalEditingOperator(bpy.types.Operator):
    bl_idname = "object.disable_proportional_editing"
    bl_label = "Finish Proportional Editing"
    
    def execute(self, context):
        disable_proportional_editing(self, context)
        return {'FINISHED'}

# Registrar los operadores y el panel
def register():
    bpy.utils.register_class(EnableProportionalEditingOperator)
    bpy.utils.register_class(DisableProportionalEditingOperator)
    bpy.utils.register_class(SimplePanel)

def unregister():
    bpy.utils.unregister_class(EnableProportionalEditingOperator)
    bpy.utils.unregister_class(DisableProportionalEditingOperator)
    bpy.utils.unregister_class(SimplePanel)

if __name__ == "__main__":
    register()
