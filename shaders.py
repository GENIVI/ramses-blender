
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
        self.config = self.get_default_config()

    def set_current_node(self, node, shader_dir: str = None, technique: str = 'default'):
        assert node
        self.current_node = node
        self.shader_dir = shader_dir if shader_dir else ''

        self.config = self._config_from_file() if self.shader_dir else self.get_default_config()

        if shader_dir:
            self.current_vert_shader, self.current_frag_shader = self._glsl_from_files(self.shader_dir, technique=technique)
        else:
            self.current_vert_shader, self.current_frag_shader = self._glsl_default()

        assert self.current_vert_shader
        assert self.current_frag_shader
        assert self._validate_config(self.config)

    def clear_current_node(self):
        self.current_node = None
        self.shader_dir = ''

    def do_node(self, node=None, technique: str = 'default'):
        # NOTE: if we want neither the default nor custom GLSL but instead want to derive
        # i.e.: shaders from material nodes or something similar, this is the place to change it
        if node:
            self.set_current_node(node)

        assert self.current_node
        assert isinstance(self.current_node, intermediary_representation.MeshNode), 'Only meshes are supported for now'

        self.current_node.vertex_shader = self.current_vert_shader
        self.current_node.fragment_shader = self.current_frag_shader
        self.current_node.vertexformat = self.config['vertexformat']

        if node:
            self.clear_current_node()
        return self.current_node

    def _glsl_from_files(self, dir=None, technique: str = 'default'):

        assert self._validate_config(self.config)


        scene_object_name = self.current_node.name
        vert_shader_name = self.config['techniques'][technique]['shaders']['vertex']
        frag_shader_name = self.config['techniques'][technique]['shaders']['fragment']

        assert vert_shader_name
        assert frag_shader_name

        dir = pathlib.Path(dir) if dir else pathlib.Path.cwd()

        vert_path = pathlib.Path(dir/f'{vert_shader_name}.vert')
        frag_path = pathlib.Path(dir/f'{frag_shader_name}.frag')

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
        """Reads a config from config.txt in self.shader_dir"""

        if not self.shader_dir:
            log.debug(f"Can't read shader config for {str(self.current_node)}: path has not been set")
            return

        assert self.shader_dir # Sanity check if the above ever gets deleted

        # TODO: consider improving this
        config_paths = list(pathlib.Path(f'{self.shader_dir}').glob(pattern='*config.txt'))
        assert len(config_paths) == 1 # NOTE: should we allow more than one config per node?
        config_path = config_paths[0]

        config_str = ''
        with open(config_path, 'r') as f:
            config_str = f.read()

        loaded_dict = json.loads(config_str) if config_str else {}
        assert isinstance(loaded_dict, dict)

        self._validate_config(loaded_dict)
        return loaded_dict

    def _validate_config(self, config: dict, valid_config: dict = None, die: bool = True) -> bool:
        """Validates a config against 'valid_config' in a recursive manner, failing if their keys differ.

        Arguments:
            config {dict} -- A config dict, usually read from a file in glsl_from_files()

        Keyword Arguments:
            valid_config {dict} -- A config to compare against. If none, defaults to the default config (default: {None})
            die {bool} -- Whether the code should raise an exception on failure (default: {True})

        Raises:
            RuntimeError: Exception raised when keys in 'config' and 'valid_config' differ.

        Returns:
            bool -- Whether the config is valid.
        """

        assert isinstance(config, dict)

        if not valid_config:
            valid_config = self.get_default_config()

        for key in config.keys():
            if key == 'techniques':
                # These names are user defined so no point in checking
                # Take them as valid
                valid_config[key] = config[key]

            if key not in valid_config.keys():
                if die:
                    raise RuntimeError(f'Unknown key "{str(key)}" in config for node "{str(self.current_node)}" located in "{str(self.shader_dir)}"')

                return False

            if isinstance(config[key], dict) and not self._validate_config(config[key], valid_config=valid_config[key], die=die):
                return False

        return True

    def get_default_config(self):
        # Leave room for extending this feature in the future
        config = {}
        config['techniques'] = {'default': {}}
        config['techniques']['default']['shaders'] = {'vertex':'', 'fragment':''}
        config['vertexformat'] = {'position':'a_position', 'normal':'', 'texcoord':''}
        return config
