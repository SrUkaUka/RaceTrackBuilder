bl_info = {
    "name": "RaceTrackBuilder",
    "blender": (4, 2, 0),
    "category": "Object",
    "author": "Sir Uka",
    "version": (1, 0),
    "description": "A set of tools for building race tracks based on CTR limitations",
    "support": "COMMUNITY",
}

import bpy

# Importar cada uno de los scripts de herramientas
from . import add_quadblock_triblock
from . import extrude_separated_objects
from . import snap_vertex_to_closest
from . import proportional_editing
from . import align_vertices
from . import fly_mode
from . import remove_garbage
from . import move_objects
from . import assets_browser
from . import simple_track
from . import relative_track
from . import apply_settings
from . import ps1_material_config
from . import vertex_lighting
from . import render_menu
from . import Find_invalid_data
from . import basic_uv_tools
from . import skybox_gradient

def register():
    # Registrar todos los módulos
    modules = [
        add_quadblock_triblock,
        extrude_separated_objects,
        snap_vertex_to_closest,
        proportional_editing,
        align_vertices,
        fly_mode,
        remove_garbage,
        move_objects,
        assets_browser,
        simple_track,
        relative_track,
        apply_settings,
        ps1_material_config,
        vertex_lighting,
        render_menu,
        Find_invalid_data,
        basic_uv_tools,
        skybox_gradient,
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
        extrude_separated_objects,
        snap_vertex_to_closest,
        proportional_editing,
        align_vertices,
        fly_mode,
        remove_garbage,
        move_objects,
        assets_browser,
        simple_track,
        relative_track,
        apply_settings,
        ps1_material_config,
        vertex_lighting,
        render_menu,
        Find_invalid_data,
        basic_uv_tools,
        skybox_gradient,
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
