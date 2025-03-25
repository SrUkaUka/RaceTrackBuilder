import bpy
import os
from bpy.props import EnumProperty, BoolProperty, StringProperty, CollectionProperty, IntProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from PIL import Image

# ====================================================
# Panel único para selección de combinaciones y acciones
# ====================================================
class TextureCombinationPanel(Panel):
    """Panel para seleccionar combinaciones de dimensiones y generar atlas"""
    bl_label = "Texture Atlas Generator"
    bl_idname = "VIEW3D_PT_texture_combination"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Atlas'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Select Atlas Size:")
        layout.prop(scene, "atlas_size")
        # Se añade opción para tamaño de atlas personalizado
        layout.prop(scene, "use_custom_atlas_size", text="Other (Custom Atlas Size)")
        if scene.use_custom_atlas_size:
            row = layout.row(align=True)
            row.prop(scene, "custom_atlas_width", text="Width")
            row.prop(scene, "custom_atlas_height", text="Height")
            
        layout.prop(scene, "atlas_colors", text="Number of Colors")
        
        layout.separator()
        layout.label(text="Selecciona Dimensiones Base:")

        # Fila para base 16
        row = layout.row(align=True)
        row.prop(scene, "use_base_16", text="16")
        if scene.use_base_16:
            row.prop(scene, "base_16_second", text="Secundaria")

        # Fila para base 32
        row = layout.row(align=True)
        row.prop(scene, "use_base_32", text="32")
        if scene.use_base_32:
            row.prop(scene, "base_32_second", text="Secundaria")

        # Fila para base 64
        row = layout.row(align=True)
        row.prop(scene, "use_base_64", text="64")
        if scene.use_base_64:
            row.prop(scene, "base_64_second", text="Secundaria")

        # Fila para base 128
        row = layout.row(align=True)
        row.prop(scene, "use_base_128", text="128")
        if scene.use_base_128:
            row.prop(scene, "base_128_second", text="Secundaria")

        # Fila para base 256
        row = layout.row(align=True)
        row.prop(scene, "use_base_256", text="256")
        if scene.use_base_256:
            row.prop(scene, "base_256_second", text="Secundaria")

        layout.separator()
        # Opción "Other" para dimensiones personalizadas
        layout.prop(scene, "use_custom_dimensions", text="Other (Custom Dimensions)")
        if scene.use_custom_dimensions:
            row = layout.row(align=True)
            row.prop(scene, "custom_width", text="Width")
            row.prop(scene, "custom_height", text="Height")

        layout.separator()
        # Botón para generar atlas según combinaciones seleccionadas (abre explorador de archivos)
        layout.operator("atlas.generate_combinations", text="Generar Atlas (Combinaciones)")
        layout.separator()
        # Botón para seleccionar texturas manualmente y generar atlas dinámico
        layout.operator("atlas.select_textures", text="Select Textures (Dynamic)")
        layout.separator()
        # Se ha quitado el botón Numerate Textures
        layout.separator()
        # Botón para cambiar el número de colores de una imagen seleccionada (nuevo flujo)
        layout.operator("atlas.change_texture_colors", text="Change Texture Colors")


# ====================================================
# Función común de cuantización (convertir a RGB, paleta adaptativa y reconversión a RGBA)
# ====================================================
def quantize_image(image_path, colors):
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        img_reduced = img.convert("P", palette=Image.ADAPTIVE, colors=colors)
        return img_reduced.convert("RGBA")
    except Exception as e:
        print(f"Error procesando {image_path}: {e}")
        return None


