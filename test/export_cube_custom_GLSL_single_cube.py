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
import pathlib

from ramses_export.test.exporter_test_base import ExporterTestBase

from ramses_export import debug_utils
from ramses_export.ramses_inspector import RamsesInspector
from ramses_export.exporter import RamsesBlenderExporter
from ramses_export import RamsesPython
from ramses_export import utils

class ExportCubeCustomGLSLTest(ExporterTestBase, unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        ExporterTestBase.__init__(self)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_export_cube_custom_GLSL_single_cube(self):
        params = {}
        shader_library_dir = 'test/shader_library'

        custom_params = utils.CustomParameters()
        # Setting up this field will make the addon look into the
        # directory for .verg/.frag/.config files
        custom_params.shader_dir = str(pathlib.Path(f'{self.addon_path}/{shader_library_dir}'))

        params['CubeRed'] = custom_params

        self.maxDiff = None # Display diff if the strings do not match

        for exportable_scene in self.get_exportable_scenes_for_test(take_screenshot=True, custom_params=params):
            self.assertTrue(exportable_scene.is_valid())

            cube_white_ir = exportable_scene.scene_representation.graph.find(attribute='name', value='CubeWhite')[0]
            cube_red_ir = exportable_scene.scene_representation.graph.find(attribute='name', value='CubeRed')[0]

            default_vertex_shader, default_fragment_shader = exportable_scene.scene_representation.shader_utils._glsl_default()

            self.assertEqual(cube_white_ir.vertex_shader, default_vertex_shader)
            self.assertEqual(cube_white_ir.fragment_shader, default_fragment_shader)

            custom_vertex_shader = """#version 300 es

in vec3 a_position;
uniform highp mat4 u_ModelMatrix;
uniform highp mat4 u_ViewMatrix;
uniform highp mat4 u_ProjectionMatrix;

void main()
{
\tvec3 new_pos = a_position;

\tnew_pos.x += 2.0f;
\tnew_pos.y += 2.0f;
\tnew_pos.z += 2.0f;

\t
\tgl_Position = u_ProjectionMatrix * u_ViewMatrix * u_ModelMatrix * vec4(new_pos.xyz, 1.0);
}
"""
            custom_fragment_shader = """#version 300 es

precision mediump float;

out vec4 FragColor;

void main(void)
{
\tFragColor = vec4(1.0, 0.0, 0.0, 1.0);
}

"""
            self.assertEqual(cube_red_ir.vertex_shader, custom_vertex_shader, msg="GLSL differs between node and file")
            self.assertEqual(cube_red_ir.fragment_shader, custom_fragment_shader, msg="GLSL differs between node and file")


if __name__ == '__main__':
    suite_1 = unittest.defaultTestLoader.\
            loadTestsFromTestCase(ExportCubeCustomGLSLTest)

    all_tests = unittest.TestSuite([suite_1])

    success = unittest.TextTestRunner().run(all_tests).wasSuccessful()
    if not success:
        raise Exception('Test "export_cube_custom_GLSL_single_cube" failed')
