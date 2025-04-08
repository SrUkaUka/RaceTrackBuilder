import sys
import subprocess

# Intentar importar PIL; si falla, se instala Pillow automáticamente
try:
    from PIL import Image, ImageEnhance
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageEnhance

import bpy
import os
import re
from bpy.props import EnumProperty, BoolProperty, StringProperty, CollectionProperty, IntProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup
from bpy_extras.io_utils import ImportHelper

# ====================================================
# Función auxiliar para ordenar archivos de forma natural:
# Si el nombre del archivo (sin extensión) termina en números,
# se usará ese número para ordenar; de lo contrario se usa el nombre.
# ====================================================
def sort_key(file_path):
    name = os.path.splitext(os.path.basename(file_path))[0]
    match = re.search(r'(\d+)$', name)
    if match:
        return (0, int(match.group(1)))
    else:
        return (1, name)

# ====================================================
# PANEL PARA GENERAR ATLAS DE TEXTURAS
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
        layout.prop(scene, "use_custom_atlas_size", text="Other (Custom Atlas Size)")
        if scene.use_custom_atlas_size:
            row = layout.row(align=True)
            row.prop(scene, "custom_atlas_width", text="Width")
            row.prop(scene, "custom_atlas_height", text="Height")
            
        layout.separator()
        layout.label(text="Select Textures Width:")

        row = layout.row(align=True)
        row.prop(scene, "use_base_16", text="16")
        if scene.use_base_16:
            row.prop(scene, "base_16_second", text="Height")

        row = layout.row(align=True)
        row.prop(scene, "use_base_32", text="32")
        if scene.use_base_32:
            row.prop(scene, "base_32_second", text="Height")

        row = layout.row(align=True)
        row.prop(scene, "use_base_64", text="64")
        if scene.use_base_64:
            row.prop(scene, "base_64_second", text="Height")

        row = layout.row(align=True)
        row.prop(scene, "use_base_128", text="128")
        if scene.use_base_128:
            row.prop(scene, "base_128_second", text="Height")

        row = layout.row(align=True)
        row.prop(scene, "use_base_256", text="256")
        if scene.use_base_256:
            row.prop(scene, "base_256_second", text="Height")

        layout.separator()
        layout.prop(scene, "use_custom_dimensions", text="Other (Custom Dimensions)")
        if scene.use_custom_dimensions:
            row = layout.row(align=True)
            row.prop(scene, "custom_width", text="Width")
            row.prop(scene, "custom_height", text="Height")

        layout.separator()
        layout.operator("atlas.generate_combinations", text="Generate Atlas (Combined)")
        layout.separator()
        layout.operator("atlas.select_textures", text="Select Textures (Dynamic)")
        layout.separator()

# ====================================================
# Función común de cuantización con soporte para canal alfa:
# Se separa el canal alfa y se reintroduce después de cuantizar la parte RGB.
# ====================================================
def quantize_image(image_path, colors):
    try:
        img = Image.open(image_path).convert("RGBA")
        r, g, b, a = img.split()
        rgb = Image.merge("RGB", (r, g, b))
        rgb_quantized = rgb.convert("P", palette=Image.ADAPTIVE, colors=colors)
        rgb_quantized = rgb_quantized.convert("RGB")
        quantized_image = Image.merge("RGBA", (*rgb_quantized.split(), a))
        return quantized_image
    except Exception as e:
        print(f"Error procesando {image_path}: {e}")
        return None

