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
from ramses_export.ramses_inspector import RamsesInspector
from ramses_export.exporter import RamsesBlenderExporter
from bpy_extras.io_utils import ExportHelper
from bpy.props import (
    StringProperty,
    BoolProperty
)

log = debug_utils.get_debug_logger()

def addon_reload():
    bpy.ops.preferences.addon_disable(module=__name__)
    bpy.ops.preferences.addon_enable(module=__name__)
    reload_package(locals())

def auto_find_viewer_path():
    pwd = pathlib.Path.cwd()

    #TODO: improve this?
    viewer_bin = 'ramses-scene-viewer'
    viewer_suffix = ''

    if os.name == 'nt':
        viewer_suffix = 'windows'
    elif os.name == 'posix':
        # Favor X11, user can change it if desired.
        viewer_suffix = 'x11'

    file_name = f'{viewer_bin}-{viewer_suffix}*'
    matches = list(pwd.rglob(file_name))
    return matches[0] # The first match

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

    viewer_path: bpy.props.StringProperty(#name='Path to the RAMSES Scene Viewer',
                                          description='The RAMSES Scene Viewer aids '
                                          + 'in finding errors in the exported scene. '
                                          + 'The viewer for your platform should be located '
                                          + 'inside the bin directory of the installation '
                                          + 'directory. Leaving empty will cause the viewer '
                                          + 'to not launch, but specifying a incorrect path '
                                          + 'will cause an error',
                                          default=str(auto_find_viewer_path()))

    emit_debug_files: bpy.props.BoolProperty(name='Emit debug files',
                                             default=True,
                                             description='Whether to emit a debug file with '
                                             + 'the carried out operations. If chosen, will '
                                             + 'write a debug.txt file')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        addon_reload()

        if self.emit_debug_files:
            debug_utils.setup_logging(f'{self.directory}debug.txt') # Master log file

        exporter = RamsesBlenderExporter(bpy.data.scenes)
        exporter.extract_from_blender_scene()
        exporter.build_from_extracted_representations()

        for exportable_scene in exporter.get_exportable_scenes():

            viewer_path = pathlib.Path(self.viewer_path) if self.viewer_path else None
            exportable_scene.set_output_dir(self.directory)
            inspector = RamsesInspector(exportable_scene, viewer_path)
            inspector.load_viewer()

            if not exportable_scene.is_valid():
                validation_report = exportable_scene.get_validation_report()
                raise RuntimeError(validation_report)

            exportable_scene.save()

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        # UI draw code
        col = layout.column()
        row = col.row(align=True)

        row = row.split(factor=0.6)
        left_col = row.column()
        left_col.label(text='Absolute path to the RAMSES Scene Viewer')
        right_col = row.column()
        right_col.prop(self, 'viewer_path', text='')

        row = col.row()
        row.prop(self, 'emit_debug_files')

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

if __name__ == "__main__":
    # If run as a standalone package - execute the tests
    # TODO: consider if this is the best way to execute tests
    from ramses_export.tests import RunAllTests
    tests = RunAllTests()
    tests.execute()
