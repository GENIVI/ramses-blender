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
        self._window = None

    def load_viewer(self):
        """Loads the RAMSES scene viewer for visual inspection of the
        generated scene"""

        self.close_viewer()

        resolution_x = self.scene.blender_scene.render.resolution_x
        resolution_y = self.scene.blender_scene.render.resolution_y

        self._window = self.scene.ramses.openWindow(resolution_x, resolution_y, 0, 0)
        self._window.showScene(self.scene.ramses_scene)

    def close_viewer(self):
        if self._window:
            self._window.close()
            self._window = None

    def get_window(self):
        return self._window

    def __del__(self):
        """Call _window.close() before going out of scope"""
        self.close_viewer()