# ====================================================
# Operador para generar atlas usando las combinaciones seleccionadas  
# (abre el explorador de archivos para elegir el origen de las texturas)
# ====================================================
class GenerateCombinationAtlasOperator(Operator, ImportHelper):
    """Genera atlas agrupando las texturas según las combinaciones seleccionadas.
    Abre el explorador de archivos para elegir el origen de las texturas."""
    bl_idname = "atlas.generate_combinations"
    bl_label = "Generar Atlas (Combinaciones)"
    filter_glob: StringProperty(default="*.png;*.jpg", options={'HIDDEN'})

    def execute(self, context):
        scene = context.scene
        atlas_colors = int(scene.atlas_colors)
        file_path = self.filepath
        folder_path = os.path.dirname(file_path)

        # Determinar dimensiones del atlas (cuadrado o personalizado)
        if scene.use_custom_atlas_size:
            atlas_width = scene.custom_atlas_width
            atlas_height = scene.custom_atlas_height
        else:
            atlas_size = int(scene.atlas_size)
            atlas_width = atlas_size
            atlas_height = atlas_size

        # Recoger las combinaciones activas (por ejemplo, "16x32")
        combinations = []
        if scene.use_base_16:
            combinations.append(f"16x{scene.base_16_second}")
        if scene.use_base_32:
            combinations.append(f"32x{scene.base_32_second}")
        if scene.use_base_64:
            combinations.append(f"64x{scene.base_64_second}")
        if scene.use_base_128:
            combinations.append(f"128x{scene.base_128_second}")
        if scene.use_base_256:
            combinations.append(f"256x{scene.base_256_second}")
        # Incluir opción personalizada si está activada
        if scene.use_custom_dimensions:
            combinations.append(f"{scene.custom_width}x{scene.custom_height}")

        if not combinations:
            self.report({'WARNING'}, "No se ha seleccionado ninguna dimensión base!")
            return {'CANCELLED'}

        texture_files = self.get_texture_files(folder_path)
        self.create_texture_atlases(atlas_width, atlas_height, texture_files, combinations, atlas_colors, scene)
        self.report({'INFO'}, f"Atlas generados para combinaciones: {', '.join(combinations)}")
        return {'FINISHED'}

    def get_texture_files(self, folder_path):
        """Obtiene los archivos de imagen de la carpeta seleccionada"""
        texture_files = [os.path.join(folder_path, f)
                         for f in os.listdir(folder_path)
                         if f.lower().endswith(('.png', '.jpg'))]
        return sorted(texture_files)

    def create_texture_atlases(self, atlas_width, atlas_height, texture_files, allowed_combinations, atlas_colors, scene):
        """
        Agrupa las texturas según su combinación "ancho x alto" y crea un atlas por cada grupo.
        Solo se procesan aquellas imágenes cuya combinación (por ejemplo, "16x32") esté permitida.
        Se utiliza la función de cuantización común para aplicar la reducción de colores.
        """
        # Crear un diccionario para agrupar: clave = "WxH"
        grouped_textures = {comb: [] for comb in allowed_combinations}
        for texture_path in texture_files:
            try:
                texture = Image.open(texture_path)
            except Exception as e:
                print(f"Error abriendo {texture_path}: {e}")
                continue
            w, h = texture.size
            comb = f"{w}x{h}"
            if comb in grouped_textures:
                grouped_textures[comb].append(texture_path)

        # Para cada grupo, crear uno o más atlas
        for comb, images in grouped_textures.items():
            if not images:
                continue
            atlas_index = 1
            x_offset, y_offset = 0, 0
            atlas_image = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
            used_textures = set()
            for texture_path in images:
                if texture_path in used_textures:
                    continue
                # Se aplica la función común de cuantización
                texture = quantize_image(texture_path, atlas_colors)
                if texture is None:
                    continue
                img_width, img_height = texture.size
                if x_offset + img_width > atlas_width:
                    x_offset = 0
                    y_offset += img_height
                if y_offset + img_height > atlas_height:
                    atlas_output_path = self.get_unique_path(os.path.dirname(texture_files[0]),
                                                             f"texture_atlas_{comb}", ".png", atlas_index)
                    atlas_image.save(atlas_output_path)
                    print(f"✅ Atlas guardado: {atlas_output_path}")
                    self.load_texture_into_blender(atlas_output_path)
                    atlas_index += 1
                    atlas_image = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
                    x_offset, y_offset = 0, 0
                atlas_image.paste(texture, (x_offset, y_offset), texture)
                x_offset += img_width
                used_textures.add(texture_path)
            if images:
                atlas_output_path = self.get_unique_path(os.path.dirname(texture_files[0]),
                                                         f"texture_atlas_{comb}", ".png", atlas_index)
                atlas_image.save(atlas_output_path)
                print(f"✅ Atlas guardado: {atlas_output_path}")
                self.load_texture_into_blender(atlas_output_path)

    def get_unique_path(self, output_dir, base_name, ext, start_index):
        """Genera un nombre de archivo único para evitar sobrescribir archivos existentes."""
        index = start_index
        while True:
            candidate = os.path.join(output_dir, f"{base_name}_{index}{ext}")
            if not os.path.exists(candidate):
                return candidate
            index += 1

    def load_texture_into_blender(self, image_path):
        """Carga el atlas en Blender y lo asigna a un material nuevo"""
        try:
            img = bpy.data.images.load(image_path)
        except Exception as e:
            print(f"Error cargando imagen {image_path}: {e}")
            return
        mat = bpy.data.materials.new(name="AtlasMaterial_Combination")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex_node.image = img
        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_node.outputs['Color'])
        if bpy.context.object:
            obj = bpy.context.object
            if not obj.data.materials:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat


