import bpy
import time

class GeometryToolsPanel(bpy.types.Panel):
    """Panel for Geometry Tools."""
    bl_label = "Finish"
    bl_idname = "PT_GEOMETRY_TOOLS"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Find Geometry"

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        # Dropdown menu for FIND button
        col.label(text="Find Options:")
        if hasattr(context.scene, "find_option"):  # Verifica que la propiedad exista
            col.prop(context.scene, "find_option", text="")
        else:
            col.label(text="Error: Property not found.", icon="ERROR")

        # Buttons
        col.operator("geometry.find_objects", text="Find")
        col.separator()
        col.operator("geometry.find_invalid", text="Find Invalid Geometry")
        col.separator()
        col.operator("geometry.reset_name", text="Reset Name")  # Aquí está el botón de Reset Name

class OBJECT_OT_FindObjects(bpy.types.Operator):
    """Find objects and add suffixes based on the selection."""
    bl_idname = "geometry.find_objects"
    bl_label = "Find Objects"

    def execute(self, context):
        context.scene.find_executed = True  # Indicates the Find button was executed
        find_option = context.scene.find_option
        
        # Desactivar actualizaciones de la vista para acelerar el proceso
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=0)

        start_time = time.time()
        
        # Filtramos los objetos MESH en la escena
        mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']

        for obj in mesh_objects:
            vertex_count = len(obj.data.vertices)
            edge_count = len(obj.data.edges)  # Contamos las aristas
            face_count = len(obj.data.polygons)  # Contamos las caras

            # Skip objects with NGons
            if any(len(poly.vertices) > 4 for poly in obj.data.polygons):
                continue

            # Asignar sufijos basado en el número de vértices, aristas y caras
            if find_option == 'TRIBLOCK' and vertex_count == 6 and edge_count == 9 and face_count == 4:
                obj.name = f"{obj.name}_triblock"
            elif find_option == 'QUADBLOCK' and vertex_count == 9 and edge_count == 12 and face_count == 4:
                obj.name = f"{obj.name}_quadblock"

        elapsed_time = time.time() - start_time
        self.report({'INFO'}, f"Find operation completed in {elapsed_time:.2f} seconds.")
        return {'FINISHED'}

class OBJECT_OT_FindInvalidGeometry(bpy.types.Operator):
    """Mark objects as "invalid" if they do not have the expected suffixes or contain NGons."""
    bl_idname = "geometry.find_invalid"
    bl_label = "Find Invalid Geometry"

    def execute(self, context):
        # Ensure the Find operation has been executed
        if not context.scene.get("find_executed", False):
            self.report({'WARNING'}, "You must run the 'Find' operation first to identify valid geometry.")
            return {'CANCELLED'}
        
        # Check if both TRIBLOCK and QUADBLOCK suffixes are found
        triblock_found = any(obj.name.endswith("_triblock") for obj in bpy.data.objects if obj.type == 'MESH')
        quadblock_found = any(obj.name.endswith("_quadblock") for obj in bpy.data.objects if obj.type == 'MESH')

        if not (triblock_found and quadblock_found):
            self.report({'WARNING'}, "Both TRIBLOCK and QUADBLOCK suffixes must be found before marking invalid geometry.")
            return {'CANCELLED'}

        # Mark objects without the expected suffixes as "_invalid"
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and not (obj.name.endswith("_triblock") or obj.name.endswith("_quadblock")):
                obj.name = f"{obj.name}_invalid"

        self.report({'INFO'}, "Invalid geometry marked.")
        return {'FINISHED'}

class OBJECT_OT_ResetName(bpy.types.Operator):
    """Remove "_invalid", "_quadblock", and "_triblock" suffixes from all objects."""
    bl_idname = "geometry.reset_name"
    bl_label = "Reset Name"

    def execute(self, context):
        # Filtramos los objetos MESH
        mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
        
        for obj in mesh_objects:
            # Eliminamos los sufijos "_invalid", "_quadblock", "_triblock"
            if obj.name.endswith("_invalid"):
                obj.name = obj.name.replace("_invalid", "")
            if obj.name.endswith("_quadblock"):
                obj.name = obj.name.replace("_quadblock", "")
            if obj.name.endswith("_triblock"):
                obj.name = obj.name.replace("_triblock", "")

        self.report({'INFO'}, "Names reset.")
        return {'FINISHED'}

# Registro de la propiedad 'find_option' antes de acceder a ella
def register():
    bpy.types.Scene.find_option = bpy.props.EnumProperty(
        name="Find Option",
        items=[ 
            ('TRIBLOCK', "Triblock", "Add suffix _triblock to objects with 6 vertices, 9 edges, and 4 faces"),
            ('QUADBLOCK', "Quadblock", "Add suffix _quadblock to objects with 9 vertices, 12 edges, and 4 faces"),
        ],
        default='TRIBLOCK'
    )
    bpy.types.Scene.find_executed = bpy.props.BoolProperty(default=False)

    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    if "find_option" in bpy.types.Scene.bl_rna.properties:
        del bpy.types.Scene.find_option
    if "find_executed" in bpy.types.Scene.bl_rna.properties:
        del bpy.types.Scene.find_executed

# Aseguramos que las clases están registradas
classes = [
    GeometryToolsPanel,
    OBJECT_OT_FindObjects,
    OBJECT_OT_FindInvalidGeometry,
    OBJECT_OT_ResetName
]

if __name__ == "__main__":
    register()
