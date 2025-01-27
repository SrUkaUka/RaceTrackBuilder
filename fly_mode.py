import bpy

# Add properties to the scene for checkmarks
def init_scene_properties():
    bpy.types.Scene.accelerate_enabled = bpy.props.BoolProperty(
        name="Accelerate",
        description="Enable faster movement in Walk/Fly mode",
        default=False
    )
    bpy.types.Scene.gravity_enabled = bpy.props.BoolProperty(
        name="Gravity",
        description="Enable gravity in Walk mode",
        default=False
    )

def clear_scene_properties():
    del bpy.types.Scene.accelerate_enabled
    del bpy.types.Scene.gravity_enabled

# Function to maximize the screen without hiding the panels
def maximize_screen():
    bpy.ops.screen.screen_full_area(use_hide_panels=False)  # Only maximizes, does not hide the panels
    return None

# Function to activate Walk Mode with increased speed
def activate_walk_mode(context):
    """
    Activates the Walk Mode with configurable speed and gravity options.
    - Adjusts the walk speed based on the "Accelerate" property.
    - Enables or disables gravity based on the "Gravity" property.
    """
    # Configure Walk mode properties
    walk_settings = context.preferences.inputs.walk_navigation
    walk_settings.use_gravity = context.scene.gravity_enabled
    walk_settings.walk_speed = 50.0 if context.scene.accelerate_enabled else 35.0  # Increased base speed
    walk_settings.walk_speed_factor = 50.0 if context.scene.accelerate_enabled else 35.0  # High acceleration factor
    bpy.ops.view3d.walk('INVOKE_DEFAULT')
    
    # Hide panels and overlays automatically when activating Walk Mode
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'UI':
                    area.ui_type = 'VIEW_3D'  # Change view to 3D
                    break
    
    bpy.context.space_data.show_region_ui = False  # Hide the UI region
    bpy.context.space_data.overlay.show_overlays = False  # Disable overlays (tools, grids, etc.)

# Function to activate Fly Mode with increased speed
def activate_fly_mode(context):
    """
    Activates the Fly Mode with configurable speed options.
    - Adjusts the fly speed based on the "Accelerate" property.
    - This mode does not use gravity by default.
    """
    # Configure Fly mode properties
    fly_settings = context.preferences.inputs.walk_navigation
    fly_settings.walk_speed = 15.0 if context.scene.accelerate_enabled else 5.0  # Increased base speed
    fly_settings.walk_speed_factor = 15.0 if context.scene.accelerate_enabled else 5.0  # High acceleration factor
    bpy.ops.view3d.fly('INVOKE_DEFAULT')
    
    # Hide panels and overlays automatically when activating Fly Mode
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'UI':
                    area.ui_type = 'VIEW_3D'  # Change view to 3D
                    break
    
    bpy.context.space_data.show_region_ui = False  # Hide the UI region
    bpy.context.space_data.overlay.show_overlays = False  # Disable overlays (tools, grids, etc.)

# Operator for Walk Mode
class WalkModeOperator(bpy.types.Operator):
    """
    Operator to activate the Walk Mode in the 3D Viewport.
    - Adjusts the walk speed and gravity according to the scene's properties.
    """
    bl_idname = "view3d.walk_mode_operator"
    bl_label = "Activate Walk Mode"

    def execute(self, context):
        activate_walk_mode(context)  # Calls the function to activate Walk Mode
        return {'FINISHED'}

# Operator for Fly Mode
class FlyModeOperator(bpy.types.Operator):
    """
    Operator to activate the Fly Mode in the 3D Viewport.
    - Adjusts the fly speed based on the scene's properties.
    """
    bl_idname = "view3d.fly_mode_operator"
    bl_label = "Activate Fly Mode"

    def execute(self, context):
        activate_fly_mode(context)  # Calls the function to activate Fly Mode
        return {'FINISHED'}

# Operator to maximize the screen without hiding the panels
class MaximizeScreenOperator(bpy.types.Operator):
    """
    Operator to maximize the 3D Viewport area.
    - The screen is maximized without hiding any panels or UI regions.
    """
    bl_idname = "screen.maximize_area"
    bl_label = "Maximize Screen"

    def execute(self, context):
        maximize_screen()  # Calls the function to maximize the screen
        return {'FINISHED'}

# Panel with buttons and checkmarks
class WalkFlyModePanel(bpy.types.Panel):
    """
    Panel for controlling the Walk and Fly modes in Blender's 3D Viewport.
    - Contains buttons to activate Walk and Fly modes.
    - Includes checkmarks for enabling/disabling acceleration and gravity.
    """
    bl_label = "Walk & Fly Mode Panel"
    bl_idname = "VIEW3D_PT_walk_fly_mode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'  # Changed from 'Tools' to 'Tool'

    def draw(self, context):
        layout = self.layout
        
        # Checkmarks for configuration
        layout.prop(context.scene, "accelerate_enabled", text="Accelerate")
        layout.prop(context.scene, "gravity_enabled", text="Gravity (Walk Mode)")
        
        # Buttons to activate the modes
        layout.operator("view3d.walk_mode_operator", text="Activate Walk Mode")
        layout.operator("view3d.fly_mode_operator", text="Activate Fly Mode")
        
        # Button to maximize the screen without hiding the panels
        layout.operator("screen.maximize_area", text="Maximize Screen")

# Registration
def register():
    init_scene_properties()
    bpy.utils.register_class(WalkModeOperator)
    bpy.utils.register_class(FlyModeOperator)
    bpy.utils.register_class(MaximizeScreenOperator)
    bpy.utils.register_class(WalkFlyModePanel)

def unregister():
    clear_scene_properties()
    bpy.utils.unregister_class(WalkModeOperator)
    bpy.utils.unregister_class(FlyModeOperator)
    bpy.utils.unregister_class(MaximizeScreenOperator)
    bpy.utils.unregister_class(WalkFlyModePanel)

if __name__ == "__main__":
    register()
