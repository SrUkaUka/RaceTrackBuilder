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
        col.prop(context.scene, "find_option", text="")

        # Checkboxes for skipping triblock and quadblock validation
        col.prop(context.scene, "skip_triblock", text="No Triblock")
        col.prop(context.scene, "skip_quadblock", text="No Quadblock")

        # Botones
        col.operator("geometry.find_objects", text="Find")
        col.separator()
        col.operator("geometry.find_invalid", text="Find Invalid Geometry")
        col.separator()
        col.operator("geometry.reset_name", text="Reset Name")
        col.separator()
        col.operator("geometry.remove_invalid_data", text="Remove Invalid Data")


class OBJECT_OT_FindObjects(bpy.types.Operator):
    """Find objects and add suffixes based on the selection."""
    bl_idname = "geometry.find_objects"
    bl_label = "Find Objects"

    def execute(self, context):
        context.scene.find_executed = True  
        find_option = context.scene.find_option

        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=0)
        start_time = time.time()

        mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']

        for obj in mesh_objects:
            vertex_count = len(obj.data.vertices)
            edge_count = len(obj.data.edges)
            face_count = len(obj.data.polygons)

            # Si el objeto contiene algún NGon (cara con más de 4 vértices), se omite.
            if any(len(poly.vertices) > 4 for poly in obj.data.polygons):
                continue

            if find_option == 'TRIBLOCK' and vertex_count == 6 and edge_count == 9 and face_count == 4:
                obj.name = f"{obj.name}_triblock"
            elif find_option == 'QUADBLOCK' and vertex_count == 9 and edge_count == 12 and face_count == 4:
                obj.name = f"{obj.name}_quadblock"

        elapsed_time = time.time() - start_time
        self.report({'INFO'}, f"Find operation completed in {elapsed_time:.2f} seconds.")
        return {'FINISHED'}


class OBJECT_OT_FindInvalidGeometry(bpy.types.Operator):
    """Mark objects with invalid geometry or UVs by adding appropriate suffixes."""
    bl_idname = "geometry.find_invalid"
    bl_label = "Find Invalid Geometry"

    def execute(self, context):
        if not context.scene.get("find_executed", False):
            self.report({'WARNING'}, "You must run 'Find' first.")
            return {'CANCELLED'}

        skip_triblock = context.scene.skip_triblock
        skip_quadblock = context.scene.skip_quadblock

        # Validación previa de que se hayan encontrado al menos un triblock o quadblock (o se hayan marcado como skip)
        triblock_found = any(obj.name.endswith("_triblock") for obj in bpy.data.objects if obj.type == 'MESH')
        quadblock_found = any(obj.name.endswith("_quadblock") for obj in bpy.data.objects if obj.type == 'MESH')

        if not ((triblock_found or skip_triblock) and (quadblock_found or skip_quadblock)):
            self.report({'WARNING'}, "Both TRIBLOCK and QUADBLOCK must be found or skipped.")
            return {'CANCELLED'}

        for obj in bpy.data.objects:
            geometry_invalid = False
            uvs_invalid = False

            # Si no es MESH, se marca como geometría inválida.
            if obj.type != 'MESH':
                geometry_invalid = True
            else:
                vertex_count = len(obj.data.vertices)
                edge_count = len(obj.data.edges)
                face_count = len(obj.data.polygons)

                # Si contiene NGons, se marca como geometría inválida.
                if any(len(poly.vertices) > 4 for poly in obj.data.polygons):
                    geometry_invalid = True

                # Validación de geometría según el sufijo asignado.
                if obj.name.endswith("_triblock"):
                    if vertex_count != 6 or edge_count != 9 or face_count != 4:
                        geometry_invalid = True
                elif obj.name.endswith("_quadblock"):
                    if vertex_count != 9 or edge_count != 12 or face_count != 4:
                        geometry_invalid = True
                else:
                    # Si no tiene ninguno de los sufijos, se marca como geometría inválida.
                    geometry_invalid = True

                # Validación de UVs: Si existen capas de UV, se verifica que todas las coordenadas estén en rango [0, 1].
                if obj.data.uv_layers:
                    for uv_layer in obj.data.uv_layers:
                        for uv_data in uv_layer.data:
                            u, v = uv_data.uv.x, uv_data.uv.y
                            if u < 0 or u > 1 or v < 0 or v > 1:
                                uvs_invalid = True
                                break
                        if uvs_invalid:
                            break

            # Añadir sufijos según corresponda
            if geometry_invalid and "_invalid_geometry" not in obj.name:
                obj.name = f"{obj.name}_invalid_geometry"
            if uvs_invalid and "_invalid_uvs" not in obj.name:
                obj.name = f"{obj.name}_invalid_uvs"

        self.report({'INFO'}, "Invalid geometry/UVs marked.")
        return {'FINISHED'}


class OBJECT_OT_ResetName(bpy.types.Operator):
    """Remove '_invalid_geometry', '_invalid_uvs', '_quadblock', and '_triblock' suffixes from all objects."""
    bl_idname = "geometry.reset_name"
    bl_label = "Reset Name"

    def execute(self, context):
        for obj in bpy.data.objects:
            for suffix in ["_invalid_geometry", "_invalid_uvs", "_quadblock", "_triblock"]:
                if obj.name.endswith(suffix):
                    obj.name = obj.name.replace(suffix, "")
        self.report({'INFO'}, "Names reset.")
        return {'FINISHED'}


class OBJECT_OT_RemoveInvalidData(bpy.types.Operator):
    """Delete objects marked as invalid by geometry or UVs."""
    bl_idname = "geometry.remove_invalid_data"
    bl_label = "Remove Invalid Data"

    def execute(self, context):
        # Se buscan objetos que tengan los sufijos de geometría o UVs inválidas.
        invalid_objects = [
            obj for obj in bpy.data.objects
            if obj.name.endswith("_invalid_geometry") or obj.name.endswith("_invalid_uvs")
        ]
        count = len(invalid_objects)
        for obj in invalid_objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        self.report({'INFO'}, f"Removed {count} invalid objects.")
        return {'FINISHED'}


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

    del bpy.types.Scene.find_option
    del bpy.types.Scene.find_executed
    del bpy.types.Scene.skip_triblock
    del bpy.types.Scene.skip_quadblock


classes = [
    GeometryToolsPanel,
    OBJECT_OT_FindObjects,
    OBJECT_OT_FindInvalidGeometry,
    OBJECT_OT_ResetName,
    OBJECT_OT_RemoveInvalidData
]

if __name__ == "__main__":
    register()