# ====================================================
# Operador para seleccionar texturas manualmente y generar un atlas dinámico
# ====================================================
class SelectTexturesOperator(Operator, ImportHelper):
    """Permite seleccionar manualmente texturas (tamaños variados) y generar un atlas dinámico."""
    bl_idname = "atlas.select_textures"
    bl_label = "Select Textures"
    files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')
    filter_glob: StringProperty(default="*.png;*.jpg", options={'HIDDEN'})

    def execute(self, context):
        selected_files = [os.path.join(self.directory, f.name) for f in self.files]
        if not selected_files:
            self.report({'WARNING'}, "No files selected!")
            return {'CANCELLED'}

        scene = context.scene
        atlas_colors = int(scene.atlas_colors)
        # Determinar dimensiones del atlas (cuadrado o personalizado)
        if scene.use_custom_atlas_size:
            atlas_width = scene.custom_atlas_width
            atlas_height = scene.custom_atlas_height
        else:
            atlas_size = int(scene.atlas_size)
            atlas_width = atlas_size
            atlas_height = atlas_size

        self.create_dynamic_atlas(atlas_width, atlas_height, selected_files, atlas_colors)
        self.report({'INFO'}, f"Atlas dinámico creado a partir de {len(selected_files)} texturas seleccionadas.")
        return {'FINISHED'}

    def create_dynamic_atlas(self, atlas_width, atlas_height, texture_files, atlas_colors):
        """
        Crea un atlas dinámico sin importar el tamaño original de cada textura.
        Se realiza un packing simple colocando las texturas en filas.
        Se utiliza la función común de cuantización para aplicar la reducción de colores.
        """
        atlas_index = 1
        x_offset, y_offset = 0, 0
        max_row_height = 0
        output_dir = os.path.dirname(texture_files[0])
        atlas_image = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))

        for texture_path in texture_files:
            texture = quantize_image(texture_path, atlas_colors)
            if texture is None:
                continue
            img_width, img_height = texture.size

            if x_offset + img_width > atlas_width:
                x_offset = 0
                y_offset += max_row_height
                max_row_height = 0

            if y_offset + img_height > atlas_height:
                atlas_output_path = self.get_unique_path(output_dir, "texture_atlas_dynamic", ".png", atlas_index)
                atlas_image.save(atlas_output_path)
                print(f"✅ Atlas dinámico guardado: {atlas_output_path}")
                self.load_texture_into_blender(atlas_output_path)
                atlas_index += 1
                atlas_image = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
                x_offset, y_offset = 0, 0
                max_row_height = 0

            atlas_image.paste(texture, (x_offset, y_offset), texture)
            x_offset += img_width
            if img_height > max_row_height:
                max_row_height = img_height

        atlas_output_path = self.get_unique_path(output_dir, "texture_atlas_dynamic", ".png", atlas_index)
        atlas_image.save(atlas_output_path)
        print(f"✅ Atlas dinámico guardado: {atlas_output_path}")
        self.load_texture_into_blender(atlas_output_path)

    def get_unique_path(self, output_dir, base_name, ext, start_index):
        index = start_index
        while True:
            candidate = os.path.join(output_dir, f"{base_name}_{index}{ext}")
            if not os.path.exists(candidate):
                return candidate
            index += 1

    def load_texture_into_blender(self, image_path):
        try:
            img = bpy.data.images.load(image_path)
        except Exception as e:
            print(f"Error cargando imagen {image_path}: {e}")
            return
        mat = bpy.data.materials.new(name="AtlasMaterial_Dynamic")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex_node.image = img
        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_node.outputs['Color'])
        if bpy.context.object:
            obj = bpy.context.object
            if not obj.data.materials:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat


