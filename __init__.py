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
import pathlib
import os
from ramses_export import debug_utils
from ramses_export import utils
from ramses_export.ramses_inspector import RamsesInspector
from ramses_export.exporter import RamsesBlenderExporter
from bpy_extras.io_utils import ExportHelper
from bpy.props import (
    StringProperty,
    BoolProperty
)

log = debug_utils.get_debug_logger()


def menu_func_export(self, context):
    """Sets up the entry in the export menu when appropriately registered
    in __init__.py"""
    self.layout.operator(RamsesExportOperator.bl_idname, text='RAMSES Scenes (.ramses, .ramres)')


class RamsesExportOperator(bpy.types.Operator):
    bl_idname = "export_scene.ramses"
    bl_label = "Export as RAMSES scenes"

    use_filter = True
    use_filter_folder = True
    filter_folder: bpy.props.BoolProperty(default=True, options={'HIDDEN'})

    """The output directory. Must be named 'directory' as this is how
    'fileselect' expects it"""
    directory: bpy.props.StringProperty(name="Current export path",
                                        description="Path where the resulting scene files will be saved",
                                        subtype='DIR_PATH')

    emit_debug_files: bpy.props.BoolProperty(name='Emit debug files',
                                             default=True,
                                             description='Whether to emit a debug file with '
                                             + 'the carried out operations. If chosen, will '
                                             + 'write a debug.txt file')

    platform: bpy.props.EnumProperty(name='Platform',
                                     items=[('x11-egl-es-3-0', 'x11-egl-es-3-0', 'x11-egl-es-3-0'), # (identifier, name, description)
                                            ('wayland-ivi-egl-es-3-0', 'wayland-ivi-egl-es-3-0', 'wayland-ivi-egl-es-3-0'),
                                            ('wayland-shell-egl-es-3-0', 'wayland-shell-egl-es-3-0', 'wayland-shell-egl-es-3-0'),
                                            ('windows-wgl-4-2-core.exe', 'windows-wgl-4-2-core', 'windows-wgl-4-2-core'),
                                            ('windows-wgl-4-5.exe', 'windows-wgl-4-5', 'windows-wgl-4-5'),
                                            ('windows-wgl-es-3-0.exe', 'windows-wgl-es-3-0', 'windows-wgl-es-3-0')],
                                     description='Platform to use for previews')

    ui_tab: bpy.props.EnumProperty(items=(('GENERAL', "General", "General settings"),
                                          ('GLSL', "GLSL", "Use custom GLSL for meshes")),
                                   name="ui_tab",
                                   description="Export setting categories")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):

        if self.emit_debug_files and not debug_utils.debug_logger_set:
            debug_utils.setup_logging(f'{self.directory}debug.txt') # Master log file
            debug_utils.debug_logger_set = True

        exporter = RamsesBlenderExporter(bpy.data.scenes)
        exporter.extract_from_blender_scene()
        exporter.build_from_extracted_representations()

        for exportable_scene in exporter.get_exportable_scenes():

            exportable_scene.set_output_dir(self.directory)
            inspector = RamsesInspector(exportable_scene, addon_dir=utils.get_addon_path())

            if not exportable_scene.is_valid():
                validation_report = exportable_scene.get_validation_report()
                raise RuntimeError(validation_report)

            exportable_scene.save()
            inspector.load_viewer(platform=self.platform)

        return {'FINISHED'}

    # ------- User Interface --------------------
    def draw(self, context):
        layout = self.layout
        scn = context.scene

        self.layout.prop(self, 'ui_tab', expand=True)
        if self.ui_tab == 'GENERAL':
            self.draw_general_settings(layout, scn)
        elif self.ui_tab == 'GLSL':
            self.draw_glsl_settings(layout, scn)

    def draw_general_settings(self, layout, scn):
        col = layout.column()
        row = col.row(align=True)
        row.prop(self, 'emit_debug_files')
        row = col.row(align=True)
        row.prop(self, 'platform')

    def draw_glsl_settings(self, layout, scn):
        pass # TODO
    # ------- User Interface --------------------

    @classmethod
    def register(cls):
        """Add scene properties here if needed"""
        print('RamsesExportOperator registered.')

    @classmethod
    def unregister(cls):
        """Remove scene properties here if needed"""
        print('RamsesExportOperator unregistered')


classes = (
    # Add all classes that must be registered and unregistered
    RamsesExportOperator,
)

def register():
    """All classes that inherit from bpy must be registered / unregistered"""

    for c in classes:
        bpy.utils.register_class(c)

    # Append a entry to Blender's 'export' menu
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    print("RAMSES Scene Exporter: Add-on registered.")
    log.info("RAMSES Scene Exporter: Add-on registered.")

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    log.info("RAMSES Scene Exporter: Add-on unregistered.")
    print("RAMSES Scene Exporter: Add-on unregistered.")

