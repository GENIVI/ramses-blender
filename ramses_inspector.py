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
                 scene: ExportableScene):

        self.scene = scene


    def load_viewer(self):
        """Loads the RAMSES scene viewer for visual inspection of the
        generated scene"""

        resolution_x = self.scene.blender_scene.render.resolution_x
        resolution_y = self.scene.blender_scene.render.resolution_y

        window = self.scene.ramses.openWindow(resolution_x, resolution_y, 0, 0)
        window.showScene(self.scene.ramses_scene)
