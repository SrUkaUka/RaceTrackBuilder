import bpy

# Panel class for displaying the UI
class ApplyPanel(bpy.types.Panel):
    bl_label = "Apply"
    bl_idname = "PT_Apply"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Apply'  # Adds the panel to the Tools tab

    def draw(self, context):
        layout = self.layout

        # Button: Separate by Loose Parts
        layout.operator("object.separate_by_loose_parts", text="Separate by Loose Parts")
        
        # Button: Separate by Material
        layout.operator("object.separate_by_material", text="Separate by Material")
        
        # Button: Apply Modifiers
        layout.operator("object.apply_all_modifiers", text="Apply Modifiers")
        
        # Button: Join
        layout.operator("object.join", text="Join")

        # Button: Add to Collection
        layout.operator("object.add_to_collection", text="Add to Collection")


# Operator to separate the object by loose parts
class OBJECT_OT_separate_by_loose_parts(bpy.types.Operator):
    bl_idname = "object.separate_by_loose_parts"
    bl_label = "Separate by Loose Parts"
    
    def execute(self, context):
        """Separates the selected object into parts based on loose geometry."""
        
        # Ensure we are in Object Mode before switching to Edit Mode
        if bpy.context.object.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        # Select all geometry in Edit Mode
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Execute separation by loose parts
        bpy.ops.mesh.separate(type='LOOSE')
        
        # Return to Object Mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        return {'FINISHED'}


# Operator to separate the object by material
class OBJECT_OT_separate_by_material(bpy.types.Operator):
    bl_idname = "object.separate_by_material"
    bl_label = "Separate by Material"
    
    def execute(self, context):
        """Separates the selected object into parts based on materials."""
        
        # Ensure we're in Edit Mode
        if bpy.context.object.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        
        # Select all geometry
        bpy.ops.mesh.select_all(action='SELECT')  # Select all geometry
        
        # Execute separation by material
        bpy.ops.mesh.separate(type='MATERIAL')
        
        # Return to Object Mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        return {'FINISHED'}


# Operator to apply all modifiers to all objects in the scene
class OBJECT_OT_apply_all_modifiers(bpy.types.Operator):
    bl_idname = "object.apply_all_modifiers"
    bl_label = "Apply Modifiers"
    
    def execute(self, context):
        """Applies all modifiers to all objects in the scene."""
        # Create a list of mesh objects to apply modifiers to
        mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
        
        # Iterate through mesh objects and apply modifiers
        for obj in mesh_objects:
            bpy.context.view_layer.objects.active = obj  # Set active object
            for mod in obj.modifiers:
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except RuntimeError:
                    self.report({'WARNING'}, f"Could not apply modifier '{mod.name}'")
        
        self.report({'INFO'}, "Modifiers applied to all objects in the scene.")
        return {'FINISHED'}


# Operator to add selected objects to a new collection
class OBJECT_OT_add_to_collection(bpy.types.Operator):
    bl_idname = "object.add_to_collection"
    bl_label = "Add to Collection"
    
    def execute(self, context):
        """Crea una nueva colección y desplaza los objetos seleccionados a ella, 
        incluyendo objetos dentro de colecciones, sin duplicarlos."""
        
        # Crear una nueva colección
        new_collection = bpy.data.collections.new("New Collection")
        bpy.context.scene.collection.children.link(new_collection)

        # Función para mover objetos a la nueva colección
        def move_to_new_collection(obj):
            # Solo mover objetos tipo 'MESH' o colecciones
            if obj.type == 'MESH':
                # Verificar si el objeto ya está en la nueva colección
                if new_collection not in obj.users_collection:
                    # Desvincular el objeto de las colecciones actuales y vincularlo a la nueva colección
                    for col in obj.users_collection:
                        col.objects.unlink(obj)
                    new_collection.objects.link(obj)
            elif obj.type == 'COLLECTION':
                # Si el objeto es una colección, mover todos los objetos dentro de esa colección
                for sub_obj in obj.objects:
                    move_to_new_collection(sub_obj)

        # Iterar sobre los objetos seleccionados en la escena
        for obj in context.view_layer.objects.selected:
            move_to_new_collection(obj)

        self.report({'INFO'}, "Los objetos seleccionados y colecciones se movieron a la nueva colección.")
        return {'FINISHED'}


# Registering all classes
def register():
    bpy.utils.register_class(ApplyPanel)
    bpy.utils.register_class(OBJECT_OT_separate_by_loose_parts)
    bpy.utils.register_class(OBJECT_OT_separate_by_material)
    bpy.utils.register_class(OBJECT_OT_apply_all_modifiers)
    bpy.utils.register_class(OBJECT_OT_add_to_collection)

# Unregistering all classes
def unregister():
    bpy.utils.unregister_class(ApplyPanel)
    bpy.utils.unregister_class(OBJECT_OT_separate_by_loose_parts)
    bpy.utils.unregister_class(OBJECT_OT_separate_by_material)
    bpy.utils.unregister_class(OBJECT_OT_apply_all_modifiers)
    bpy.utils.unregister_class(OBJECT_OT_add_to_collection)


# If the script is run directly, register the operators
if __name__ == "__main__":
    register()
