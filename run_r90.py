import bpy
import os

# Function to run the script
def run_script(script_name):
    try:
        # Path of the scripts
        path = bpy.context.scene.script_folder
        full_path = os.path.join(path, script_name)

        # Check if the file exists
        if os.path.isfile(full_path):
            bpy.ops.script.python_file_run(filepath=full_path)  # Use bpy to run the script
            print(f"Script {script_name} executed successfully.")
        else:
            print(f"The file {script_name} does not exist at the specified path.")
    except Exception as e:
        print(f"Error executing the script: {e}")

# Define the operator that handles key input
class SimpleOperator(bpy.types.Operator):
    bl_idname = "object.run_script"
    bl_label = "Run Script"

    # Execute the action based on the pressed key
    def execute(self, context):
        # Check the selected option in the menu
        if bpy.context.scene.script_action == "rectangle":
            run_script("R90rectangle.py")
        elif bpy.context.scene.script_action == "quadblock":
            run_script("R90.py")
        return {'FINISHED'}

# Define the user interface panel
class SimplePanel(bpy.types.Panel):
    bl_label = "Run Python Script"
    bl_idname = "PT_SimplePanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout

        # Input field for the scripts path
        layout.prop(context.scene, "script_folder")
        
        # Menu to select the action
        layout.prop(context.scene, "script_action", text="Action")

        # Button to run the script
        layout.operator("object.run_script", text="Run Script")

# Register custom properties
def register():
    bpy.types.Scene.script_folder = bpy.props.StringProperty(
        name="Scripts Path",
        description="Specifies the path of the scripts",
        subtype='DIR_PATH'
    )
    bpy.types.Scene.script_action = bpy.props.EnumProperty(
        name="Action",
        description="Choose which script to execute",
        items=[("rectangle", "Rectangle", ""),
               ("quadblock", "QuadBlock", "")]
    )

    bpy.utils.register_class(SimpleOperator)
    bpy.utils.register_class(SimplePanel)

def unregister():
    bpy.utils.unregister_class(SimpleOperator)
    bpy.utils.unregister_class(SimplePanel)
    del bpy.types.Scene.script_folder
    del bpy.types.Scene.script_action

if __name__ == "__main__":
    register()
