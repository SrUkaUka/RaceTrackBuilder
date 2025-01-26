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
from . import simple_track

def register():
    # Registrar todos los módulos
    modules = [
        add_quadblock_triblock,
        align_vertices,
        assets_browser,
        fly_mode,
        move_objects,
        ps1_material_config,
        relative_track,
        render_menu,
        snap_vertex_to_closest,
        vertex_lighting,
        extrude_separated_objects,
        Find_invalid_data,
        apply_settings,
        simple_track,
    ]
    
    for module in modules:
        # Verificar si el módulo tiene una función de registro antes de llamarla
        if hasattr(module, 'register'):
            try:
                module.register()
            except Exception as e:
                print(f"Error registrando módulo {module.__name__}: {e}")

def unregister():
    # Desregistrar todos los módulos
    modules = [
        add_quadblock_triblock,
        align_vertices,
        assets_browser,
        fly_mode,
        move_objects,
        ps1_material_config,
        relative_track,
        render_menu,
        snap_vertex_to_closest,
        vertex_lighting,
        extrude_separated_objects,
        Find_invalid_data,
        apply_settings,
        simple_track,
    ]
    
    for module in modules:
        # Verificar si el módulo tiene una función de desregistro antes de llamarla
        if hasattr(module, 'unregister'):
            try:
                module.unregister()
            except Exception as e:
                print(f"Error desregistrando módulo {module.__name__}: {e}")

if __name__ == "__main__":
    register()
