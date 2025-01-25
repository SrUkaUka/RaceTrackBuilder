import bpy

# Functions to move vertices
def move_vertices(context, direction, value_x, value_y, value_z):
    """Moves the selected vertices in the specified direction."""
    obj = context.active_object
    if obj and obj.type == 'MESH':
        bpy.ops.object.mode_set(mode='EDIT')  # Switch to edit mode
        bpy.ops.mesh.select_mode(type='VERT')  # Ensure we're in vertex mode
        if direction == 'LEFT':
            bpy.ops.transform.translate(value=(-value_x, 0, 0))
        elif direction == 'RIGHT':
            bpy.ops.transform.translate(value=(value_x, 0, 0))
        elif direction == 'FORWARD':
            bpy.ops.transform.translate(value=(0, value_y, 0))
        elif direction == 'BACKWARD':
            bpy.ops.transform.translate(value=(0, -value_y, 0))
        elif direction == 'UP':
            bpy.ops.transform.translate(value=(0, 0, value_z))
        elif direction == 'DOWN':
            bpy.ops.transform.translate(value=(0, 0, -value_z))
        bpy.ops.object.mode_set(mode='OBJECT')  # Switch back to object mode

# Functions to move objects
def move_objects(context, direction, value_x, value_y, value_z):
    """Moves the selected objects in the specified direction."""
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            if direction == 'LEFT':
                obj.location.x -= value_x
            elif direction == 'RIGHT':
                obj.location.x += value_x
            elif direction == 'FORWARD':
                obj.location.y += value_y
            elif direction == 'BACKWARD':
                obj.location.y -= value_y
            elif direction == 'UP':
                obj.location.z += value_z
            elif direction == 'DOWN':
                obj.location.z -= value_z

# Functions to rotate objects
def rotate_object(context, angle, axis='Z'):
    """Rotates the selected objects around the specified axis."""
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            if axis == 'Z':
                obj.rotation_euler.z += angle
            elif axis == 'X':
                obj.rotation_euler.x += angle

# Function to reset coordinates
def reset_coordinates(context):
    """Restores the coordinates of the selected objects to (0, 0, 0)."""
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            obj.location = (0.0, 0.0, 0.0)

# Function to duplicate objects
def duplicate_objects(context, direction, value_x, value_y, value_z):
    """Duplicates the selected objects, moves the duplicates, and selects only the new objects."""
    new_objects = []
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            # Create a full copy of the object
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()  # Create a copy of the data block (mesh)
            context.collection.objects.link(new_obj)
            new_objects.append(new_obj)

            # Move the new object in the specified direction
            if direction == 'LEFT':
                new_obj.location.x -= value_x
            elif direction == 'RIGHT':
                new_obj.location.x += value_x
            elif direction == 'FORWARD':
                new_obj.location.y += value_y
            elif direction == 'BACKWARD':
                new_obj.location.y -= value_y
            elif direction == 'UP':
                new_obj.location.z += value_z
            elif direction == 'DOWN':
                new_obj.location.z -= value_z

    # Deselect all objects
    for obj in context.scene.objects:
        obj.select_set(False)

    # Select only the new duplicates
    for new_obj in new_objects:
        new_obj.select_set(True)

# Function to mirror objects
def mirror_objects(context, axis):
    """Mirrors the selected objects along the specified axis."""
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            if axis == 'X':
                obj.scale.x *= -1
            elif axis == 'Y':
                obj.scale.y *= -1
            elif axis == 'Z':
                obj.scale.z *= -1

# Operators to move vertices
class MoveVerticesOperator(bpy.types.Operator):
    """Operator to move selected vertices in a specified direction."""
    bl_idname = "object.move_vertices"
    bl_label = "Move Vertices"

    direction: bpy.props.StringProperty()

    def execute(self, context):
        # Get current values from the context
        value_x = context.scene.move_operator.value_x
        value_y = context.scene.move_operator.value_y
        value_z = context.scene.move_operator.value_z

        move_vertices(context, self.direction, value_x, value_y, value_z)
        return {'FINISHED'}

