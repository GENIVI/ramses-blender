#  -------------------------------------------------------------------------
#  Copyright (C) 2019 Daniel Werner Lima Souza de Almeida
#                     dwlsalmeida at gmail dot com, BMW AG
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

import sys
import bpy

from ramses_export import debug_utils
from ramses_export.ramses_inspector import RamsesInspector
from ramses_export.exporter import RamsesBlenderExporter
from ramses_export import RamsesPython

class RunAllTests:
    def _test_doing_nothing(self):
        # Do nothing ;)
        self._EXPECT_single_cube_blender()

    def _test_extraction(self):

        exporter = RamsesBlenderExporter(bpy.data.scenes)
        exporter.extract_from_blender_scene()

        # TODO Add some tests for expected content of extracted scene
        # TODO also add a test which checks what happens if scene is extracted more, e.g. two times

        self._EXPECT_single_cube_blender()

    def _test_exporting(self):

        # TODO this is copied from __init__.py, probably needs refactoring so that it can be reused, not copied

        debug_utils.setup_logging('C:/dev/ramses-blender/build/debug.txt') # TODO: set up as an option for the end user.
        exporter = RamsesBlenderExporter(bpy.data.scenes)
        exporter.extract_from_blender_scene()

        exporter.build_from_extracted_representations()

        for exportable_scene in exporter.get_exportable_scenes():

            inspector = RamsesInspector(exportable_scene)
            inspector.load_viewer()

            if not exportable_scene.is_valid():
                validation_report = exportable_scene.get_validation_report()
                raise RuntimeError(validation_report)

            exportable_scene.save()

        self._EXPECT_single_cube_blender()
        self._EXPECT_single_cube_ramses(exportable_scene.ramses_scene)

    # TODO add more tests here

    def _EXPECT_single_cube_blender(self):
        expected_scenes = 1
        found_scenes = len(bpy.data.scenes)
        if found_scenes != expected_scenes:
            raise AssertionError(f'Expected {expected_scenes} scenes but found {found_scenes}!')

    def _EXPECT_single_cube_ramses(self, ramsesScene: RamsesPython.Scene):
        # TODO find a more elegant way to check expectations, but plain text will do for now
        expectedSceneContents = """Scene 'test scene' [id:0]
RootNode 'Root node'
 Node 'Positions mesh                 IRNode of type: <class 'ramses_export.intermediary_representation.MeshNode'> and name: Cube into scene'
  MeshNode 'Cube'
  vec3 a_position: [Type: 58]
 Node 'Light'
 Camera 'Camera'

RenderPass setup:
RenderPass Render pass for Camera
  Perspective Camera:
    Planes: [Left: -0.00107221 Right: 0.00107221 Bot: -0.000603116 Top: 0.000603116]
    Viewport: [0, 0, 1920, 1080]
    FoV: 0.691111; Asp. Ratio: 1.77778
"""

        actualSceneContents = ramsesScene.toText('Cube')

        if actualSceneContents != expectedSceneContents:
            raise AssertionError(f'Expected scene contents:\n\n+++{expectedSceneContents}+++\n\nbut found:\n\n+++{actualSceneContents}+++\n')

    def execute(self):
        # TODO make a test battery, with permutation, randomization, etc.
        # For now, just run every test 2 times and expect the same result
        self._test_doing_nothing()
        self._test_doing_nothing()

        self._test_extraction()
        self._test_extraction()

        self._test_exporting()
        self._test_exporting()
