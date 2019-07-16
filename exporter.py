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
import itertools
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
                                           scene_representation.scene)
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
                  f'Recursively building RAMSES nodes for IR node: "{str(ir_node)}", '
                 +f'RAMSES parent is "{parent.getName() if parent else None}"')

        translation_result = self.translate(scene, ir_node, exportable_scene=exportable_scene)
        first_translated_node = translation_result[0]
        last_translated_node = translation_result[-1]

        if ir_node.children:
            current_depth += 1

        for child in ir_node.children:
            self._ramses_build_recursively(scene,
                                           child,
                                           exportable_scene,
                                           parent=last_translated_node,
                                           current_depth=current_depth)

        if parent:
            parent.addChild(first_translated_node)

        return first_translated_node


    def translate(self, scene: RamsesPython.Scene, ir_node: Node, exportable_scene: ExportableScene = None) -> RamsesPython.Node:
        """Translates the IRNode into a RAMSES node / graph

        Arguments:
            ir_node {Node} -- The node to be translated
            scene {RamsesPython.Scene} -- The current RAMSES Scene to \
                create the node from
            exportable_scene {ExportableScene} -- optional: sets up RenderGroups and RenderPasses.

        Returns:
            List[RamsesPython.Node] -- A list of all translated nodes
        """

        name = ir_node.name
        ret = []

        # Translate the transforms i.e. scaling, rotation and translation to RAMSES.
        transformation_nodes = self._resolve_transforms_for_node(scene, ir_node)
        ret.extend(transformation_nodes)

        last_transformation = transformation_nodes[-1] if transformation_nodes else None

        ramses_node = None

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

            if exportable_scene:
                self._add_to_render_groups(exportable_scene, ir_node, ramses_mesh_node)

            ret.append(ramses_mesh_node)
            ramses_node = ramses_mesh_node

        elif isinstance(ir_node, PerspectiveCameraNode):
            fov = ir_node.fov * 180 / math.pi
            z_near = ir_node.z_near
            z_far = ir_node.z_far
            aspect_ratio = ir_node.aspect_ratio

            ramses_camera_node = scene.createPerspectiveCamera(name)
            ramses_camera_node.setViewport(0, 0, int(ir_node.width), int(ir_node.height))
            ramses_camera_node.setFrustumFromFoV(fov, aspect_ratio, z_near, z_far)

            if exportable_scene:
                self._add_to_render_passes(exportable_scene, ir_node, ramses_camera_node)

            ret.append(ramses_camera_node)
            ramses_node = ramses_camera_node

        elif isinstance(ir_node, Node):
            # TODO should also translate and rotate, same as with camera
            node = scene.createNode(name)
            ret.append(node)
            ramses_node = node

        else:
            raise NotImplementedError(f"Cannot translate node: {str(ir_node)} !")

        # Final hierarchy is: first_transform -> .. -> last_transform -> ramses_node -> ..
        if last_transformation:
            last_transformation.addChild(ramses_node)

        log.debug(f'Translated IRNode "{str(ir_node)}" into "{ramses_node.getName()}"')

        return ret


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

    def _resolve_rotation_order(self,
                                ramses_scene: RamsesPython.Scene,
                                ir_node: RamsesPython.Node) -> List[RamsesPython.Node]:
        """Resolves the order of RAMSES rotation nodes based on Blender's
        rotation order.

        Rotations are not commutative, that is, the end result depend
        on the order in which individual rotations happen. Use this
        method to properly order the RAMSES node to achieve the same
        rotation order used in Blender.

        Arguments:
            ramses_scene {RamsesPython.Scene} -- The scene to create
            nodes from.
            ir_node {RamsesPython.Node} -- The node to resolve
            rotation from.

        Returns:
            List[RamsesPython.Node] -- A list with the RAMSES nodes in the
            order they were added.
        """

        rotation = ir_node.rotation
        rotation_order = ir_node.rotation.order

        assert len(rotation) == 3 # A value for each axis
        assert len(rotation_order) == 3 # Three axis of rotation

        assert rotation_order[0] in ('X', 'Y', 'Z')
        assert rotation_order[1] in ('X', 'Y', 'Z')
        assert rotation_order[2] in ('X', 'Y', 'Z')

        ret = []

        for i in range(3):
            # Use several single-axis rotations for maximum compatibility
            rotation_degrees = -rotation[i] * 180 / math.pi
            rotation_node = ramses_scene.createNode(\
                f'Rotates node "{str(ir_node)}" in axis: ({str(rotation_order[i])}) by {rotation_degrees}')

            # For some reason, blender uses left-hand instead of right-hand rule for Euler rotations
            # Thus, rotation values are negative
            # TODO investigate why blender rotates like this

            if rotation_order[i] == 'X':
                rotation_node.setRotation(rotation_degrees, 0, 0)
            elif rotation_order[i] == 'Y':
                rotation_node.setRotation(0, rotation_degrees, 0)
            elif rotation_order[i] == 'Z':
                rotation_node.setRotation(0, 0, rotation_degrees)

            ret.append(rotation_node)

        ret.reverse() # e.g. XYZ is (Z -> Y -> X -> Node)

        for count, node in enumerate(ret):
            try:
                # Set up parenting in order nodes were added.
                next_node = ret[count + 1]
                node.addChild(next_node)
            except IndexError:
                break

        return ret

    def _resolve_transforms_for_node(self,
                                     ramses_scene: RamsesPython.Scene,
                                     ir_node: RamsesPython.Node) -> List[RamsesPython.Node]:
        """
        Resolves the transforms needed to properly set this node in the
        scene. The order of the linear transformations applied are:
        Scale, Rotations, Translation.

        Arguments:
            ramses_scene {RamsesPython.Scene} -- The scene to create
            nodes from.
            ir_node {RamsesPython.Node} -- The node to resolve
            rotation from.

        Returns:
            List[RamsesPython.Node] -- A list with the RAMSES nodes in the
            order they were added.
        """

        if ir_node.is_root():
            # Do not append any transforms to the root node itself.
            return []

        assert isinstance(ir_node.scale, mathutils.Vector)
        scale_node = ramses_scene.createNode(f'Scales {str(ir_node)} by {str(ir_node.scale)}')
        scale_node.setScaling(ir_node.scale[0], ir_node.scale[1], ir_node.scale[2])

        rotation_nodes = self._resolve_rotation_order(ramses_scene, ir_node)

        translation_node = ramses_scene.createNode(f'Translates "{str(ir_node)}" by {str(ir_node.location)}')
        translation_node.setTranslation(ir_node.location[0],
                                        ir_node.location[1],
                                        ir_node.location[2])

        # Set up parenting: scaling -> first_rotation ... last_rotation -> translation
        first_rotation = rotation_nodes[0]
        last_rotation = rotation_nodes[-1]

        translation_node.addChild(first_rotation)
        last_rotation.addChild(scale_node)

        # Flatten the output before returning.
        ret = list(itertools.chain.from_iterable([
                                                  [translation_node],
                                                  rotation_nodes,
                                                  [scale_node],
                                                 ]))

        return ret


class BlenderRamsesExtractor():
    """Runs over a scene extracting relevant data from bpy"""

    def __init__(self, scene: bpy.types.Scene):
        self.scene = scene

    def run(self):
        log.debug(f'Extracting data from scene {self.scene}')
        representation = SceneRepresentation(self.scene)
        return representation
