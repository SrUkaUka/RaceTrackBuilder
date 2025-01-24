import bpy

class AlignVerticesPanel(bpy.types.Panel):
    bl_label = "Align Vertices"
    bl_idname = "VIEW3D_PT_align_vertices"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator("mesh.align_vertices_x", text="X")
        row.operator("mesh.align_vertices_y", text="Y")
        row.operator("mesh.align_vertices_z", text="Z")

class AlignVerticesOperatorZ(bpy.types.Operator):
    bl_idname = "mesh.align_vertices_z"
    bl_label = "Align Vertices Z"
    
    # Documentation for the operator
    bl_description = "Aligns the selected vertices along the Z-axis by resizing the mesh. This operation will " \
                      "constrain the movement of the vertices to the Z-axis, effectively flattening the " \
                      "mesh along the X and Y axes."

    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')  # Switch to Edit Mode
        bpy.ops.mesh.select_mode(type='VERT')  # Set the selection mode to vertices
        bpy.ops.transform.resize(value=(1, 1, 0))  # Scale along X and Y, but not Z
        bpy.ops.object.mode_set(mode='OBJECT')  # Switch back to Object Mode
        return {'FINISHED'}

class AlignVerticesOperatorX(bpy.types.Operator):
    bl_idname = "mesh.align_vertices_x"
    bl_label = "Align Vertices X"
    
    # Documentation for the operator
    bl_description = "Aligns the selected vertices along the X-axis by resizing the mesh. This operation will " \
                      "constrain the movement of the vertices to the X-axis, effectively flattening the " \
                      "mesh along the Y and Z axes."

    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')  # Switch to Edit Mode
        bpy.ops.mesh.select_mode(type='VERT')  # Set the selection mode to vertices
        bpy.ops.transform.resize(value=(0, 1, 1))  # Scale along Y and Z, but not X
        bpy.ops.object.mode_set(mode='OBJECT')  # Switch back to Object Mode
        return {'FINISHED'}

class AlignVerticesOperatorY(bpy.types.Operator):
    bl_idname = "mesh.align_vertices_y"
    bl_label = "Align Vertices Y"
    
    # Documentation for the operator
    bl_description = "Aligns the selected vertices along the Y-axis by resizing the mesh. This operation will " \
                      "constrain the movement of the vertices to the Y-axis, effectively flattening the " \
                      "mesh along the X and Z axes."

    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')  # Switch to Edit Mode
        bpy.ops.mesh.select_mode(type='VERT')  # Set the selection mode to vertices
        bpy.ops.transform.resize(value=(1, 0, 1))  # Scale along X and Z, but not Y
        bpy.ops.object.mode_set(mode='OBJECT')  # Switch back to Object Mode
        return {'FINISHED'}

def register():
    bpy.utils.register_class(AlignVerticesPanel)
    bpy.utils.register_class(AlignVerticesOperatorZ)
    bpy.utils.register_class(AlignVerticesOperatorX)
    bpy.utils.register_class(AlignVerticesOperatorY)

def unregister():
    bpy.utils.unregister_class(AlignVerticesPanel)
    bpy.utils.unregister_class(AlignVerticesOperatorZ)
    bpy.utils.unregister_class(AlignVerticesOperatorX)
    bpy.utils.unregister_class(AlignVerticesOperatorY)

if __name__ == "__main__":
    register()