# ====================================================
# OPERADOR PARA GENERAR ATLAS CON COMBINACIONES
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

        if scene.use_custom_atlas_size:
            atlas_width = scene.custom_atlas_width
            atlas_height = scene.custom_atlas_height
        else:
            atlas_size = int(scene.atlas_size)
            atlas_width = atlas_size
            atlas_height = atlas_size

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
        texture_files = [os.path.join(folder_path, f)
                         for f in os.listdir(folder_path)
                         if f.lower().endswith(('.png', '.jpg'))]
        return sorted(texture_files, key=sort_key)

    def create_texture_atlases(self, atlas_width, atlas_height, texture_files, allowed_combinations, atlas_colors, scene):
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
                try:
                    texture = Image.open(texture_path).convert("RGBA")
                except Exception as e:
                    print(f"Error procesando {texture_path}: {e}")
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
# OPERADOR PARA SELECCIONAR TEXTURAS Y GENERAR UN ATLAS DINÁMICO
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
        selected_files = sorted(selected_files, key=sort_key)
        if not selected_files:
            self.report({'WARNING'}, "No files selected!")
            return {'CANCELLED'}

        scene = context.scene
        atlas_colors = int(scene.atlas_colors)
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
        atlas_index = 1
        x_offset, y_offset = 0, 0
        max_row_height = 0
        output_dir = os.path.dirname(texture_files[0])
        atlas_image = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))

        for texture_path in texture_files:
            try:
                texture = Image.open(texture_path).convert("RGBA")
            except Exception as e:
                print(f"Error procesando {texture_path}: {e}")
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
# OPERADOR PARA RENOMBRAR TEXTURAS
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
        texture_files = sorted(texture_files, key=lambda f: sort_key(os.path.join(folder_path, f)))
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
# NUEVO OPERADOR Y PANEL PARA CONVERTIR COLORES DE TEXTURAS
# ====================================================
SATURATION_FACTOR = 1.2

class TextureColorSettings(PropertyGroup):
    colors: IntProperty(
        name="Colors",
        description="Define the number of colors for conversion",
        default=16,
        min=1,
        max=256
    )
    alpha: BoolProperty(
        name="Alpha",
        description="Aplicar procesamiento especial para imágenes con canal alfa (pone fondo negro y lo elimina)",
        default=False
    )

