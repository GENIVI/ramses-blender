from __future__ import annotations # Needed in order for something to reference itself in 'typing'
import bpy
import bmesh
from . import RamsesPython
import logging
import mathutils
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


class SceneRepresentation():
    """Defines a minimal representation we want to be able to support in
    RAMSES.
    """

    def __init__(self,
                 scene: bpy.types.Scene,
                 objects,
                 camera,
                 animation_data,
                 world):
        self.scene = scene
        self.objects = objects
        self.camera = camera
        self.animation_data = animation_data
        self.world = world

        self.graph = SceneGraph(scene)
        for o in self.objects:
            self.graph.add_node(o)


class Node():
    """A base class for operations every node must support"""

    def __init__(self, bo: bpy.types.Object = None):
        self.parent = None
        self.children = []

        # See https://docs.blender.org/api/master/bpy.types.Object.html
        # Matrix access to location, rotation and scale (including deltas),
        # before constraints and parenting are applied
        self.matrix_basis = mathutils.Matrix().to_4x4().identity()
        # Parent relative transformation matrix - WARNING: Only takes into
        # account ‘Object’ parenting, so e.g. in case of bone parenting you
        # get a matrix relative to the Armature object, not to the actual
        # parent bone
        self.matrix_local = mathutils.Matrix().to_4x4().identity()
        # Inverse of object’s parent matrix at time of parenting
        self.matrix_parent_inverse = mathutils.Matrix().to_4x4().identity()
        # Worldspace transformation matrix, that is, the matrix that transforms
        # into the viewport's coordinate system
        self.matrix_world = mathutils.Matrix().to_4x4().identity()

    def find(self, node: Node) -> Node:
        if self == node:
            return self

        for child in self.children:
            found = child.find(node)
            if found:
                return found

        return None

    def add_child(self, node: Node):
        node.parent = self
        self.children.append(node)

    def get_before_parenting_transform(self): return self.matrix_basis
    def get_transform_relative_to_parent(self): return self.matrix_local
    def get_parent_inverse_transform(self): return self.matrix_parent_inverse
    def get_world_transform(self): return self.matrix_world



class SceneGraph():
    """For every scene, a graph is created so we can translate concepts as close as possible"""

    def __init__(self, scene: bpy.types.Scene, root: Node = Node()):
        self.root = root
        self.scene = scene

    def add_node(self, o: bpy.types.Object, parent: Node = None) -> Node:
        log.debug(f"Adding Blender Object: {o} as a node for root {self.root} and {parent} as parent")

        node = None

        # See https://docs.blender.org/manual/en/dev/editors/3dview/object/types.html
        # See also https://docs.blender.org/manual/en/dev/editors/3dview/object/index.html
        if o.type == 'MESH':
            node = MeshNode(o)
        elif o.type == 'CAMERA':
            node = CameraNode(o)
        elif o.type == 'LIGHT' or o.type == 'LAMP':
            node = LightNode(o)
        else: # TODO: map EMPTIES to Node() ?
            node = ObjectNode(o)

        if self.root is None:
            root = node
        else:
            parent = node.find(parent) if parent is not None else self.root
            parent.add_child(node)

        return node

    def find(self, node: Node) -> Node:
        return self.root.find(node)


class MeshNode(Node):

    def __init__(self, bo: bpy.types.Object):
        super().__init__(bo)
        self.mesh = bo.to_mesh()
        # TODO: pass apply_modifiers as a user pref. Note: to_mesh creates a
        # new mesh that must be deleted

    def get_vertices(self) -> bpy.types.VertexGroup:
        return self.mesh.vertices

    def get_normals(self):
        return self.mesh.calc_normals_split()

    def get_tex_coords(self):
        raise NotImplementedError

    def get_faces(self):
        return self.mesh.polygons

    def get_indices(self):
        pass

    def get_textures(self):
        pass

    def get_materials(self):
        pass
