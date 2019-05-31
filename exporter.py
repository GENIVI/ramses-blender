from __future__ import annotations # Needed in order for something to reference itself in 'typing'

#  -------------------------------------------------------------------------
#  Copyright (C) 2019 Daniel Werner Lima Souza de Almeida -
#                     dwlsalmeida at gmail dot com
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

import bpy
from . import RamsesPython
import logging
from .intermediary_representation import *
from typing import List

log = logging.getLogger(name='ramses-scene-exporter')

class RamsesBlenderExporter():
    """Extracts the scene graph, translating it to a RAMSES scene"""

    def __init__(self, scenes: List[bpy.types.Scene]):
        self.scenes = scenes
        self.scene_representations = []
        self.ready_to_translate = False

    def extract_from_blender_scene(self):
        """Extract the scene graph from Blender, building an internal
        representation that can then be used to build a RAMSES scene"""

        for scene in self.scenes:
            extractor = BlenderRamsesExtractor(scene)
            representation = extractor.run()
            self.scene_representations.append(representation)

        self.ready_to_translate = True

    def build_ramses_scene(self):
        if not self.ready_to_translate:
            raise RuntimeError("Extract data from Blender first.")
        raise NotImplementedError


class BlenderRamsesExtractor():
    """Runs over a scene extracting relevant data from bpy"""

    def __init__(self, scene: bpy.types.Scene):
        self.scene = scene

    def run(self):
        log.debug(f'Extracting data from scene {self.scene}')
        representation = SceneRepresentation(self.scene,
                                             self.scene.objects,
                                             self.scene.camera,
                                             self.scene.animation_data,
                                             self.scene.world)
        return representation
