import bpy

# Function to create a circle (as a curve) with subdivisions and specific scale
def create_road(self, context, subdivisions, scale_factor, road_name):
    bpy.ops.curve.primitive_bezier_circle_add(radius=5, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = road_name
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.subdivide(number_cuts=subdivisions)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.scale = (scale_factor, scale_factor, scale_factor)

def create_long_road(self, context):
    create_road(self, context, subdivisions=6, scale_factor=10, road_name="Long_Road")

def create_med_road(self, context):
    create_road(self, context, subdivisions=4, scale_factor=6, road_name="Med_Road")

def create_short_road(self, context):
    create_road(self, context, subdivisions=2, scale_factor=3, road_name="Short_Road")

def check_road_exists():
    road_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'CURVE' and 'Road' in obj.name]
    return road_objects

# Function to create multiple tiles based on the provided tile count
def create_multiple_tiles(self, context, tile_count):
    road_objects = check_road_exists()
    if not road_objects:
        self.report({'WARNING'}, "There is no road in the scene")
        return {'CANCELLED'}
    if len(road_objects) > 1:
        self.report({'WARNING'}, "There's more than one road")
        return {'CANCELLED'}

    # Tile coordinates
    coordinates = [(0, -5, 0), (0, 5, 0), (0, 15, 0), (0, -15, 0), (0, -25, 0), (0, 25, 0)]
    
    # Create the appropriate number of tiles based on tile_count parameter
    created_objects = []
    for i in range(tile_count):
        bpy.ops.mesh.primitive_plane_add(location=coordinates[i])
        obj = bpy.context.active_object
        obj.scale = (6, 6, 6)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        material = bpy.data.materials.new(name="Road")
        material.use_nodes = True
        bsdf = material.node_tree.nodes["Principled BSDF"]
        image_texture_node = material.node_tree.nodes.new(type='ShaderNodeTexImage')
        material.node_tree.links.new(image_texture_node.outputs["Color"], bsdf.inputs["Base Color"])

        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)

        array_modifier = obj.modifiers.new(name="Array", type='ARRAY')
        array_modifier.count = 5
        array_modifier.relative_offset_displace[0] = 1

        curve_modifier = obj.modifiers.new(name="Curve", type='CURVE')
        curve_modifier.deform_axis = 'POS_X'
        curve_modifier.object = road_objects[0]

        # Add object to the list
        created_objects.append(obj)

    # Join all created objects into a single object after they have been generated
    if created_objects:
        # Select all generated objects
        bpy.context.view_layer.objects.active = created_objects[0]  # Activate the first object
        for obj in created_objects:
            obj.select_set(True)  # Select all objects
        bpy.ops.object.join()  # Join all selected objects

# Specific functions to create 3, 4, 5, and 6 tiles
def create_three_tiles(self, context):
    create_multiple_tiles(self, context, tile_count=3)

def create_four_tiles(self, context):
    create_multiple_tiles(self, context, tile_count=4)

def create_five_tiles(self, context):
    create_multiple_tiles(self, context, tile_count=5)

def create_six_tiles(self, context):
    create_multiple_tiles(self, context, tile_count=6)

# Function to apply modifiers, select the object, and separate by loose parts
def finish_process(self, context):
    if not bpy.context.selected_objects:
        self.report({'WARNING'}, "No object found")
        return {'CANCELLED'}
    obj = bpy.context.active_object
    if obj.modifiers:
        for modifier in obj.modifiers:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.select_set(True)
    bpy.ops.mesh.separate(type='LOOSE')
    return {'FINISHED'}

# Define the operators before registering them
class CreateLongRoadOperator(bpy.types.Operator):
    bl_idname = "mesh.create_long_road"
    bl_label = "Generate Long_Road"

    def execute(self, context):
        create_long_road(self, context)
        return {'FINISHED'}

class CreateMedRoadOperator(bpy.types.Operator):
    bl_idname = "mesh.create_med_road"
    bl_label = "Generate Med_Road"

    def execute(self, context):
        create_med_road(self, context)
        return {'FINISHED'}

class CreateShortRoadOperator(bpy.types.Operator):
    bl_idname = "mesh.create_short_road"
    bl_label = "Generate Short_Road"

    def execute(self, context):
        create_short_road(self, context)
        return {'FINISHED'}

class CreateTileOperator(bpy.types.Operator):
    bl_idname = "mesh.create_tile"
    bl_label = "Generate Tile (Plane subdivided with Modifiers)"

    def execute(self, context):
        create_tile(self, context)
        return {'FINISHED'}

