
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


class TestExportCubeRotated_XZY(ExporterTestBase, unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        ExporterTestBase.__init__(self)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_rotation_mode_XZY(self):

        for exportable_scene in self.get_exportable_scenes_for_test():

            cube = exportable_scene.ramses_scene.findObjectByName('Cube')
            cube_node = ramses_export.RamsesPython.toNode(cube)

            # XZY: ...Y -> Z -> X -> (Scaling) -> Mesh
            rotation_x_node = ramses_export.RamsesPython.toNode(cube_node.getParent().getParent())
            rotation_z_node = ramses_export.RamsesPython.toNode(rotation_x_node.getParent())
            rotation_y_node = ramses_export.RamsesPython.toNode(rotation_z_node.getParent())

            rotation_x = rotation_x_node.getRotation()
            rotation_y = rotation_y_node.getRotation()
            rotation_z = rotation_z_node.getRotation()


            # if the order is off, this will not be true
            self.assertEqual(rotation_x, [-30.0, 0.0,  0.0], msg=f'Node is: {rotation_x_node.getName()}')
            self.assertEqual(rotation_y, [0.0,  -45.0, 0.0], msg=f'Node is: {rotation_y_node.getName()}')
            self.assertEqual(rotation_z, [0.0, 0.0,  -60.0], msg=f'Node is: {rotation_z_node.getName()}')


if __name__ == '__main__':
    suite_1 = unittest.defaultTestLoader.\
            loadTestsFromTestCase(TestExportCubeRotated_XZY)

    all_tests = unittest.TestSuite([suite_1])

    success = unittest.TextTestRunner().run(all_tests).wasSuccessful()
    if not success:
        raise Exception('Test "cube rotated with rotation mode XZY" failed.')