# Operators to move objects
class MoveObjectsOperator(bpy.types.Operator):
    """Operator to move selected objects in a specified direction."""
    bl_idname = "object.move_objects"
    bl_label = "Move Objects"

    direction: bpy.props.StringProperty()

    def execute(self, context):
        # Get current values from the context
        value_x = context.scene.move_operator.value_x
        value_y = context.scene.move_operator.value_y
        value_z = context.scene.move_operator.value_z

        move_objects(context, self.direction, value_x, value_y, value_z)
        return {'FINISHED'}

# Rotation operators
class RotateObjectZOperator(bpy.types.Operator):
    """Operator to rotate objects around the Z axis by 90 degrees."""
    bl_idname = "object.rotate_object_z"
    bl_label = "Rotate Object in Z"

    def execute(self, context):
        rotate_object(context, 1.5708, 'Z')  # 90 degrees in radians
        return {'FINISHED'}

class RotateObjectXOperator(bpy.types.Operator):
    """Operator to rotate objects around the X axis by 90 degrees."""
    bl_idname = "object.rotate_object_x"
    bl_label = "Rotate Object in X"

    def execute(self, context):
        rotate_object(context, 1.5708, 'X')  # 90 degrees in radians
        return {'FINISHED'}

# Operators to reset coordinates
class ResetCoordinatesOperator(bpy.types.Operator):
    """Operator to reset the coordinates of the selected objects."""
    bl_idname = "object.reset_coordinates"
    bl_label = "Reset Coordinates"

    def execute(self, context):
        reset_coordinates(context)
        return {'FINISHED'}

# Operators to duplicate objects
class DuplicateObjectsOperator(bpy.types.Operator):
    """Operator to duplicate selected objects in a specified direction."""
    bl_idname = "object.duplicate_objects"
    bl_label = "Duplicate Objects"

    direction: bpy.props.StringProperty()

    def execute(self, context):
        duplicate_objects(context, self.direction, 12.0, 12.0, 1.0)
        return {'FINISHED'}

# Operators to mirror objects
class MirrorObjectOperator(bpy.types.Operator):
    """Operator to mirror objects along a specific axis."""
    bl_idname = "object.mirror_object"
    bl_label = "Mirror Object"

    axis: bpy.props.StringProperty()

    def execute(self, context):
        mirror_objects(context, self.axis)
        return {'FINISHED'}

