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
import math
from . import RamsesPython
from . import debug_utils
from .exportable_scene import ExportableScene
from .intermediary_representation import *
from typing import List

log = debug_utils.get_debug_logger()

class RamsesBlenderExporter():
    """Extracts the scene graph, translating it to a RAMSES scene"""

    def __init__(self, scenes: List[bpy.types.Scene]):
        self.scenes = scenes
        self.scene_representations = []
        self.ready_to_translate = False
        self.ramses = RamsesPython.Ramses("RAMSES Framework Handle")
        self.exportable_scenes = []

    def get_exportable_scenes(self) -> List[ExportableScene]:
        return self.exportable_scenes

    def extract_from_blender_scene(self):
        """Extract the scene graph from Blender, building an internal
        representation that can then be used to build a RAMSES scene"""

        for scene in self.scenes:
            extractor = BlenderRamsesExtractor(scene)
            representation = extractor.run()
            representation.build_ir()
            self.scene_representations.append(representation)

            """ While this is not a 1:1 translation, if we've created way more
            nodes than there were objects then this might be indicative of a
            bug somewhere. Start checking after a minimum number of nodes"""
            assert representation.graph.node_count() < 20 or \
                (representation.graph.node_count() <= \
                len(representation.scene.objects) * 1.25), "Too many objects were created"

        self.ready_to_translate = True

    def build_from_extracted_representations(self):
        for representation in self.scene_representations:
            ramses_scene = self.build_ramses_scene(representation)
            self.exportable_scenes.append(ramses_scene)

    def build_ramses_scene(self,
                           scene_representation: SceneRepresentation) -> ExportableScene:
        """Builds a RAMSES scene out of the available scene \
            representations

        Arguments:
            scene_representation {SceneRepresentation} -- The scene \
                representation previously extracted from Blender.

        Raises:
            RuntimeError: Raised when 'extract_from_blender_scene' is \
                not called first.

        Returns:
            ExportableScene -- A scene that is ready to be visualized / saved.
        """

        if not self.ready_to_translate:
            raise RuntimeError("Extract data from Blender first.")


        ramses_scene = self.ramses.createScene("test scene")

        ir_root = scene_representation.graph.root
        ir_groups = scene_representation.graph.as_groups()

        exportable_scene = ExportableScene(self.ramses,
                                           ramses_scene,
                                           scene_representation.scene,
                                           None)
        exportable_scene.groups = self._build_ramses_render_groups(ramses_scene, ir_groups)
        exportable_scene.passes = self._build_ramses_render_passes(ramses_scene, ir_root)
        exportable_scene.ir_groups = ir_groups

        log.debug(\
            f'Intermediary representation consists of:\n{str(scene_representation.graph)}')

        ramses_root = self._ramses_build_recursively(ramses_scene,
                                                     ir_root,
                                                     parent=None,
                                                     exportable_scene=exportable_scene)

        log.debug(f'Successfully built RAMSES Scenegraph: {str(ramses_root)}. Tearing down the IR graph')
        scene_representation.teardown()

        exportable_scene.bind_groups_to_passes()

        validation_report = exportable_scene.get_validation_report()
        log.debug(f"Validation report for scene {str(exportable_scene.ramses_scene)}:\n{validation_report}")

        log.debug(f"RAMSES Scene Text Representation:\n{exportable_scene.to_text()}\n")
        return exportable_scene


    def _ramses_build_recursively(self,
                                  scene: RamsesPython.Scene,
                                  ir_node: Node,
                                  exportable_scene: ExportableScene,
                                  parent: RamsesPython.Node = None,
                                  current_depth = 0) -> RamsesPython.Node:

        """Builds a RAMSES scene graph starting from 'node' and
        optionally adds it as a child to 'parent'

        Arguments:
            scene {RamsesPython.Scene} -- The scene to build nodes from
            ir_node {Node} -- The IRNode to begin from
            render_group {RamsesPython.RenderGroup} -- The group to add the subscene to

        Keyword Arguments:
            parent {RamsesPython.Node} -- The optional RAMSES parent node (default: {None})
            exportable_scene {ExportableScene} -- sets up RenderGroups and RenderPasses.
            current_depth {int} - Optional information to aid in debugging.

        Returns:
            RamsesPython.Node -- The built node / scene graph
        """

        log.debug((' ' * current_depth * 4) +
                  f'Recursively building RAMSES nodes for IR node: "{str(ir_node)}", RAMSES parent is "{str(parent)}"')

        current_ramses_node = self.translate(scene, ir_node, exportable_scene=exportable_scene)

        if ir_node.children:
            current_depth += 1

        for child in ir_node.children:
            self._ramses_build_recursively(scene,
                                           child,
                                           exportable_scene,
                                           parent=current_ramses_node,
                                           current_depth=current_depth)

        if parent:
            parent.addChild(current_ramses_node)

        return current_ramses_node


    def translate(self, scene: RamsesPython.Scene, ir_node: Node, exportable_scene: ExportableScene = None) -> RamsesPython.Node:
        """Translates the IRNode into a RAMSES node / graph

        Arguments:
            ir_node {Node} -- The node to be translated
            scene {RamsesPython.Scene} -- The current RAMSES Scene to \
                create the node from
            exportable_scene {ExportableScene} -- optional: sets up RenderGroups and RenderPasses.

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

            ramses_effect = scene.createEffect(vertShader, fragShader)
            geometry = scene.createGeometry(ramses_effect)
            appearance = scene.createAppearance(ramses_effect)

            geometry.setIndexBuffer(indices)
            geometry.setVertexBuffer("a_position", vertices)

            ramses_mesh_node.setAppearance(appearance)
            ramses_mesh_node.setGeometry(geometry)

            translation_node = scene.createNode(f'Positions mesh "{str(ir_node)}" into scene')
            translation_node.setTranslation(ir_node.location[0],
                                            ir_node.location[1],
                                            ir_node.location[2])
            translation_node.addChild(ramses_mesh_node)

            if exportable_scene:
                self._add_to_render_groups(exportable_scene, ir_node, ramses_mesh_node)

            returned_node = translation_node

        elif isinstance(ir_node, PerspectiveCameraNode):
            fov = ir_node.fov * 180 / math.pi
            z_near = ir_node.z_near
            z_far = ir_node.z_far
            aspect_ratio = ir_node.aspect_ratio

            ramses_camera_node = scene.createPerspectiveCamera(name)
            ramses_camera_node.setViewport(0, 0, int(ir_node.width), int(ir_node.height))
            ramses_camera_node.setFrustumFromFoV(fov, aspect_ratio, z_near, z_far)

            rotationX_node = scene.createNode(f'Rotates Camera "{str(ir_node)}" in scene (X)')
            rotationY_node = scene.createNode(f'Rotates Camera "{str(ir_node)}" in scene (Y)')
            rotationZ_node = scene.createNode(f'Rotates Camera "{str(ir_node)}" in scene (Z)')
            # Use several single-axis rotations for maximum compatibility
            # Rotation order: Euler X -> Y -> Z
            rotationZ_node.addChild(rotationY_node)
            rotationY_node.addChild(rotationX_node)
            rotationX_node.addChild(ramses_camera_node)

            translation_node = scene.createNode(f'Positions Camera "{str(ir_node)}" into scene')
            translation_node.setTranslation(ir_node.location[0],
                                            ir_node.location[1],
                                            ir_node.location[2])

            # Translation comes last - after rotation
            translation_node.addChild(rotationZ_node)

            if exportable_scene:
                self._add_to_render_passes(exportable_scene, ir_node, ramses_camera_node)

            returned_node = translation_node

        elif isinstance(ir_node, Node):
            ramses_node = scene.createNode(name)

            returned_node = ramses_node

        else:
            raise NotImplementedError(f"Cannot translate node: {str(ir_node)} !")

        log.debug(f'Translated IRNode "{str(ir_node)}" into "{returned_node}"')
        # TODO: get RAMSES node name from bindings

        return returned_node

    def _build_ramses_render_groups(self,
                                    ramses_scene: RamsesPython.Scene,
                                    ir_groups: List[Node]) -> List[RamsesPython.RenderGroup]:
        """Builds a RAMSES RenderGroup for each GroupNode in the IR.

        Arguments:
            ramses_scene {RamsesPython.Scene} -- The RAMSES Scene
            ir_groups {List[Node]} -- A list of IR Group Nodes.

        Returns:
            List[RamsesPython.RenderGroup] -- A list of RAMSES RenderGroups for each GroupNode in the IR.
        """
        return {group.name : ramses_scene.createRenderGroup(group.name) for group in ir_groups}

    def _build_ramses_render_passes(self,
                                    ramses_scene: RamsesPython.Scene,
                                    ir_root: Node) -> List[RamsesPython.RenderPass]:
        """Builds a RAMSES RenderPass for each CameraNode in the scene.

        Arguments:
            ramses_scene {RamsesPython.Scene} -- [description]
            ir_root {Node} -- [description]

        Returns:
            List[RamsesPython.RenderPass] -- [description]
        """
        ret = {}

        for ir_node in ir_root.traverse():
            if isinstance(ir_node, CameraNode):
                ret[ir_node.name] = ramses_scene.createRenderPass(f'Render pass for {ir_node.name}')

        return ret

    def _add_to_render_groups(self, exportable_scene, ir_node, ramses_mesh_node):
        for ir_group in exportable_scene.ir_groups:
            if ir_group.contains(ir_node):
                #TODO: render order
                exportable_scene.groups[ir_group.name].addMesh(ramses_mesh_node, 0)

    def _add_to_render_passes(self, exportable_scene, ir_camera_node, ramses_camera_node):
        for ir_group in exportable_scene.ir_groups:
            if ir_group.contains(ir_camera_node):
                exportable_scene.passes[ir_camera_node.name].setCamera(ramses_camera_node)


class BlenderRamsesExtractor():
    """Runs over a scene extracting relevant data from bpy"""

    def __init__(self, scene: bpy.types.Scene):
        self.scene = scene

    def run(self):
        log.debug(f'Extracting data from scene {self.scene}')
        representation = SceneRepresentation(self.scene)
        return representation
