
#  -------------------------------------------------------------------------
#  Copyright (C) 2019 Daniel Werner Lima Souza de Almeida
#                     dwlsalmeida at gmail dot com
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

import json
import pathlib
from . import debug_utils
from . import intermediary_representation
log = debug_utils.get_debug_logger()


class ShaderUtils():
    """Deals with bridging shaders from Blender to RAMSES"""

    def __init__(self):
        self.shader_dir = ''
        self.current_node = None
        self.current_vert_shader = ''
        self.current_frag_shader = ''
        # A dict with extra metadata to help bridge Blender materials to RAMSES effects
        # Read from a JSON file since it is very human-readable and easy to parse
        # See 'https://docs.substance3d.com/sddoc/glslfx-shaders-102400055.html' as inspiration
        self.config = {}

    def set_current_node(self, node: intermediary_representation.Node, shader_dir: str = None):
        assert node
        self.current_node = node
        self.shader_dir = shader_dir if shader_dir else ''
        self.current_vert_shader, self.current_frag_shader = self._glsl_from_files() if \
            self.shader_dir else self._glsl_default()
        self.config = self._config_from_file()
        assert self.current_vert_shader
        assert self.current_frag_shader

    def clear_current_node(self):
        self.current_node = None
        self.shader_dir = ''

    def do_node(self) -> intermediary_representation.Node:
        # NOTE: if we want neither the default nor custom GLSL but instead want to derive
        # i.e.: shaders from material nodes or something similar, this is the place to change it

        assert isinstance(self.current_node, intermediary_representation.MeshNode), 'Only meshes are supported for now'
        self.current_node.vertex_shader = self.current_vert_shader
        self.current_node.fragment_shader = self.current_frag_shader
        return self.current_node

    def _glsl_from_files(self, dir=None):

        scene_object_name = self.current_node.name
        dir = pathlib.Path(dir) if dir else pathlib.Path.cwd()

        vert_path = pathlib.Path(dir/f'{scene_object_name}.vert')
        frag_path = pathlib.Path(dir/f'{scene_object_name}.frag')

        if not vert_path and not frag_path:
            # Probably a mistake if both are missing
            raise RuntimeError(f"Tried reading GLSL from files but no shaders found for {scene_object_name}!\n")

        with open(vert_path, 'r') as f:
            vert_shader = f.read()
            if vert_shader:
                log.debug(f'Read GLSL from {vert_path} for {scene_object_name}. Contents are:\n{vert_shader}\n')

        with open(frag_path, 'r') as f:
            frag_shader = f.read()
            if frag_shader:
                log.debug(f'Read GLSL from {frag_path} for {scene_object_name}. Contents are:\n{frag_shader}\n')

        return vert_shader, frag_shader

    def _glsl_default(self) -> str:

        vertShader = """
                       #version 300 es

                        in vec3 a_position;
                        uniform highp mat4 u_ModelMatrix;
                        uniform highp mat4 u_ViewMatrix;
                        uniform highp mat4 u_ProjectionMatrix;

                        void main()
                            {
                                gl_Position = u_ProjectionMatrix * u_ViewMatrix * u_ModelMatrix * vec4(a_position.xyz, 1.0);
                            }
                     """

        fragShader = """
                    #version 300 es

                    precision mediump float;
                    out vec4 FragColor;

                    void main(void)
                    {
                        FragColor = vec4(1.0, 1.0, 1.0, 1.0);
                    }

                    """

        return vertShader, fragShader

    def _config_from_file(self):
        assert self.shader_dir
        # TODO: consider improving this
        config_paths = list(pathlib.Path(f'{self.shader_dir}').glob(pattern='*.config'))
        config_path = config_paths[0]

        return json.loads(config_path)