# ====================================================
# Operador para renombrar texturas
# ====================================================
class NumerateTexturesOperator(Operator, ImportHelper):
    """Renombra las texturas agregándoles un sufijo numérico"""
    bl_idname = "atlas.numerate_textures"
    bl_label = "Numerate Textures"
    filter_glob: StringProperty(default="*.png;*.jpg", options={'HIDDEN'})

    def execute(self, context):
        folder_path = os.path.dirname(self.filepath)
        self.numerate_textures(folder_path)
        return {'FINISHED'}

    def numerate_textures(self, folder_path):
        texture_files = [f for f in os.listdir(folder_path)
                         if f.lower().endswith(('.png', '.jpg'))]
        texture_files.sort()
        for index, filename in enumerate(texture_files, start=1):
            name, ext = os.path.splitext(filename)
            new_name = f"{name}_{index:03d}{ext}"
            old_path = os.path.join(folder_path, filename)
            new_path = os.path.join(folder_path, new_name)
            if old_path != new_path:
                os.rename(old_path, new_path)
                print(f"✅ '{filename}' → '{new_name}'")
        print("✅ Todas las texturas han sido numeradas correctamente.")


# ====================================================
# NUEVO OPERADOR: Cambiar la cantidad de colores de una o varias imágenes seleccionadas
# ====================================================
class ChangeTextureColorsOperator(Operator, ImportHelper):
    """Cambia la cantidad de colores de una o varias imágenes seleccionadas al número especificado, manteniendo mayor detalle"""
    bl_idname = "atlas.change_texture_colors"
    bl_label = "Change Texture Colors"
    filter_glob: StringProperty(default="*.png;*.jpg;*.jpeg", options={'HIDDEN'})
    files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        scene = context.scene
        atlas_colors = int(scene.atlas_colors)
        
        # Obtener la lista de archivos seleccionados
        selected_files = []
        if self.files:
            selected_files = [os.path.join(self.directory, f.name) for f in self.files]
        elif self.filepath:
            selected_files = [self.filepath]
            
        if not selected_files:
            self.report({'WARNING'}, "No se seleccionó ninguna imagen.")
            return {'CANCELLED'}

        for file_path in selected_files:
            # Se utiliza la función común de cuantización para cada imagen
            img_reduced = quantize_image(file_path, atlas_colors)
            if img_reduced is None:
                self.report({'ERROR'}, f"Error procesando la imagen: {file_path}")
                continue

            # Guardar la imagen reducida en un archivo nuevo con un nombre único
            output_path = self.get_unique_path(os.path.dirname(file_path), "texture_quantized", ".png", 1)
            img_reduced.save(output_path)
            self.report({'INFO'}, f"Imagen procesada y guardada en: {output_path}")

            # Cargar la textura resultante en Blender y asignarla al objeto activo
            self.load_texture_into_blender(output_path)
        return {'FINISHED'}

    def get_unique_path(self, output_dir, base_name, ext, start_index):
        """Genera un nombre de archivo único para evitar sobrescribir archivos existentes."""
        index = start_index
        while True:
            candidate = os.path.join(output_dir, f"{base_name}_{index}{ext}")
            if not os.path.exists(candidate):
                return candidate
            index += 1

    def load_texture_into_blender(self, image_path):
        """Carga la imagen procesada en Blender y la asigna al material del objeto activo"""
        try:
            img = bpy.data.images.load(image_path)
        except Exception as e:
            print(f"Error cargando imagen {image_path}: {e}")
            return

        obj = bpy.context.active_object
        if not obj or obj.type != 'MESH':
            print("No hay objeto activo o el objeto seleccionado no es un mesh.")
            return

        if not obj.data.materials:
            mat = bpy.data.materials.new(name="AtlasMaterial_SingleTexture")
            mat.use_nodes = True
            obj.data.materials.append(mat)
        else:
            mat = obj.data.materials[0]

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex_node.image = img
        mat.node_tree.links.new(bsdf.inputs["Base Color"], tex_node.outputs["Color"])


