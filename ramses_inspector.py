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


class RamsesInspector():
    """Inspector for assessing the results of generated RAMSES scenes"""

    def __init__(self,
                 scene: ExportableScene,
                 viewer_path: pathlib.Path):

        self.scene = scene
        self.viewer_path = viewer_path

        assert self.viewer_path.exists()


    def load_viewer(self):
        """Loads the RAMSES scene viewer for visual inspection of the
        generated scene"""

        program_name = self.viewer_path

        arg_ramses_scene_file = str(self.scene.ramses_scene_file)
        arg_ramses_scene_resources_file = str(self.scene.ramses_scene_resources_file)
        viewer_arg = arg_ramses_scene_file.replace('.ramses', '')

        assert arg_ramses_scene_file
        assert arg_ramses_scene_resources_file

        subprocess.run([program_name, '-s', viewer_arg], capture_output=True)
