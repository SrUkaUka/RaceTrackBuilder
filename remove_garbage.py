import bpy

# Function to clean "garbage" objects in the scene
def clean_objects():
    """
    This function iterates through all objects in the scene and checks if they are of type 'MESH' and visible.
    If the object has no vertices (empty) or has disconnected geometry, it will be removed from the scene.
    """
    for obj in bpy.context.scene.objects:
        # Ensure the object is of type 'MESH' and is visible in the current view layer
        if obj.type == 'MESH' and obj.visible_get():
            bpy.context.view_layer.objects.active = obj

            # Remove empty objects (objects with no vertices)
            if len(obj.data.vertices) == 0:
                print(f"Removing empty object: {obj.name}")
                bpy.data.objects.remove(obj)
            # Remove objects without connected geometry (no selected vertices or edges)
            elif not any([v.select for v in obj.data.vertices]):
                print(f"Removing object with no connected geometry: {obj.name}")
                bpy.data.objects.remove(obj)

# Create an operator in Blender to execute the cleaning
class OBJECT_OT_clean_objects(bpy.types.Operator):
    """
    This operator removes 'garbage' objects from the scene. Garbage objects are those of type 'MESH' 
    that are either empty (no vertices) or have disconnected geometry (no selected vertices or edges).
    """
    bl_idname = "object.clean_objects"  # The operator's unique identifier
    bl_label = "Clean Objects"  # The label shown in the UI for the operator
    bl_options = {'REGISTER', 'UNDO'}  # Allows for undo/redo functionality

    def execute(self, context):
        """
        This method is called when the operator is triggered. It invokes the `clean_objects` function 
        to clean up the scene, removing objects that are empty or have no connected geometry.
        
        Returns {'FINISHED'} to indicate that the operation was successful.
        """
        clean_objects()  # Call the function to clean up the objects in the scene
        
        # Return 'FINISHED' to indicate that the operator has finished
        return {'FINISHED'}

# Add a button in the tools panel to trigger the operator
class VIEW3D_PT_clean_objects_panel(bpy.types.Panel):
    """
    This panel adds a button in the 3D View's Tool tab that triggers the object cleaning operation.
    """
    bl_label = "Clean Objects"  # The label for the panel
    bl_idname = "VIEW3D_PT_clean_objects"  # The panel's unique identifier
    bl_space_type = 'VIEW_3D'  # The type of space the panel will appear in (3D View)
    bl_region_type = 'UI'  # The region of the space (UI panel)
    bl_category = 'Tool'  # The tab category where the panel will appear

    def draw(self, context):
        """
        Draws the panel layout with a button that triggers the operator when clicked.
        """
        layout = self.layout  # Get the panel layout

        # Add a button that will call the clean_objects operator when pressed
        layout.operator("object.clean_objects", text="Clean Garbage Objects")

# Register the classes
def register():
    bpy.utils.register_class(OBJECT_OT_clean_objects)  # Register the operator class
    bpy.utils.register_class(VIEW3D_PT_clean_objects_panel)  # Register the panel class

# Unregister the classes
def unregister():
    bpy.utils.unregister_class(OBJECT_OT_clean_objects)  # Unregister the operator class
    bpy.utils.unregister_class(VIEW3D_PT_clean_objects_panel)  # Unregister the panel class

# Ensure the script runs by registering the classes when the script is executed
if __name__ == "__main__":
    register()
