import bpy

# Function to separate the selected vertices and extrude
def extrude_separately():
    # Create a list of objects before separation
    initial_objects = set(bpy.context.view_layer.objects.selected)
    
    # Ensure that edit mode is activated
    bpy.ops.object.mode_set(mode='EDIT')

    # Separate selected vertices by selection
    bpy.ops.mesh.separate(type='SELECTED')

    # Return to object mode to select the separated objects
    bpy.ops.object.mode_set(mode='OBJECT')

    # Create a list of objects after separation
    current_objects = set(bpy.context.view_layer.objects.selected)
    
    # Identify the new objects (those that were not in the initial list)
    new_objects = list(current_objects - initial_objects)  # Convert set to list
    
    # Deselect the initial objects
    for obj in initial_objects:
        obj.select_set(False)
    
    # Select only the new objects
    for obj in new_objects:
        obj.select_set(True)
    
    # Set the last object as the active one for extrusion
    bpy.context.view_layer.objects.active = new_objects[-1]  # Set active object
    bpy.ops.object.mode_set(mode='EDIT')

    # Select all vertices in edit mode
    bpy.ops.mesh.select_all(action='SELECT')

    # Perform the extrusion on the new selected objects without moving it
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, 0)})  # Extrusion at the same position


# Function to finalize the extrusion with a horizontal cut and separate by loose parts
def finalize_extrusion():
    # Iterate over each selected object
    for obj in bpy.context.view_layer.objects.selected:
        # Set the object as active
        bpy.context.view_layer.objects.active = obj

        # Switch to edit mode for making the cut
        bpy.ops.object.mode_set(mode='EDIT')

        # Deselect all vertices
        bpy.ops.mesh.select_all(action='DESELECT')

        # Perform the horizontal cut using Loop Cut (Ctrl + R)
        bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={
            "number_cuts": 1,
            "smoothness": 0,
            "falloff": 'INVERSE_SQUARE',
            "object_index": 0,
            "edge_index": 4,  # This may need adjustment based on the specific edge index
            "mesh_select_mode_init": (True, False, False)
        }, TRANSFORM_OT_edge_slide={
            "value": 0,
            "single_side": False,
            "use_even": False,
            "flipped": False,
            "use_clamp": True,
            "mirror": True,
            "snap": False,
            "snap_elements": {'INCREMENT'},
            "use_snap_project": False,
            "snap_target": 'CLOSEST',
            "use_snap_self": True,
            "use_snap_edit": True,
            "use_snap_nonedit": True,
            "use_snap_selectable": False,
            "snap_point": (0, 0, 0),
            "correct_uv": True,
            "release_confirm": False,
            "use_accurate": False
        })

    # Return to object mode to separate by loose parts
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.separate(type='LOOSE')


# Create the user interface (UI)
class ExtrudeSeparatePanel(bpy.types.Panel):
    bl_label = "Extrude Separately & Finalize Extrusion"
    bl_idname = "OBJECT_PT_extrude_separately_finalize"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.extrude_separately", text="Extrude Separately")
        layout.operator("mesh.finalize_extrusion", text="Finalize Extrusion")


# Register the operators
class ExtrudeSeparateOperator(bpy.types.Operator):
    bl_idname = "mesh.extrude_separately"
    bl_label = "Extrude Separately"

    def execute(self, context):
        extrude_separately()
        return {'FINISHED'}


class FinalizeExtrusionOperator(bpy.types.Operator):
    bl_idname = "mesh.finalize_extrusion"
    bl_label = "Finalize Extrusion"

    def execute(self, context):
        finalize_extrusion()
        return {'FINISHED'}


# Register the classes
def register():
    bpy.utils.register_class(ExtrudeSeparatePanel)
    bpy.utils.register_class(ExtrudeSeparateOperator)
    bpy.utils.register_class(FinalizeExtrusionOperator)


def unregister():
    bpy.utils.unregister_class(ExtrudeSeparatePanel)
    bpy.utils.unregister_class(ExtrudeSeparateOperator)
    bpy.utils.unregister_class(FinalizeExtrusionOperator)


if __name__ == "__main__":
    register()
