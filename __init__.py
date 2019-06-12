#  -------------------------------------------------------------------------
#  Copyright (C) 2019 Daniel Werner Lima Souza de Almeida
#                     dwlsalmeida at gmail dot com
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

bl_info = {
    "name": "RAMSES Scene Exporter",
    "author": "Daniel Lima de Almeida",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "View3D",
    "description": "A add-on for exporting RAMSES scenes from Blender scenes",
    "category": "Import-Export",
    "Warning": "Under development!",
    "wiki-url": "",
    "tracker-url": ""
}

# Copied from gltf-Blender-IO.
# NOTE: Most extensions take care when reloading imports due to caching
#
# Script reloading (if the user calls 'Reload Scripts' from Blender)
#
def reload_package(module_dict_main):
    import importlib
    from pathlib import Path

    def reload_package_recursive(current_dir, module_dict):
        for path in current_dir.iterdir():
            if "__init__" in str(path) or path.stem not in module_dict:
                continue

            if path.is_file() and path.suffix == ".py":
                importlib.reload(module_dict[path.stem])
            elif path.is_dir():
                reload_package_recursive(path, module_dict[path.stem].__dict__)

    reload_package_recursive(Path(__file__).parent, module_dict_main)

if "bpy" in locals():
    reload_package(locals())

import bpy # NOTE: the bpy import must come below the module reload code
from . import debug_utils
from .exporter import RamsesBlenderExporter


log = debug_utils.get_debug_logger()

def addon_reload():
    bpy.ops.preferences.addon_disable(module=__name__)
    bpy.ops.preferences.addon_enable(module=__name__)
    reload_package(locals())

class SceneDumpOperator(bpy.types.Operator):
    bl_idname = "object.scenedumpoperator"
    bl_label = "SceneDumpOperator"

    def execute(self, context):
        addon_reload()
        scene = bpy.context.scene

        debug_utils.setup_logging('debug.txt') # TODO: set up as an option for the end user.
        exporter = RamsesBlenderExporter(bpy.data.scenes)
        exporter.extract_from_blender_scene()
        exporter.build_from_extracted_representations()

        for exportable_scene in exporter.get_exportable_scenes():

            if not exportable_scene.is_valid():
                validation_report = exportable_scene.get_validation_report()
                raise RuntimeError(validation_report)

            exportable_scene.save()

        return {'FINISHED'}

def register():
    log.info("RAMSES Scene Exporter: Add-on registered.")
    bpy.utils.register_class(SceneDumpOperator)
    print("RAMSES Scene Exporter: Add-on registered.")


def unregister():
    bpy.utils.unregister_class(SceneDumpOperator)
    log.info("RAMSES Scene Exporter: Add-on unregistered.")
