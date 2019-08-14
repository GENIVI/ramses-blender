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
from . import utils
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

    def extract_from_blender_scene(self, custom_params=None):
        """Extract the scene graph from Blender, building an internal
        representation that can then be used to build a RAMSES scene"""

        for scene in self.scenes:
            extractor = BlenderRamsesExtractor(scene)
            representation = extractor.run(custom_params)
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

    def do_passes(self, scene_representation: SceneRepresentation, ramses_scene: RamsesPython.Scene):
        for layer in scene_representation.layers:
            assert isinstance(layer, ViewLayerNode)

            render_pass = ramses_scene.createRenderPass(f'RenderPass for {layer.name}')

            scene_camera_blender_object = scene_representation.camera
            scene_camera_ir = scene_representation.graph.find_from_blender_object(scene_camera_blender_object)[0]

            camera = RamsesPython.toCamera(ramses_scene.findObjectByName(scene_camera_ir.name))
            render_pass.setCamera(camera)

            self.do_groups(scene_representation, ramses_scene, render_pass)

    def do_groups(self,
                  scene_representation: SceneRepresentation,
                  ramses_scene: RamsesPython.Scene,
                  ramses_pass: RamsesPython.RenderPass):

        def do_group(scene_representation, ramses_scene, ramses_pass, current_node):
            assert isinstance(current_node, ViewLayerNode) or isinstance(current_node, LayerCollectionNode)

            current_group = ramses_scene.createRenderGroup(f'RenderGroup for {current_node.name}')
            render_order = 0
            empty = True

            for child in current_node.children:

                if isinstance(child, MeshNode):
                    # NOTE: I guess evaluating objects might change them, so we should maybe
                    #       create new objects in RAMSES (i.e. by calling translate())
                    translation_result = self.translate(ramses_scene, child)
                    assert translation_result

                    ramses_mesh = RamsesPython.toMesh(ramses_scene.findObjectByName(child.name))
                    assert ramses_mesh

                    current_group.addMesh(ramses_mesh, render_order)
                    render_order += 1

                    empty = False

                elif isinstance(child, LayerCollectionNode):
                    child_group = do_group(scene_representation, ramses_scene, ramses_pass, current_node=child)
                    if child_group:
                        empty = False
                        current_group.addRenderGroup(child_group, render_order)
                        render_order += 1

            if empty:
                ramses_scene.destroy(current_group)
                current_group = None

            return current_group

        for layer in scene_representation.layers:
            order_within_pass = 0
            group = do_group(scene_representation, ramses_scene, ramses_pass, current_node=layer)
            if group:
                # Do not fail if we do not find meshes (i.e. blank scene, empty collection, etc)
                ramses_pass.addRenderGroup(group, order_within_pass)
                order_within_pass += 1

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

        exportable_scene = ExportableScene(self.ramses,
                                           ramses_scene,
                                           scene_representation)

        log.debug(\
            f'Intermediary representation consists of:\n{str(scene_representation.graph)}')

        ramses_root = self._ramses_build_recursively(ramses_scene,
                                                     ir_root,
                                                     parent=None,
                                                     exportable_scene=exportable_scene)

        self.do_passes(scene_representation, ramses_scene)

        log.debug(f'Successfully built RAMSES Scenegraph: {str(ramses_root)}. Tearing down the IR graph')
        scene_representation.teardown()


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
            # NOTE: normals, texcoords and other data are easily
            #       found in intermediary_representation.MeshNode

            # NOTE: current implementation is to require either
            #       the default shaders or user-supplied ones.
            assert ir_node.vertex_shader
            assert ir_node.fragment_shader

            vertex_shader = ir_node.vertex_shader
            fragment_shader = ir_node.fragment_shader

            ramses_effect = scene.createEffect(vertex_shader, fragment_shader)
            geometry = scene.createGeometry(ramses_effect)
            appearance = scene.createAppearance(ramses_effect)

            geometry.setIndexBuffer(indices)
            geometry.setVertexBuffer(ir_node.vertexformat['position'], vertices)

            ramses_mesh_node.setAppearance(appearance)
            ramses_mesh_node.setGeometry(geometry)

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

    def run(self, custom_params=None):
        log.debug(f'Extracting data from scene {self.scene}')
        representation = SceneRepresentation(self.scene, custom_params)
        return representation