# ====================================================
# Funciones para registrar y eliminar propiedades del escenario
# ====================================================
def register_properties():
    bpy.types.Scene.atlas_size = EnumProperty(
        name="Atlas Size",
        items=[('64', '64x64', ''), ('128', '128x128', ''), ('256', '256x256', '')],
        default='256'
    )
    bpy.types.Scene.atlas_colors = IntProperty(
        name="Number of Colors",
        default=16,
        min=1,
        max=256
    )
    # Propiedades para tamaño de atlas personalizado
    bpy.types.Scene.use_custom_atlas_size = BoolProperty(name="Other (Custom Atlas Size)", default=False)
    bpy.types.Scene.custom_atlas_width = IntProperty(name="Atlas Width", default=256, min=1)
    bpy.types.Scene.custom_atlas_height = IntProperty(name="Atlas Height", default=256, min=1)

    bpy.types.Scene.use_base_16 = BoolProperty(name="16", default=False)
    bpy.types.Scene.use_base_32 = BoolProperty(name="32", default=False)
    bpy.types.Scene.use_base_64 = BoolProperty(name="64", default=False)
    bpy.types.Scene.use_base_128 = BoolProperty(name="128", default=False)
    bpy.types.Scene.use_base_256 = BoolProperty(name="256", default=False)
    bpy.types.Scene.base_16_second = EnumProperty(
        name="Segunda dimensión para 16",
        items=[('16', "16", ""), ('32', "32", ""), ('64', "64", ""), ('128', "128", "")],
        default='16'
    )
    bpy.types.Scene.base_32_second = EnumProperty(
        name="Segunda dimensión para 32",
        items=[('16', "16", ""), ('32', "32", ""), ('64', "64", ""), ('128', "128", "")],
        default='16'
    )
    bpy.types.Scene.base_64_second = EnumProperty(
        name="Segunda dimensión para 64",
        items=[('16', "16", ""), ('32', "32", ""), ('64', "64", ""), ('128', "128", "")],
        default='16'
    )
    bpy.types.Scene.base_128_second = EnumProperty(
        name="Segunda dimensión para 128",
        items=[('16', "16", ""), ('32', "32", ""), ('64', "64", ""), ('128', "128", "")],
        default='16'
    )
    bpy.types.Scene.base_256_second = EnumProperty(
        name="Segunda dimensión para 256",
        items=[('16', "16", ""), ('32', "32", ""), ('64', "64", ""), ('128', "128", "")],
        default='16'
    )
    # Propiedades para la opción "Other" (dimensiones personalizadas)
    bpy.types.Scene.use_custom_dimensions = BoolProperty(name="Other", default=False)
    bpy.types.Scene.custom_width = IntProperty(name="Custom Width", default=64, min=1)
    bpy.types.Scene.custom_height = IntProperty(name="Custom Height", default=64, min=1)

def unregister_properties():
    del bpy.types.Scene.atlas_size
    del bpy.types.Scene.atlas_colors
    del bpy.types.Scene.use_custom_atlas_size
    del bpy.types.Scene.custom_atlas_width
    del bpy.types.Scene.custom_atlas_height
    del bpy.types.Scene.use_base_16
    del bpy.types.Scene.use_base_32
    del bpy.types.Scene.use_base_64
    del bpy.types.Scene.use_base_128
    del bpy.types.Scene.use_base_256
    del bpy.types.Scene.base_16_second
    del bpy.types.Scene.base_32_second
    del bpy.types.Scene.base_64_second
    del bpy.types.Scene.base_128_second
    del bpy.types.Scene.base_256_second
    del bpy.types.Scene.use_custom_dimensions
    del bpy.types.Scene.custom_width
    del bpy.types.Scene.custom_height


# ====================================================
# Registro en Blender
# ====================================================
def register():
    register_properties()
    bpy.utils.register_class(TextureCombinationPanel)
    bpy.utils.register_class(GenerateCombinationAtlasOperator)
    bpy.utils.register_class(SelectTexturesOperator)
    bpy.utils.register_class(NumerateTexturesOperator)
    bpy.utils.register_class(ChangeTextureColorsOperator)

def unregister():
    bpy.utils.unregister_class(TextureCombinationPanel)
    bpy.utils.unregister_class(GenerateCombinationAtlasOperator)
    bpy.utils.unregister_class(SelectTexturesOperator)
    bpy.utils.unregister_class(NumerateTexturesOperator)
    bpy.utils.unregister_class(ChangeTextureColorsOperator)
    unregister_properties()

if __name__ == "__main__":
    register()
