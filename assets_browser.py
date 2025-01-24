import bpy
import os

def normalize_path(path):
    """Converts backslashes to forward slashes for compatibility."""
    return path.replace("\\", "/")

class ConfigureUserLibraryOperator(bpy.types.Operator):
    """Configures the specified path as a User Library in Blender preferences."""
    bl_idname = "object.configure_user_library"
    bl_label = "Add Path as User Library"

    def execute(self, context):
        path = normalize_path(context.scene.assets_path)

        # Validate that the path exists
        if not os.path.exists(path):
            self.report({'ERROR'}, "The specified path does not exist.")
            return {'CANCELLED'}

        # If it's a file, get its containing folder
        if os.path.isfile(path):
            path = os.path.dirname(path)

        # Check if it's already configured as a User Library
        user_libraries = bpy.context.preferences.filepaths.asset_libraries
        if any(lib.path == path for lib in user_libraries):
            self.report({'INFO'}, "The path is already configured as a User Library.")
            return {'FINISHED'}

        # Add the new User Library
        new_library = user_libraries.new(name=os.path.basename(path))
        new_library.path = path
        self.report({'INFO'}, f"Path '{path}' added as a User Library.")

        return {'FINISHED'}

class OpenAssetBrowserOperator(bpy.types.Operator):
    """Opens the Asset Browser in a new area at the bottom of the screen."""
    bl_idname = "object.open_asset_browser"
    bl_label = "Open Asset Browser"

    def execute(self, context):
        # Search for an area of type 'VIEW_3D'
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                # Split the current area
                bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.5)

                # Change the newly created area to Asset Browser
                new_area = bpy.context.screen.areas[-1]
                new_area.type = 'FILE_BROWSER'
                new_area.ui_type = 'ASSETS'

                self.report({'INFO'}, "Opened the Asset Browser at the bottom.")
                return {'FINISHED'}

        self.report({'WARNING'}, "No suitable area found to open the Asset Browser.")
        return {'CANCELLED'}

class AssetsPanel(bpy.types.Panel):
    """Panel to configure User Libraries."""
    bl_label = "User Libraries Management"
    bl_idname = "VIEW3D_PT_user_libraries"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assets'

    def draw(self, context):
        layout = self.layout

        # Text field for the assets path
        layout.prop(context.scene, "assets_path", text="Assets Path")
        layout.operator("object.configure_user_library", text="Add as User Library", icon='FILE_FOLDER')
        layout.operator("object.open_asset_browser", text="Open Asset Browser", icon='ASSET_MANAGER')

def register():
    bpy.utils.register_class(ConfigureUserLibraryOperator)
    bpy.utils.register_class(OpenAssetBrowserOperator)
    bpy.utils.register_class(AssetsPanel)

    bpy.types.Scene.assets_path = bpy.props.StringProperty(
        name="Assets Path",
        description="Path to a .blend file or folder containing the assets",
        default="C:/Users/YourUser/assets.blend",
    )

def unregister():
    bpy.utils.unregister_class(ConfigureUserLibraryOperator)
    bpy.utils.unregister_class(OpenAssetBrowserOperator)
    bpy.utils.unregister_class(AssetsPanel)

    del bpy.types.Scene.assets_path

if __name__ == "__main__":
    register()
