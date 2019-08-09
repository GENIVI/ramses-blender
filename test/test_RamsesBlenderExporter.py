
#  -------------------------------------------------------------------------
#  Copyright (C) 2019 Daniel Werner Lima Souza de Almeida
#                     dwlsalmeida@gmail.com
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------


import unittest
import bpy
import os
import ramses_export.debug_utils
import ramses_export.exporter
import ramses_export.ramses_inspector
import ramses_export.RamsesPython

from ramses_export.test.exporter_test_base import ExporterTestBase


class TestRamsesBlenderExporter(ExporterTestBase, unittest.TestCase):
    def __init__(self, methodName='runTest'):
        # Deriving from ExporterTestBase makes passing arguments easier
        unittest.TestCase.__init__(self, methodName)
        ExporterTestBase.__init__(self)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_default_scene_does_not_crash_blender(self):
        exporter = ramses_export.exporter.RamsesBlenderExporter(bpy.data.scenes)
        exporter.extract_from_blender_scene()
        exporter.build_from_extracted_representations()

        for exportable_scene in exporter.get_exportable_scenes():

            if not exportable_scene.is_valid():
                validation_report = exportable_scene.get_validation_report()
                raise RuntimeError(validation_report)

    def test_default_scene_viewer_does_not_crash_blender(self):
        exporter = ramses_export.exporter.RamsesBlenderExporter(bpy.data.scenes)
        exporter.extract_from_blender_scene()
        exporter.build_from_extracted_representations()

        for exportable_scene in exporter.get_exportable_scenes():
            exportable_scene.set_output_dir(self.working_dir)
            exportable_scene.save() # Can't see what we do not save
            inspector = ramses_export.ramses_inspector.RamsesInspector(exportable_scene, addon_dir=self.addon_path)
            inspector.load_viewer(self.platform)

            if not exportable_scene.is_valid():
                validation_report = exportable_scene.get_validation_report()
                raise RuntimeError(validation_report)

            inspector.close_viewer()