#  -------------------------------------------------------------------------
#  Copyright (C) 2019 Daniel Werner Lima Souza de Almeida
#                     dwlsalmeida at gmail dot com
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------


class ExportableScene():
    """A RAMSES Scene ready to be visualized / saved"""
    def __init__(self, ramses, ramses_scene):
        self.ramses = ramses
        self.ramses_scene = ramses_scene
        self.ir_groups = []
        self.groups = {}
        self.passes = {}

    def save(self):
        scene_file = "/tmp/scene.ramses"
        scene_resources = "/tmp/scene.ramres" # TODO: make configurable
        self.ramses_scene.saveToFiles(scene_file, scene_resources, True)

    def get_validation_report(self):
        return str(self.ramses_scene.getValidationReport())

    def is_valid(self):
        report = self.get_validation_report()
        return len(report) == 0

    def bind_groups_to_passes(self):
        for render_pass in self.passes.values():
            group_order = 0 #TODO improve this.

            for render_group in self.groups.values():
                render_pass.addRenderGroup(render_group, group_order)
                group_order += 1
