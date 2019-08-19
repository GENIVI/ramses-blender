#  -------------------------------------------------------------------------
#  Copyright (C) 2019 BMW AG
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

import os
import subprocess
import bpy
import unittest

from ramses_export.test.exporter_test_base import ExporterTestBase

from ramses_export import debug_utils
from ramses_export.ramses_inspector import RamsesInspector
from ramses_export.exporter import RamsesBlenderExporter
from ramses_export import RamsesPython
import ramses_export.intermediary_representation


class ExportMultipleLayersAndCollections_OneDisabledTest(ExporterTestBase, unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        ExporterTestBase.__init__(self)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_export_multiple_layers_and_collections_one_disabled(self):
        for exportable_scene in self.get_exportable_scenes_for_test(take_screenshot=True):
            self.assertTrue(exportable_scene.is_valid())
            layers = exportable_scene.scene_representation.layers
            self.assertTrue(len(layers), 1) # The other is disabled

            self.assertTrue(len(layers[0].children), 2) # Collection2, cube
            self.assertTrue(len(layers[0].children[0].children), 1) # Cube
            #TODO: Implement SceneObjectIterator to check the same structure on the RAMSES side

if __name__ == '__main__':
    suite_1 = unittest.defaultTestLoader.\
            loadTestsFromTestCase(ExportMultipleLayersAndCollections_OneDisabledTest)

    all_tests = unittest.TestSuite([suite_1])

    success = unittest.TextTestRunner().run(all_tests).wasSuccessful()
    if not success:
        raise Exception('Test "export multiple layers and collections: one disabled" failed')
