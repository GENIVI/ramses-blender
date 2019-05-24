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

    def __init__(self, blender_object: bpy.types.Object = None, name=''):
        self.parent = None
        self.children = []
        self.blender_object = blender_object
        self.name = name

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

    def vector_unpack(self, vector_list) -> List[float]:
        """Unpack a vector list i.e. [Vector(1., 1., 1.), Vector(...) ...]
        into [1., 1., 1., ...]

        Useful for passing values into a rendering engine.

        Arguments:
            vector_list  -- A vector from Blender.


        Returns:
            List[Float] -- The unpacked values in a Python list.
        """
        return [vertex.co for vertex in vector_list]

    def teardown(self):
        for child in self.children:
            child.teardown()

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

    def debug(self):
        """A convenience method so we can quickly check if a node does not
        error out on its basic operations"""
        pass

    def teardown(self):
        """Tears down the SceneGraph, unallocating resources it might have
        acquired from Blender. Should be called after the export is complete
        so the user does not end up with dangling resources which can be very
        memory intensive"""
        self.root.teardown()


class MeshNode(Node):
    """A class for meshes that tries to provide its data in a way an
    OpenGL-powered renderer would expect"""

    def __init__(self, blender_object: bpy.types.Object):
        super().__init__(blender_object)
        self.mesh = None
        self.init_memory_mesh()

    def teardown(self):
        super().teardown()
        self.mesh.free()

    def init_memory_mesh(self, triangulate=True):
        bmesh_handle = bmesh.new()
        bmesh_handle.from_mesh(self.blender_object.to_mesh())
        log.debug(f'Instantiated BMesh {self.mesh} for MeshNode: {self.name}')

        if triangulate:
            MeshNode.triangulate_mesh(mesh=bmesh_handle, faces=bmesh_handle.faces)
            log.debug(f'Triangulated mesh: {self.mesh}')

        self.mesh = bmesh_handle

    @staticmethod
    def triangulate_mesh(mesh, faces):
        """ Triangulates the argument in-place."""
        #Artists quite often strive for quads (i.e. four vertices per face),
        # but for rendering purposes, triangles are often preferred. This same
        #approach is used by the official .obj exporter

        bmesh.ops.triangulate(mesh, faces=faces)

    def get_vertices(self) -> bmesh.types.BMVertSeq:
        self.mesh.verts.ensure_lookup_table()
        return self.mesh.verts

    def get_vertex_buffer(self) -> List[float]:
        """Returns an unpacked vertex buffer suitable for rendering engines"""
        vertices = self.get_vertices()
        return self.vector_unpack(vertices)

    def get_normal_buffer(self, b_use_vertex_normals=True):
        """Returns an unpacked normal buffer suitable for rendering engines"""
        normals = self.get_vertex_normals() \
            if b_use_vertex_normals else self.get_face_normals()
        return self.vector_unpack(normals)

    def get_vertex_normals(self) -> List[mathutils.Vector]:
        vertices = self.get_vertices()
        return [vertex.normal for vertex in vertices]

    def get_face_normals(self, split=True) -> List[mathutils.Vector]:
        faces = self.get_faces()
        return [face.normal for face in faces]

    def get_tex_coords(self):
        raise NotImplementedError

    def get_faces(self) -> bmesh.types.BMFaceSeq:
        self.mesh.faces.ensure_lookup_table()
        return self.mesh.faces

    def get_indices(self) -> List[int]:
        faces = self.get_faces()
        indices = []

        for face in faces:
            for vertex in face.verts:
                indices.append(vertex.index)

        return indices

    def get_textures(self):
        pass

    def get_materials(self):
        pass

    def debug(self):
        print(self.get_vertices())
        print(self.get_vertex_normals())
        print(self.get_face_normals())
        print(self.get_faces())
        print(self.get_indices())
