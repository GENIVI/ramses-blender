
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
import ramses_export.debug_utils
import ramses_export.exporter
import ramses_export.ramses_inspector
import ramses_export.RamsesPython

from ramses_export.test.exporter_test_base import ExporterTestBase


class TestExportCubeRotatedX30(ExporterTestBase, unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        ExporterTestBase.__init__(self)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_rotated_x_30(self):


        import math
        sin = math.sin(math.radians(30))
        cos = math.cos(math.radians(30))

        for exportable_scene in self.get_exportable_scenes_for_test():

            expected_final_transform = []
            # This was obtained by running Blender with the file above, exporting,
            # visually inspecting the output for success and then querying the
            # resulting matrix with a debugger.
            col1 = [1.0, 0.0, 0.0, 0.0]
            col2 = [0.0, cos, sin, 0.0]
            col3 = [0.0, -sin, cos, 0.0]
            col4 = [0.0, 0.0, 0.0, 1.0]

            expected_final_transform.extend(col1)
            expected_final_transform.extend(col2)
            expected_final_transform.extend(col3)
            expected_final_transform.extend(col4)

            cube = exportable_scene.ramses_scene.findObjectByName('Cube')
            cube_node = ramses_export.RamsesPython.toNode(cube)

            actual_transform = cube_node.getModelMatrix()

            assert len(expected_final_transform) == 16
            assert len(actual_transform) == 16

            index = 0
            for expected, actual in zip(expected_final_transform, actual_transform):
                self.assertAlmostEqual(expected, actual, places=3, msg=f'on index {index}')
                index += 1

if __name__ == '__main__':
    suite_1 = unittest.defaultTestLoader.\
            loadTestsFromTestCase(TestExportCubeRotatedX30)

    all_tests = unittest.TestSuite([suite_1])

    success = unittest.TextTestRunner().run(all_tests).wasSuccessful()
    if not success:
        raise Exception('Test "cube rotated X by 30 degrees" failed.')
