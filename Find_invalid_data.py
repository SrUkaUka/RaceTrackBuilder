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

        # Checkboxes for skipping triblock and quadblock validation
        col.prop(context.scene, "skip_triblock", text="No Triblock")
        col.prop(context.scene, "skip_quadblock", text="No Quadblock")

        # Buttons
        col.operator("geometry.find_objects", text="Find")
        col.separator()
        col.operator("geometry.find_invalid", text="Find Invalid Geometry")
        col.separator()
        col.operator("geometry.reset_name", text="Reset Name")  # Botón de Reset Name


class OBJECT_OT_FindObjects(bpy.types.Operator):
    """Find objects and add suffixes based on the selection."""
    bl_idname = "geometry.find_objects"
    bl_label = "Find Objects"

    def execute(self, context):
        context.scene.find_executed = True  # Indica que se ejecutó el botón Find
        find_option = context.scene.find_option

        # Desactivar actualizaciones de la vista para acelerar el proceso
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=0)

        start_time = time.time()

        # Filtrar los objetos de tipo MESH en la escena
        mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']

        for obj in mesh_objects:
            vertex_count = len(obj.data.vertices)
            edge_count = len(obj.data.edges)
            face_count = len(obj.data.polygons)

            # Saltar objetos con NGons
            if any(len(poly.vertices) > 4 for poly in obj.data.polygons):
                continue

            # Asignar sufijos basado en la cantidad de vértices, aristas y caras
            if find_option == 'TRIBLOCK' and vertex_count == 6 and edge_count == 9 and face_count == 4:
                obj.name = f"{obj.name}_triblock"
            elif find_option == 'QUADBLOCK' and vertex_count == 9 and edge_count == 12 and face_count == 4:
                obj.name = f"{obj.name}_quadblock"

        elapsed_time = time.time() - start_time
        self.report({'INFO'}, f"Find operation completed in {elapsed_time:.2f} seconds.")
        return {'FINISHED'}


class OBJECT_OT_FindInvalidGeometry(bpy.types.Operator):
    """Mark objects as 'invalid' if they do not have the expected suffixes or are not MESH objects."""
    bl_idname = "geometry.find_invalid"
    bl_label = "Find Invalid Geometry"

    def execute(self, context):
        # Asegurar que el botón "Find" ha sido ejecutado antes de marcar objetos
        if not context.scene.get("find_executed", False):
            self.report({'WARNING'}, "You must run the 'Find' operation first to identify valid geometry.")
            return {'CANCELLED'}

        skip_triblock = context.scene.skip_triblock
        skip_quadblock = context.scene.skip_quadblock

        # Verificar si se han encontrado ambos sufijos (_triblock y _quadblock), a menos que se hayan marcado las excepciones
        triblock_found = any(obj.name.endswith("_triblock") for obj in bpy.data.objects if obj.type == 'MESH')
        quadblock_found = any(obj.name.endswith("_quadblock") for obj in bpy.data.objects if obj.type == 'MESH')

        if not ((triblock_found or skip_triblock) and (quadblock_found or skip_quadblock)):
            self.report({'WARNING'}, "Both TRIBLOCK and QUADBLOCK suffixes must be found or their exceptions checked before marking invalid geometry.")
            return {'CANCELLED'}

        # Recorrer todos los objetos en la escena
        for obj in bpy.data.objects:
            # Si el objeto no es MESH, marcar como "_invalid"
            if obj.type != 'MESH':
                obj.name = f"{obj.name}_invalid"
            # Si es MESH pero no tiene los sufijos correctos, marcar como "_invalid"
            elif not (obj.name.endswith("_triblock") or obj.name.endswith("_quadblock")):
                obj.name = f"{obj.name}_invalid"

        self.report({'INFO'}, "Invalid geometry marked.")
        return {'FINISHED'}


class OBJECT_OT_ResetName(bpy.types.Operator):
    """Remove '_invalid', '_quadblock', and '_triblock' suffixes from all objects."""
    bl_idname = "geometry.reset_name"
    bl_label = "Reset Name"

    def execute(self, context):
        # Filtrar los objetos en la escena
        for obj in bpy.data.objects:
            # Eliminar los sufijos "_invalid", "_quadblock", "_triblock"
            for suffix in ["_invalid", "_quadblock", "_triblock"]:
                if obj.name.endswith(suffix):
                    obj.name = obj.name.replace(suffix, "")

        self.report({'INFO'}, "Names reset.")
        return {'FINISHED'}


# Registro de propiedades antes de acceder a ellas
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
    bpy.types.Scene.skip_triblock = bpy.props.BoolProperty(name="No Triblock", default=False)
    bpy.types.Scene.skip_quadblock = bpy.props.BoolProperty(name="No Quadblock", default=False)

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    if "find_option" in bpy.types.Scene.bl_rna.properties:
        del bpy.types.Scene.find_option
    if "find_executed" in bpy.types.Scene.bl_rna.properties:
        del bpy.types.Scene.find_executed
    if "skip_triblock" in bpy.types.Scene.bl_rna.properties:
        del bpy.types.Scene.skip_triblock
    if "skip_quadblock" in bpy.types.Scene.bl_rna.properties:
        del bpy.types.Scene.skip_quadblock


# Asegurar que las clases estén registradas
classes = [
    GeometryToolsPanel,
    OBJECT_OT_FindObjects,
    OBJECT_OT_FindInvalidGeometry,
    OBJECT_OT_ResetName
]

if __name__ == "__main__":
    register()
