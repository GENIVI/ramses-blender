#  -------------------------------------------------------------------------
#  Copyright (C) 2019 Daniel Werner Lima Souza de Almeida -
#                     dwlsalmeida at gmail dot com
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

from __future__ import annotations # Needed in order for something to reference itself in 'typing'
import bpy
from . import RamsesPython
from . import debug_utils
from .intermediary_representation import *
from typing import List

log = debug_utils.get_debug_logger()

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
        """Builds a RAMSES scene out of the available scene \
            representations

        Raises:
            RuntimeError: Raised when 'extract_from_blender_scene' is \
                not called first.
        """

        if not self.ready_to_translate:
            raise RuntimeError("Extract data from Blender first.")

        ramses = RamsesPython.Ramses("test")

        ramses_scene = ramses.createScene("test scene")

        ramses_render_group = ramses_scene.createRenderGroup('rendergroup')
        ramses_render_pass = ramses_scene.createRenderPass('renderpass')

        ramses_render_pass.addRenderGroup(ramses_render_group, 0)

        for scene_representation in self.scene_representations:
            ir_root = scene_representation.graph.root
            debug_utils.get_debug_logger().debug(\
                f'Intermediary representation consists of:\n{str(scene_representation.graph)}')

            ramses_root = self._ramses_build_subscene(ramses_scene, ir_root, parent=None)

            log.debug(f'Successfully built RAMSES Scenegraph: {str(ramses_root)}')


        sceneFile = "/tmp/scene.ramses"
        sceneResources = "/tmp/scene.ramres"
        ramses_scene.saveToFiles(sceneFile, sceneResources, True)
        validationReport = str(ramses_scene.getValidationReport())


        log.debug(f"Validation report for scene {str(ramses_scene)}:\n{validationReport}")
        if validationReport != '':
            raise RuntimeError(validationReport)


    def _ramses_build_subscene(self,
                                scene: RamsesPython.Scene,
                                ir_node: Node,
                                parent: RamsesPython.Node = None) -> RamsesPython.Node:

        """Builds a RAMSES scene graph starting from 'node' and
        optionally adds it as a child to 'parent'

        Arguments:
            scene {RamsesPython.Scene} -- The scene to build nodes from
            ir_node {Node} -- The IRNode to begin from

        Keyword Arguments:
            parent {RamsesPython.Node} -- The optional RAMSES parent node (default: {None})

        Returns:
            RamsesPython.Node -- The built node / scene graph
        """

        log.debug(f'Building subscene for node: {str(ir_node)}')
        current_ramses_node = self.translate(scene, ir_node) # TODO: add to render group

        for child in ir_node.children:
            self._ramses_build_subscene(scene, child, parent=current_ramses_node)

        if parent:
            parent.addChild(current_ramses_node)

        return current_ramses_node


    def translate(self, scene: RamsesPython.Scene, ir_node: Node) -> RamsesPython.Node:
        """Translates the IRNode into a RAMSES node / graph

        Arguments:
            ir_node {Node} -- The node to be translated
            scene {RamsesPython.Scene} -- The current RAMSES Scene to \
                create the node from

        Returns:
            RamsesPython.Node -- The translated node / graph
        """

        name = ir_node.name
        returned_node = None


        if isinstance(ir_node, MeshNode):
            ramses_mesh_node = scene.createMesh(name)

            indices = scene.createIndexArray(ir_node.get_indices())
            vertices = scene.createVertexArray(3, ir_node.get_vertex_buffer())
            # TODO normals, texcoords...


            vertShader = """
            #version 300 es

            in vec3 a_position;
            in vec2 a_texcoords;
            out vec2 v_texcoords;

            void main()
            {
                //v_texcoords = a_texcoords;
                // z = -1.0, so that the geometry will not be clipped by the near plane of the camera
                gl_Position = vec4(a_position.xy, -1.0, 1.0);
            }
            """

            fragShader = """
            #version 300 es

            //uniform sampler2D u_texture;
            precision mediump float;
            //uniform float u_opacity;

            //in vec2 v_texcoords;
            out vec4 FragColor;

            void main(void)
            {
                //ivec2 textureSize = textureSize(u_texture, 0);
                //vec2 texelFloat = vec2(v_texcoords.x * float(textureSize.x), v_texcoords.y * float(textureSize.y));
                //vec4 texel = texelFetch(u_texture, ivec2(texelFloat), 0);
                //FragColor = u_opacity * texel;

                FragColor = vec4(1.0, 1.0, 1.0, 1.0);
            }

            """

            ramses_effect = scene.createEffect(vertShader, fragShader)
            geometry = scene.createGeometry(ramses_effect)
            appearance = scene.createAppearance(ramses_effect)

            geometry.setIndexBuffer(indices)
            geometry.setVertexBuffer("a_position", vertices)

            ramses_mesh_node.setAppearance(appearance)
            ramses_mesh_node.setGeometry(geometry)

            translation_node = scene.createNode(f'Positions mesh \
                {str(ir_node)} into scene')
            translation_node.setTranslation(ir_node.location[0],
                                            ir_node.location[1],
                                            ir_node.location[2])
            translation_node.addChild(ramses_mesh_node)

            returned_node = translation_node

        elif isinstance(ir_node, PerspectiveCameraNode):
            fov = ir_node.fov
            z_near = ir_node.z_near
            z_far = ir_node.z_far
            aspect_ratio = ir_node.aspect_ratio

            ramses_camera_node = scene.createPerspectiveCamera(name)
            ramses_camera_node.setViewport(0, 0, int(ir_node.width), int(ir_node.height))
            ramses_camera_node.setFrustumFromFoV(fov, aspect_ratio, z_near, z_far)

            returned_node = ramses_camera_node

        elif isinstance(ir_node, Node):
            ramses_node = scene.createNode(name)

            returned_node = ramses_node

        else:
            raise NotImplementedError(f"Cannot translate node: {str(ir_node)} !")

        log.debug(f'Translated IRNode {str(ir_node)} into {returned_node}')
        # TODO: get RAMSES node name from bindings
        return returned_node



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
