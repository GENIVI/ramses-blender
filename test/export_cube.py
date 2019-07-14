#  -------------------------------------------------------------------------
#  Copyright (C) 2019 BMW AG
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

import os
import bpy

from ramses_export.test.exporter_test_base import ExporterTestBase

from ramses_export import debug_utils
from ramses_export.ramses_inspector import RamsesInspector
from ramses_export.exporter import RamsesBlenderExporter
from ramses_export import RamsesPython


class ExportCubeTest(ExporterTestBase):
    def execute(self):

        exporter = RamsesBlenderExporter(bpy.data.scenes)
        exporter.extract_from_blender_scene()
        exporter.build_from_extracted_representations()

        if len(exporter.get_exportable_scenes()) != 1:
            raise AssertionError(f'Expected one scene, found {len(exporter.get_exportable_scenes())}')
        exportable_scene = exporter.get_exportable_scenes()[0]
        exportable_scene.set_output_dir(self.working_dir)

        if not exportable_scene.is_valid():
            validation_report = exportable_scene.get_validation_report()
            raise AssertionError(validation_report)

        exportable_scene.save()
        # TODO resolution should come from the exported scene's camera viewport setting
        window = exporter.ramses.openWindow(800, 600, 0, 0)
        window.showScene(exportable_scene.ramses_scene)
        window.takeScreenshot(os.path.join(self.working_dir, f'screenshot.png'))
        window.close()

        with open(os.path.join(self.working_dir, f'scene.txt'), 'w') as file:
            file.write(exportable_scene.ramses_scene.toText())
        with open(os.path.join(self.working_dir, f'scene_cube.txt'), 'w') as file:
            file.write(exportable_scene.ramses_scene.toText('Cube'))

if __name__ == "__main__":
    test = ExportCubeTest()
    test.execute()
