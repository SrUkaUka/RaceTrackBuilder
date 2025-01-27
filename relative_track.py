import bpy
import math

# Operator to create the spiral
class SimpleSpiralOperator(bpy.types.Operator):
    bl_idname = "mesh.create_spiral"
    bl_label = "Create Spiral"
    bl_description = "Creates a spiral curve"

    def execute(self, context):
        subdivisions = context.scene.nurbs_path_subdivisions
        turns = context.scene.spiral_turns
        
        radius = 100  # Fixed radius for larger size
        height = context.scene.spiral_height  # Usamos la altura seleccionada
        sections = subdivisions
        
        verts = []
        for i in range(sections * turns):
            angle = i * math.pi * 2 / sections
            z = i * height / (sections * turns)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            verts.append((x, y, z))
        
        curve_data = bpy.data.curves.new('spiral_curve', type='CURVE')
        curve_data.dimensions = '3D'
        spline = curve_data.splines.new('POLY')
        spline.points.add(count=len(verts) - 1)
        
        for i, coord in enumerate(verts):
            spline.points[i].co = (coord[0], coord[1], coord[2], 1)
        
        curve_obj = bpy.data.objects.new('Spiral', curve_data)
        context.scene.collection.objects.link(curve_obj)
        
        self.report({'INFO'}, f"Spiral created with {turns} turns and height {height}.")
        return {'FINISHED'}

# Operator to create a Bezier circle curve
class SimpleCircleOperator(bpy.types.Operator):
    bl_idname = "curve.create_circle"
    bl_label = "Create Circle (Curve)"
    bl_description = "Creates a Bezier circle curve"

    def execute(self, context):
        bpy.ops.curve.primitive_bezier_circle_add(
            radius=100,  # Fixed radius for larger size
            location=(0, 0, 0), 
            align='WORLD'
        )
        
        obj = context.active_object
        if obj and obj.type == 'CURVE':
            obj.data.resolution_u = context.scene.nurbs_path_subdivisions
        
        return {'FINISHED'}

# Operator to create a NURBS Path curve
class SimplePathOperator(bpy.types.Operator):
    bl_idname = "curve.create_nurbs_path"
    bl_label = "Create NURBS Path Curve"
    bl_description = "Creates a NURBS path curve"

    def execute(self, context):
        bpy.ops.curve.primitive_nurbs_path_add(
            radius=30,  # Fixed radius for larger size
            location=(0, 0, 0), 
            align='WORLD'
        )
        
        obj = context.active_object
        if obj and obj.type == 'CURVE':
            obj.data.resolution_u = context.scene.nurbs_path_subdivisions
        
        return {'FINISHED'}

# Operator to adjust the subdivision of the selected curve
class AdjustCurveResolutionOperator(bpy.types.Operator):
    bl_idname = "curve.adjust_resolution"
    bl_label = "Adjust Curve Subdivision"
    bl_description = "Adjust the subdivision of the selected curve"

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'CURVE':
            # Ensure we're in object mode
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Switch to Edit Mode
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Apply the Subdivide command directly in Edit Mode
            bpy.ops.curve.subdivide(number_cuts=context.scene.nurbs_path_subdivisions)
            
            # Return to Object Mode
            bpy.ops.object.mode_set(mode='OBJECT')
            
            self.report({'INFO'}, f"Curve subdivided with {context.scene.nurbs_path_subdivisions} cuts.")
        else:
            self.report({'WARNING'}, "Select a curve to adjust its subdivision.")
        
        return {'FINISHED'}

# Operator to add modifiers to selected objects
class AddModifiersOperator(bpy.types.Operator):
    bl_idname = "object.add_modifiers"
    bl_label = "Add Modifiers"
    bl_description = "Adds array and curve modifiers to the selected mesh"

    def execute(self, context):
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected.")
            return {'CANCELLED'}
        
        non_curve_objects = [obj for obj in selected_objects if obj.type != 'CURVE']
        
        if len(non_curve_objects) > 1:
            bpy.ops.object.join()
        elif len(non_curve_objects) == 1:
            self.report({'INFO'}, "Only one non-curve object. No objects were joined.")
        else:
            self.report({'WARNING'}, "Select more than one non-curve object to join.")
            return {'CANCELLED'}
        
        obj = context.active_object
        
        if obj and obj.type == 'MESH':
            array_modifier = obj.modifiers.new(name="Array", type='ARRAY')
            curve_modifier = obj.modifiers.new(name="Curve", type='CURVE')
            
            curve_object = None
            for selected in selected_objects:
                if selected.type == 'CURVE':
                    curve_object = selected
                    break
            if not curve_object:
                curve_object = context.view_layer.objects.active
            
            if curve_object and curve_object.type == 'CURVE':
                obj.modifiers["Curve"].object = curve_object
                self.report({'INFO'}, f"Modifiers applied with {curve_object.name} as the target.")
            else:
                self.report({'WARNING'}, "No valid curve found as the target for the 'Curve' modifier.")
        else:
            self.report({'WARNING'}, "Selected object is not a mesh to apply modifiers.")
        
        return {'FINISHED'}

