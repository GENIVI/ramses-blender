#  -------------------------------------------------------------------------
#  Copyright (C) 2019 Daniel Werner Lima Souza de Almeida
#                     dwlsalmeida at gmail dot com
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

import pathlib
import os


class ExportableScene():
    """A RAMSES Scene ready to be visualized / saved"""
    def __init__(self,
                 ramses,
                 ramses_scene,
                 blender_scene):
        self.ramses = ramses
        self.ramses_scene = ramses_scene
        self.blender_scene = blender_scene

        # Paths are set at a later stage
        self.output_path = None

        self.ir_groups = []
        self.groups = {}
        self.passes = {}

    def save(self):
        """Persists the RAMSES scene."""

        ramses_scene_file = os.path.join(self.output_path, f'{self.blender_scene.name}.ramses')
        ramses_scene_resources_file = os.path.join(self.output_path, f'{self.blender_scene.name}.ramres')
        self.ramses_scene.saveToFiles(str(ramses_scene_file),
                                      str(ramses_scene_resources_file),
                                      True)

    def get_validation_report(self):
        """Returns the validation report issued by RAMSES."""
        return str(self.ramses_scene.getValidationReport())

    def is_valid(self):
        """Whether the underlying RAMSES scene is valid."""
        report = self.get_validation_report()
        return len(report) == 0

    def bind_groups_to_passes(self):
        """Adds every RAMSES render group to the available RAMSES render passes"""
        for render_pass in self.passes.values():
            group_order = 0 #TODO improve this.

            for render_group in self.groups.values():
                render_pass.addRenderGroup(render_group, group_order)
                group_order += 1

    def set_output_dir(self, output_dir: str):
        """Sets the output directory if this scene is to be saved"""

        if not pathlib.Path(output_dir).is_dir():
            raise RuntimeError('Invalid output directory specified.')

        self.output_path = output_dir

    def to_text(self) -> str:
        """Returns the RAMSES text representation for the underlying
        RAMSES scene"""
        text_representation = self.ramses_scene.toText()
        assert text_representation
        return text_representation
