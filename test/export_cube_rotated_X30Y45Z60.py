
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


class TestExportCubeRotatedX30Y45Z60(ExporterTestBase, unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        ExporterTestBase.__init__(self)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def matmul(self, a, b):
        result = [[0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0]]

        for i in range(len(a)):
            for j in range(len(b[0])):
                for k in range(len(b)):
                    result[i][j] += a[i][k] * b[k][j]

        return result

    def test_rotated_x_30_y_45_z_60(self):

        import math

        sin30 = math.sin(math.radians(30))
        sin45 = math.sin(math.radians(45))
        sin60 = math.sin(math.radians(60))

        cos30 = math.cos(math.radians(30))
        cos45 = math.cos(math.radians(45))
        cos60 = math.cos(math.radians(60))

        for exportable_scene in self.get_exportable_scenes_for_test():
            x = [[1.0, 0.0, 0.0, 0.0], [0.0, cos30, sin30, 0.0], [0.0, -sin30, cos30, 0.0], [0.0, 0.0, 0.0, 1.0]]

            y = [[cos45, 0.0, -sin45, 0.0], [0.0, 1.0, 0.0, 0.0], [sin45, 0.0, cos45, 0.0], [0.0, 0.0, 0.0, 1.0]]

            z = [[cos60, sin60, 0.0, 0.0], [-sin60, cos60, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]

            expected_final_transform = self.matmul(x,y)
            expected_final_transform = self.matmul(expected_final_transform, z)
            expected_final_transform_flattened = [item for sublist in expected_final_transform for item in sublist]

            cube = exportable_scene.ramses_scene.findObjectByName('Cube')
            cube_node = ramses_export.RamsesPython.toNode(cube)

            actual_transform = cube_node.getModelMatrix()

            assert len(expected_final_transform_flattened) == 16
            assert len(actual_transform) == 16

            index = 0
            for expected, actual in zip(expected_final_transform_flattened, actual_transform):
                self.assertAlmostEqual(expected, actual, places=3, msg=f'on index {index}')
                index += 1

if __name__ == '__main__':
    suite_1 = unittest.defaultTestLoader.\
            loadTestsFromTestCase(TestExportCubeRotatedX30Y45Z60)

    all_tests = unittest.TestSuite([suite_1])

    success = unittest.TextTestRunner().run(all_tests).wasSuccessful()
    if not success:
        raise Exception('Test "cube rotated by 30 on X, 45 on Y and 60 on Z" failed.')
