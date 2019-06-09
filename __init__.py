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

def in_development_mode():
    return 'bpy' in locals()

import bpy
from . import debug_utils
from .exporter import RamsesBlenderExporter


log = debug_utils.get_debug_logger()


class SceneDumpOperator(bpy.types.Operator):
    bl_idname = "object.scenedumpoperator"
    bl_label = "SceneDumpOperator"

    def execute(self, context):
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