# Panel for moving, rotating, duplicating, resetting, and mirroring objects and vertices
class MoveObjectsPanel(bpy.types.Panel):
    """Panel with buttons for moving, rotating, duplicating, and resetting selected objects."""
    bl_label = "Transformation Tools"
    bl_idname = "VIEW3D_PT_move_objects"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Transform'

    def draw(self, context):
        layout = self.layout

        # Access dynamic properties of the operator
        operator = context.scene.move_operator

        # Objects movement section
        layout.label(text="Move Objects:")

        row = layout.row(align=True)
        row.prop(operator, "value_x", text="Value X")
        row.prop(operator, "value_y", text="Value Y")
        row.prop(operator, "value_z", text="Value Z")

        # Movement buttons for objects
        row = layout.row(align=True)
        row.operator("object.move_objects", text="Left", icon='TRIA_LEFT').direction = 'LEFT'
        row.operator("object.move_objects", text="Right", icon='TRIA_RIGHT').direction = 'RIGHT'

        row = layout.row(align=True)
        row.operator("object.move_objects", text="Forward", icon='TRIA_UP').direction = 'FORWARD'
        row.operator("object.move_objects", text="Backward", icon='TRIA_DOWN').direction = 'BACKWARD'

        row = layout.row(align=True)
        row.operator("object.move_objects", text="Up", icon='SORT_DESC').direction = 'UP'
        row.operator("object.move_objects", text="Down", icon='SORT_ASC').direction = 'DOWN'

        # Rotation section
        layout.label(text="Rotate Objects:")
        row = layout.row(align=True)
        row.operator("object.rotate_object_z", text="90° Z", icon='FILE_REFRESH')
        row.operator("object.rotate_object_x", text="90° X", icon='FILE_REFRESH')

        # Duplication section
        layout.label(text="Duplicate Objects:")
        row = layout.row(align=True)
        row.operator("object.duplicate_objects", text="Left", icon='TRIA_LEFT').direction = 'LEFT'
        row.operator("object.duplicate_objects", text="Right", icon='TRIA_RIGHT').direction = 'RIGHT'

        row = layout.row(align=True)
        row.operator("object.duplicate_objects", text="Forward", icon='TRIA_UP').direction = 'FORWARD'
        row.operator("object.duplicate_objects", text="Backward", icon='TRIA_DOWN').direction = 'BACKWARD'

        row = layout.row(align=True)
        row.operator("object.duplicate_objects", text="Up", icon='SORT_DESC').direction = 'UP'
        row.operator("object.duplicate_objects", text="Down", icon='SORT_ASC').direction = 'DOWN'

        # Mirroring section
        layout.label(text="Mirror Objects:")
        row = layout.row(align=True)
        row.operator("object.mirror_object", text="Mirror X").axis = 'X'
        row.operator("object.mirror_object", text="Mirror Y").axis = 'Y'
        row.operator("object.mirror_object", text="Mirror Z").axis = 'Z'

        # Vertex movement section
        layout.label(text="Move Vertices:")

        # Movement buttons for vertices
        row = layout.row(align=True)
        row.operator("object.move_vertices", text="Left", icon='TRIA_LEFT').direction = 'LEFT'
        row.operator("object.move_vertices", text="Right", icon='TRIA_RIGHT').direction = 'RIGHT'

        row = layout.row(align=True)
        row.operator("object.move_vertices", text="Forward", icon='TRIA_UP').direction = 'FORWARD'
        row.operator("object.move_vertices", text="Backward", icon='TRIA_DOWN').direction = 'BACKWARD'

        row = layout.row(align=True)
        row.operator("object.move_vertices", text="Up", icon='SORT_DESC').direction = 'UP'
        row.operator("object.move_vertices", text="Down", icon='SORT_ASC').direction = 'DOWN'

        # Reset section
        layout.label(text="Restore:")
        layout.operator("object.reset_coordinates", text="Reset Coordinates", icon='FILE_NEW')

# Operator properties
class MoveObjectsSettings(bpy.types.PropertyGroup):
    value_x: bpy.props.FloatProperty(name="Value X", default=12.0, min=-100.0, max=100.0)
    value_y: bpy.props.FloatProperty(name="Value Y", default=12.0, min=-100.0, max=100.0)
    value_z: bpy.props.FloatProperty(name="Value Z", default=1.0, min=-100.0, max=100.0)

def register():
    bpy.utils.register_class(MoveObjectsSettings)
    bpy.utils.register_class(MoveVerticesOperator)
    bpy.utils.register_class(MoveObjectsOperator)
    bpy.utils.register_class(RotateObjectZOperator)
    bpy.utils.register_class(RotateObjectXOperator)
    bpy.utils.register_class(ResetCoordinatesOperator)
    bpy.utils.register_class(DuplicateObjectsOperator)
    bpy.utils.register_class(MirrorObjectOperator)
    bpy.utils.register_class(MoveObjectsPanel)
    bpy.types.Scene.move_operator = bpy.props.PointerProperty(type=MoveObjectsSettings)

def unregister():
    bpy.utils.unregister_class(MoveObjectsSettings)
    bpy.utils.unregister_class(MoveVerticesOperator)
    bpy.utils.unregister_class(MoveObjectsOperator)
    bpy.utils.unregister_class(RotateObjectZOperator)
    bpy.utils.unregister_class(RotateObjectXOperator)
    bpy.utils.unregister_class(ResetCoordinatesOperator)
    bpy.utils.unregister_class(DuplicateObjectsOperator)
    bpy.utils.unregister_class(MirrorObjectOperator)
    bpy.utils.unregister_class(MoveObjectsPanel)
    del bpy.types.Scene.move_operator

if __name__ == "__main__":
    register()
