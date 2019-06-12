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
from .exportable_scene import ExportableScene
from . import debug_utils

log = debug_utils.get_debug_logger()


class RamsesInspector():
    """Inspector for assessing the results of generated RAMSES scenes"""

    def __init__(self,
                 scene: ExportableScene,
                 viewer_path: pathlib.Path):

        self.scene = scene
        self.viewer_path = viewer_path

        if self.viewer_path and \
            (not self.viewer_path.exists() or not self.viewer_path.is_file()):
            raise RuntimeError('Could not find the RAMSES Scene Viewer. '
                               + 'Leave the path blank if you do not '
                               + 'intend to use it.')

    def load_viewer(self):
        """Loads the RAMSES scene viewer for visual inspection of the
        generated scene"""

        if not self.viewer_path:
            log.debug(f'Not launching viewer as chosen path was empty.')
            return

        program_name = self.viewer_path

        arg_ramses_scene_file = str(self.scene.ramses_scene_file)
        arg_ramses_scene_resources_file = str(self.scene.ramses_scene_resources_file)
        viewer_arg = arg_ramses_scene_file.replace('.ramses', '')

        assert arg_ramses_scene_file
        assert arg_ramses_scene_resources_file

        log.debug(f'Loading viewer: {program_name} with args: {viewer_arg}')
        subprocess.run([program_name, '-s', viewer_arg], capture_output=True)