# Operator to join selected objects
class JoinObjectsOperator(bpy.types.Operator):
    bl_idname = "object.join_objects"
    bl_label = "Join Objects"
    bl_description = "Joins the selected objects into one"

    def execute(self, context):
        if len(context.selected_objects) < 2:
            self.report({'WARNING'}, "At least two objects are needed to join.")
            return {'CANCELLED'}
        
        bpy.ops.object.join()
        self.report({'INFO'}, "Objects joined successfully.")
        return {'FINISHED'}

# New Operator to insert quadblock planes based on width
class QuadblockWidthOperator(bpy.types.Operator):
    bl_idname = "mesh.quadblock_width"
    bl_label = "Quadblock Width Planes"
    bl_description = "Inserts planes parallel to each other based on the width value"

    def execute(self, context):
        width = context.scene.width  # Number of planes to create
        
        distance = 12  # Size of each plane, adjust as needed
        for i in range(width):
            # Calculate position for each plane
            position_y = (i - (width - 1) / 2) * distance  # Ensures planes are centered
            
            # Create a plane
            bpy.ops.mesh.primitive_plane_add(size=12, location=(0, position_y, 0))  # Adjust to Y axis
            plane = context.active_object
            
            # Subdivide the plane
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.subdivide(number_cuts=1)  # You can adjust number of subdivisions here
            bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, f"{width} quadblock width planes inserted.")
        return {'FINISHED'}

# Panel for the interface
class SimpleSpiralPanel(bpy.types.Panel):
    bl_label = "Create Spiral, Circle, and NURBS Path Curve"
    bl_idname = "OBJECT_PT_spiral_circle_path"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Relative Shape'
    
    def draw(self, context):
        layout = self.layout
        
        layout.prop(context.scene, "nurbs_path_subdivisions")
        layout.prop(context.scene, "spiral_turns")
        
        # Agregar la propiedad de altura
        layout.prop(context.scene, "spiral_height")  # Nueva propiedad de altura
        
        # Añadir el campo de "width"
        layout.prop(context.scene, "width")
        
        layout.operator("curve.adjust_resolution", text="Apply Subdivision to Curve")
        
        layout.separator()
        
        layout.operator("mesh.create_spiral")
        layout.operator("curve.create_circle")
        layout.operator("curve.create_nurbs_path")
        
        layout.separator()
        
        layout.operator("object.add_modifiers")
        layout.operator("object.join_objects")
        
        layout.separator()
        
        layout.operator("mesh.quadblock_width", text="Quadblock Width")

# Registering the classes and properties
def register():
    bpy.utils.register_class(SimpleSpiralOperator)
    bpy.utils.register_class(SimpleCircleOperator)
    bpy.utils.register_class(SimplePathOperator)
    bpy.utils.register_class(AdjustCurveResolutionOperator)
    bpy.utils.register_class(AddModifiersOperator)
    bpy.utils.register_class(JoinObjectsOperator)
    bpy.utils.register_class(SimpleSpiralPanel)
    bpy.utils.register_class(QuadblockWidthOperator)
    
    bpy.types.Scene.nurbs_path_subdivisions = bpy.props.IntProperty(
        name="Subdivisions",
        description="Number of subdivisions to adjust curve subdivision",
        default=5,
        min=2,
        max=64
    )
    
    bpy.types.Scene.spiral_turns = bpy.props.IntProperty(
        name="Turns",
        description="Number of turns for the spiral",
        default=10,
        min=1,
        max=100
    )
    
    bpy.types.Scene.width = bpy.props.IntProperty(
        name="Width",
        description="Number of planes to insert",
        default=5,  # Default number of planes
        min=1,
        max=100
    )
    
    # Registrar la nueva propiedad de altura del espiral
    bpy.types.Scene.spiral_height = bpy.props.FloatProperty(
        name="Height",
        description="Altura total del espiral",
        default=100,  # Valor predeterminado
        min=1,  # Aseguramos que la altura no sea menor que 1
        max=1000  # Aseguramos que la altura no sea mayor que 1000
    )

def unregister():
    bpy.utils.unregister_class(SimpleSpiralOperator)
    bpy.utils.unregister_class(SimpleCircleOperator)
    bpy.utils.unregister_class(SimplePathOperator)
    bpy.utils.unregister_class(AdjustCurveResolutionOperator)
    bpy.utils.unregister_class(AddModifiersOperator)
    bpy.utils.unregister_class(JoinObjectsOperator)
    bpy.utils.unregister_class(SimpleSpiralPanel)
    bpy.utils.unregister_class(QuadblockWidthOperator)
    
    del bpy.types.Scene.nurbs_path_subdivisions
    del bpy.types.Scene.spiral_turns
    del bpy.types.Scene.width
    del bpy.types.Scene.spiral_height  # Eliminar la propiedad de altura

if __name__ == "__main__":
    register()
