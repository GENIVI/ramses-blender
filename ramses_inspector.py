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
                 scene: ExportableScene):

        self.scene = scene
        self.viewer_process = None

    def load_viewer(self, platform, block: bool = False):
        """Loads the RAMSES scene viewer for visual inspection of the
        generated scene"""

        assert isinstance(platform, str)
        platform = platform.lower()

        self.close_viewer()

        resolution_x = self.scene.blender_scene.render.resolution_x
        resolution_y = self.scene.blender_scene.render.resolution_y

        program_args = f'-s {self.scene.output_path}{self.scene.blender_scene.name} -x -w {resolution_x} -h {resolution_y}'
        program = f'ramses-scene-viewer-{platform}'
        cmd = f'bin/{program} {program_args}'

        log.debug(f'Running viewer. Command is: {cmd}\n')

        self.viewer_process = subprocess.Popen(cmd, shell=True)
        if block:
            self.viewer_process.wait()

    def close_viewer(self):
        if self.viewer_process:
            self.viewer_process.kill()
