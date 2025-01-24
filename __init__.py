bl_info = {
    "name": "RaceTrackBuilder",
    "blender": (4, 2, 0),
    "category": "Object",
    "author": "Sir Uka",
    "version": (1, 0),
    "description": "A set of tools for building race tracks",
    "support": "COMMUNITY",
}

import bpy

# Importar cada uno de los scripts de herramientas
from . import add_quadblock_triblock
from . import align_vertices
from . import assets_browser
from . import fly_mode
from . import move_objects
from . import ps1_material_config
from . import relative_track
from . import render_menu
from . import snap_vertex_to_closest
from . import vertex_lighting
from . import extrude_separated_objects
from . import Find_invalid_data
from . import apply_settings


def register():
    # Registrar todos los módulos
    add_quadblock_triblock.register()
    align_vertices.register()
    assets_browser.register()
    fly_mode.register()
    move_objects.register()
    ps1_material_config.register()
    relative_track.register()
    render_menu.register()
    snap_vertex_to_closest.register()
    vertex_lighting.register()
    extrude_separated_objects.register()  # Corregido
    Find_invalid_data.register()  # Corregido
    apply_settings.register()  # Corregido

def unregister():
    # Desregistrar todos los módulos
    add_quadblock_triblock.unregister()
    align_vertices.unregister()
    assets_browser.unregister()
    fly_mode.unregister()
    move_objects.unregister()
    ps1_material_config.unregister()
    relative_track.unregister()
    render_menu.unregister()
    snap_vertex_to_closest.unregister()
    vertex_lighting.unregister()
    extrude_separated_objects.unregister()  # Corregido
    Find_invalid_data.unregister()  # Corregido
    apply_settings.unregister()  # Corregido

if __name__ == "__main__":
    register()