class OT_SelectTexturesConvertColors(Operator, ImportHelper):
    bl_idname = "file.select_textures_convert_colors"
    bl_label = "Select Textures and Convert Colors"

    files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: StringProperty(
        name="Directory",
        description="Directory of the selected textures",
        maxlen=1024,
        subtype='DIR_PATH'
    )

    def execute(self, context):
        settings = context.scene.texture_color_settings
        num_colors = settings.colors
        use_alpha = settings.alpha

        folder = self.directory
        for file_elem in self.files:
            file_path = os.path.join(folder, file_elem.name)
            new_path = self.convert_to_n_colors(file_path, num_colors, use_alpha)
            if new_path:
                self.report({'INFO'}, f"Saved: {os.path.basename(new_path)}")
        return {'FINISHED'}

    def convert_to_n_colors(self, image_path, n_colors, use_alpha):
        try:
            # Abrir la imagen original en modo RGBA
            image_orig = Image.open(image_path).convert("RGBA")
            if use_alpha:
                # Proceso con fondo negro para imágenes con alfa (procedimiento común)
                background = Image.new("RGBA", image_orig.size, (0, 0, 0, 255))
                image_solid = Image.alpha_composite(background, image_orig)
                image_rgb = image_solid.convert("RGB")
                # Determinar si hay píxeles semitransparentes en la imagen original
                semitransparent = image_orig.getchannel("A").getextrema()[0] < 255
                quantize_colors = n_colors + 1 if semitransparent else n_colors
                # Aumentar la saturación y cuantizar la imagen (con fondo negro)
                image_sat = ImageEnhance.Color(image_rgb).enhance(SATURATION_FACTOR)
                quantized = image_sat.quantize(colors=quantize_colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
                final_image = ImageEnhance.Color(quantized.convert("RGB")).enhance(1 / SATURATION_FACTOR)
                # Convertir a RGBA para manipular la transparencia
                final_image = final_image.convert("RGBA")
                pixels = final_image.load()
                for y in range(final_image.height):
                    for x in range(final_image.width):
                        r, g, b, a = pixels[x, y]
                        # Si el píxel es puro negro, lo hacemos transparente
                        if (r, g, b) == (0, 0, 0):
                            pixels[x, y] = (0, 0, 0, 0)
                        else:
                            pixels[x, y] = (r, g, b, 255)
            else:
                # Proceso normal sin componer sobre fondo negro
                image_rgb = image_orig.convert("RGB")
                # Determinar si hay píxeles semitransparentes en la imagen original
                semitransparent = image_orig.getchannel("A").getextrema()[0] < 255
                quantize_colors = n_colors + 1 if semitransparent else n_colors
                image_sat = ImageEnhance.Color(image_rgb).enhance(SATURATION_FACTOR)
                quantized = image_sat.quantize(colors=quantize_colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
                final_image = ImageEnhance.Color(quantized.convert("RGB")).enhance(1 / SATURATION_FACTOR)
                # Convertir a RGBA y conservar el canal alfa original
                final_image = final_image.convert("RGBA")
                final_image.putalpha(image_orig.split()[-1])

            base_name, ext = os.path.splitext(image_path)
            new_file_name = f"{base_name}_quantized_{n_colors}{ext}"
            final_image.save(new_file_name, optimize=True)

            print(f"Image saved as: {new_file_name}")
            return new_file_name
        except Exception as e:
            self.report({'ERROR'}, f"Error converting {image_path}: {e}")
            return None

class OT_IncreaseColorCount(Operator):
    bl_idname = "texture.increase_color_count"
    bl_label = "Increase Color Count"
    def execute(self, context):
        settings = context.scene.texture_color_settings
        if settings.colors < 256:
            settings.colors += 1
        return {'FINISHED'}

class OT_DecreaseColorCount(Operator):
    bl_idname = "texture.decrease_color_count"
    bl_label = "Decrease Color Count"
    def execute(self, context):
        settings = context.scene.texture_color_settings
        if settings.colors > 1:
            settings.colors -= 1
        return {'FINISHED'}

class PT_ConvertColorsPanel(Panel):
    bl_idname = "PT_ConvertColorsPanel"
    bl_label = "Convert Texture Colors"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Atlas'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.texture_color_settings

        row = layout.row(align=True)
        row.operator("texture.decrease_color_count", text="<")
        row.prop(settings, "colors", slider=True)
        row.operator("texture.increase_color_count", text=">")
        
        # Nuevo checkbox para activar el procesamiento con alfa
        layout.prop(settings, "alpha", text="Alpha")

        layout.operator("file.select_textures_convert_colors", text="Convert Texture Colors")

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
        name="Colors",
        default=16,
        min=1,
        max=256
    )
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
    bpy.utils.register_class(TextureColorSettings)
    bpy.types.Scene.texture_color_settings = PointerProperty(type=TextureColorSettings)
    bpy.utils.register_class(OT_SelectTexturesConvertColors)
    bpy.utils.register_class(OT_IncreaseColorCount)
    bpy.utils.register_class(OT_DecreaseColorCount)
    bpy.utils.register_class(PT_ConvertColorsPanel)

def unregister():
    bpy.utils.unregister_class(TextureCombinationPanel)
    bpy.utils.unregister_class(GenerateCombinationAtlasOperator)
    bpy.utils.unregister_class(SelectTexturesOperator)
    bpy.utils.unregister_class(NumerateTexturesOperator)
    bpy.utils.unregister_class(PT_ConvertColorsPanel)
    bpy.utils.unregister_class(OT_SelectTexturesConvertColors)
    bpy.utils.unregister_class(OT_IncreaseColorCount)
    bpy.utils.unregister_class(OT_DecreaseColorCount)
    bpy.utils.unregister_class(TextureColorSettings)
    del bpy.types.Scene.texture_color_settings
    unregister_properties()

if __name__ == "__main__":
    register()
