#  -------------------------------------------------------------------------
#  Copyright (C) 2019 Daniel Werner Lima Souza de Almeida
#                     dwlsalmeida at gmail dot com
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

import subprocess
import pathlib
import subprocess
from .exportable_scene import ExportableScene
from . import debug_utils

log = debug_utils.get_debug_logger()


class RamsesInspector():
    """Inspector for assessing the results of generated RAMSES scenes"""

    def __init__(self,
                 scene: ExportableScene,
                 addon_dir: str = None):

        self.scene = scene
        self.viewer_process = None
        self.addon_dir = addon_dir if addon_dir else \
            str(pathlib.Path.cwd())

        assert pathlib.Path(self.addon_dir).exists()

    def load_viewer(self, platform, block: bool = False):
        """Loads the RAMSES scene viewer for visual inspection of the
        generated scene"""

        assert isinstance(platform, str)
        assert platform.islower() # Having uppercase chars is a common mistake
                                  # Leads to viewer binary not being found
        assert self.scene.output_path
        assert self.scene.blender_scene.name

        self.close_viewer()

        resolution_x = self.scene.blender_scene.render.resolution_x
        resolution_y = self.scene.blender_scene.render.resolution_y

        scene_full_path = pathlib.Path(self.scene.output_path).joinpath(f'{self.scene.blender_scene.name}.ramses')
        assert scene_full_path.exists(), f'Wrong scene path: {str(scene_full_path)}'

        program_args = f"-s {str(scene_full_path).replace('.ramses','')} -x -w {resolution_x} -h {resolution_y}"
        program = f'ramses-scene-viewer-{platform}'

        program_full_path = pathlib.Path(self.addon_dir).joinpath('bin').joinpath(program)
        assert program_full_path.exists(), f'Wrong viewer path: {str(program_full_path)}'

        cmd = f'{str(program_full_path)} {program_args}'

        log.debug(f'Running viewer. Command is: {cmd}\n')

        self.viewer_process = subprocess.Popen(cmd, shell=True)
        if block:
            self.viewer_process.wait()

    def close_viewer(self):
        if self.viewer_process:
            self.viewer_process.kill()