class Create1TilesOperator(bpy.types.Operator):
    bl_idname = "mesh.create_1_tiles"
    bl_label = "Generate 1 Tile"

    def execute(self, context):
        create_multiple_tiles(self, context, tile_count=1)
        return {'FINISHED'}

class Create2TilesOperator(bpy.types.Operator):
    bl_idname = "mesh.create_2_tiles"
    bl_label = "Generate 2 Tiles"

    def execute(self, context):
        create_multiple_tiles(self, context, tile_count=2)
        return {'FINISHED'}

class Create3TilesOperator(bpy.types.Operator):
    bl_idname = "mesh.create_3_tiles"
    bl_label = "Generate 3 Tiles"

    def execute(self, context):
        create_three_tiles(self, context)
        return {'FINISHED'}

class Create4TilesOperator(bpy.types.Operator):
    bl_idname = "mesh.create_4_tiles"
    bl_label = "Generate 4 Tiles"

    def execute(self, context):
        create_four_tiles(self, context)
        return {'FINISHED'}

class Create5TilesOperator(bpy.types.Operator):
    bl_idname = "mesh.create_5_tiles"
    bl_label = "Generate 5 Tiles"

    def execute(self, context):
        create_five_tiles(self, context)
        return {'FINISHED'}

class Create6TilesOperator(bpy.types.Operator):
    bl_idname = "mesh.create_6_tiles"
    bl_label = "Generate 6 Tiles"

    def execute(self, context):
        create_six_tiles(self, context)
        return {'FINISHED'}

class FinishProcessOperator(bpy.types.Operator):
    bl_idname = "mesh.finish_process"
    bl_label = "Finish (Apply Modifiers and Separate)"

    def execute(self, context):
        finish_process(self, context)
        return {'FINISHED'}

# Define the panel
class SimplePanel(bpy.types.Panel):
    bl_label = "Road Creation Panel"
    bl_idname = "PT_CreateRoads"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Track Builder"

    def draw(self, context):
        layout = self.layout

        # Roads section
        layout.label(text="Generate Roads:", icon='CURVE_BEZCURVE')
        col = layout.column(align=True)
        col.operator("mesh.create_long_road", text="Long Road")
        col.operator("mesh.create_med_road", text="Medium Road")
        col.operator("mesh.create_short_road", text="Short Road")

        # Tiles section
        layout.label(text="Generate Tiles:", icon='MESH_GRID')
        grid = layout.grid_flow(row_major=True, columns=3, even_columns=True, even_rows=True, align=True)
        grid.operator("mesh.create_1_tiles", text="1 Tile")
        grid.operator("mesh.create_2_tiles", text="2 Tiles")
        grid.operator("mesh.create_3_tiles", text="3 Tiles")
        grid.operator("mesh.create_4_tiles", text="4 Tiles")
        grid.operator("mesh.create_5_tiles", text="5 Tiles")
        grid.operator("mesh.create_6_tiles", text="6 Tiles")

        # Finalization section
        layout.label(text="Finalization:", icon='CHECKMARK')
        col = layout.column(align=True)
        col.operator("mesh.finish_process", text="Finalize")


# Register and unregister the classes
def register():
    bpy.utils.register_class(CreateLongRoadOperator)
    bpy.utils.register_class(CreateMedRoadOperator)
    bpy.utils.register_class(CreateShortRoadOperator)
    bpy.utils.register_class(CreateTileOperator)
    bpy.utils.register_class(Create1TilesOperator)
    bpy.utils.register_class(Create2TilesOperator)
    bpy.utils.register_class(Create3TilesOperator)
    bpy.utils.register_class(Create4TilesOperator)
    bpy.utils.register_class(Create5TilesOperator)
    bpy.utils.register_class(Create6TilesOperator)
    bpy.utils.register_class(FinishProcessOperator)
    bpy.utils.register_class(SimplePanel)

def unregister():
    bpy.utils.unregister_class(SimplePanel)
    bpy.utils.unregister_class(CreateShortRoadOperator)
    bpy.utils.unregister_class(CreateMedRoadOperator)
    bpy.utils.unregister_class(CreateLongRoadOperator)
    bpy.utils.unregister_class(CreateTileOperator)
    bpy.utils.unregister_class(Create1TilesOperator)
    bpy.utils.unregister_class(Create2TilesOperator)
    bpy.utils.unregister_class(Create3TilesOperator)
    bpy.utils.unregister_class(Create4TilesOperator)
    bpy.utils.unregister_class(Create5TilesOperator)
    bpy.utils.unregister_class(Create6TilesOperator)
    bpy.utils.unregister_class(FinishProcessOperator)

if __name__ == "__main__":
    register()
