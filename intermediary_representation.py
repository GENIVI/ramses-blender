#  -------------------------------------------------------------------------
#  Copyright (C) 2019 Daniel Werner Lima Souza de Almeida -
#                     dwlsalmeida at gmail dot com
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------

from __future__ import annotations # Needed in order for something to reference itself in 'typing'
import bpy
import bmesh
from . import RamsesPython
from . import debug_utils
from . import utils
import mathutils
from typing import List, Any, Dict
import math
import itertools
import pathlib

log = debug_utils.get_debug_logger()

class SceneRepresentation():
    """Defines a minimal representation we want to be able to support in
    RAMSES.
    """

    def __init__(self, scene: bpy.types.Scene, custom_params: Dict[str, utils.CustomParameters]=None):
        self.scene = scene
        self.graph = SceneGraph(scene)
        if not custom_params:
            custom_params = {}
        self.custom_params = custom_params

    def build_ir(self):
        """Builds the intermediary representation from the Blender
        scene"""

        for o in self.scene.objects:
            self.graph.add_node(o)

        self._doCustomParams(self.custom_params)

    def teardown(self):
        self.graph.teardown()

    def _doCustomParams(self, custom_params):
        for scene_object_name, params in custom_params.items():
            blender_object = self.scene.objects[scene_object_name]
            node = self.graph.find_from_blender_object(blender_object)

            if not node:
                # Malformed meshes or other issues
                log.debug(f'Specified extra parameters for object {blender_object.name} but it did not get translated.')
                return

            node = node[0]

            if params.use_custom_GLSL:
                vert_shader, frag_shader = self._load_shaders(scene_object_name, dir=params.shader_dir)
                node.vertex_shader = vert_shader
                node.fragment_shader = frag_shader

    def _load_shaders(self, scene_object_name, dir:str=None):
        return utils.load_shaders(scene_object_name, dir)


class Node():
    """A base class for operations every node must support"""

    def __init__(self, blender_object: bpy.types.Object = None, name=''):
        self.parent = None
        self.children = []
        self.blender_object = blender_object
        self.name = name
        self.location = mathutils.Vector((0.0, 0.0, 0.0))
        self.rotation = mathutils.Euler()
        self.rotation_order = ''

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

        self.dimensions = mathutils.Vector((0.0, 0.0, 0.0))
        self.color = mathutils.Vector((0.0, 0.0, 0.0))

        # Default scale is 1, otherwise objects would not be visible by default
        self.scale = mathutils.Vector((1.0, 1.0, 1.0))
        self.vertex_groups = []

        self.up_axis = 'Z'
        self.forward_axis = 'NEG_Z'

        # The scenes in which this node appears
        self.users_scene = []
        # The collections in which this node appears. This is a new
        # concept in Blender 2.8 for organizational purposes only.
        self.users_collections = []

        # Optional GLSL source code to use when rendering this node
        self.vertex_shader = ''
        self.fragment_shader = ''

        if blender_object:
            self._init_from_blender_object(blender_object)

    def _init_from_blender_object(self, blender_object: bpy.types.Object):
        self.location = blender_object.location
        # TODO have to also chech rotation_mode -> translate correctly
        self.rotation = blender_object.rotation_euler
        self.rotation_order = blender_object.rotation_mode
        self.matrix_basis = blender_object.matrix_basis
        self.matrix_local = blender_object.matrix_local
        self.matrix_parent_inverse = blender_object.matrix_parent_inverse
        self.matrix_world = blender_object.matrix_world

        self.dimensions = blender_object.dimensions
        self.color = blender_object.color
        self.scale = blender_object.scale
        self.vertex_groups = blender_object.vertex_groups

        self.up_axis = blender_object.up_axis
        self.forward_axis = blender_object.track_axis

        self.users_scene = blender_object.users_scene
        self.users_collections = blender_object.users_collection

    def is_placeholder(self):
        """Placehold nodes are possible in order to have more flexibility to
        define concepts that are not a 1:1 translation from Blender. Such
        nodes have no corresponding blender object and are initialized to
        default sane values. Any other node is initialized from its
        Blender object."""
        return self.blender_object is None

    def is_point(self):
        """Whether this node can be represented by a single point,
        such as a point light or a camera"""
        return self.dimensions.length == 0

    def is_root(self):
        """Whether this node is the root of the graph"""
        return self.parent is None

    def contains(self, node: Node) -> bool:
        """Whether this node or its children contains the argument"""
        if self == node:
            return True

        for child in self.children:
            found = child.contains(node)
            if found:
                return found

        return False

    def node_count(self) -> int:
        """Counts the number of nodes in the hierarchy

        Returns:
            int -- The number of nodes in the hierarchy
        """
        return len([node for node in self.traverse()])

    def find(self, attribute: str, value: Any, n: int = 1) -> List[Node]:
        """Search the hierarchy looking for nodes in which attribute == value

        Arguments:
            attribute {str} -- Any attribute contained in node.__dict__
            value {Any} -- Any value to look for
            n {int} -- The number of matches to return. Defaults to 1 \
                and a value of 0 returns all matches

        Returns:
            List[Node] -- A list containing all the matches.
        """

        if n < 0:
            raise RuntimeError

        matches = []

        for attr, val in self.__dict__.items():
            if n and (len(matches) == n):
                break

            if attr.lower() == attribute.lower():
                if val and (val == value):
                    matches.append(self)

        for child in self.children:
            if n and (len(matches) == n):
                break

            found = child.find(attribute, value, n)
            if found:
                matches.extend(found)

        return matches

    def find_from_blender_object(self, blender_object: bpy.types.Object) -> List[Node]:
        """A convenience method to find nodes based on the underlying Blender \
            object

        Arguments:
            blender_object {bpy.types.Object} -- The object to look for in the \
                hierarchy

        Returns:
            List[Node] -- A list with matches
        """

        return self.find(attribute='blender_object', value=blender_object, n=0)

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
            vector_list  -- A list of vectors from Blender.


        Returns:
            List[Float] -- The unpacked values in a Python list.
        """
        a_iterable = [vertex.co if hasattr(vertex, 'co') else vertex for vertex in vector_list]
        return list(itertools.chain.from_iterable(a_iterable))

    def teardown(self):
        for child in self.children:
            child.teardown()
        del self

    def traverse(self):
        yield self

        for child in self.children:
            yield from child.traverse()

    def __str__(self):
        return f'IRNode of type: {type(self)} and name: {self.name}'

class SceneGraph():
    """For every scene, a graph is created so we can translate concepts as close as possible"""

    def __init__(self, scene: bpy.types.Scene, root: Node = None):
        self.root = root if root else Node(name='Root node')
        self.scene = scene

    def add_node(self, o: bpy.types.Object = None, parent: Node = None) -> Node:

        node = self._translate(o) if o else Node('Placeholder node')
        node_parent = None

        if self.is_uninitialized():
            node.name += ' ' + '(Root node)'
            log.debug(f'No root node for this SceneGraph, adding {str(node)} as root')
            self.root = node
            node.parent = None
        else:
            node_parent = parent if parent else self._resolve_parenting(o)
            node_parent.add_child(node)

        assert self.root
        assert self.root.parent is None

        log.debug(f'Scene graph: adding "{node}" with Blender Object: "{o}". Parent is: "{node_parent}"')
        return node

    def _translate(self, o: bpy.types.Object) -> Node:
        """Translates a Blender object into an IR node / node hierarchy.

        Arguments:
            o {bpy.types.Object} -- The object to be translated

        Returns:
            Node -- The node / node hierarchy
        """

        # See https://docs.blender.org/manual/en/dev/editors/3dview/object/types.html
        # See also https://docs.blender.org/manual/en/dev/editors/3dview/object/index.html
        node = None

        if o.type == 'MESH':
            node = MeshNode(o)

            if node.malformed():
                log.debug(f'Malformed mesh with no faces: {str(node)}. '
                          + 'Adding placeholder.')
                old_node = node
                node = Node(blender_object=old_node.blender_object,
                            name='Placeholder node for malformed '
                                 +f'mesh with no faces: {str(old_node)}')
                old_node.teardown()

        elif o.type == 'CAMERA':
            if o.data.type == 'PERSP':
                node = PerspectiveCameraNode(o, self.scene)
            elif o.data.type == 'ORTHO':
                node = OrthographicCameraNode(o)
            else:
                raise NotImplementedError
        elif o.type == 'LIGHT' or o.type == 'LAMP':
            if o.data.type == 'POINT':
                node = PointLightNode(o)
            elif o.data.type == 'SUN':
                node = SunLightNode(o)
            elif o.data.type == 'SPOT':
                node = SpotLightNode(o)
            elif o.data.type == 'AREA':
                node = AreaLightNode(o)

        else: # TODO: map EMPTIES to Node() ?

            log.debug( f'IR SceneGraph: found node: {o.name} of type: {o.type} '
                      + 'in Blender which is currently not implemented. Adding '
                      + 'a placeholder node.')

            node = Node(name=f'Unresolved Blender node: {str(o)} of type {o.type}')

        log.debug(f'Translated Blender object: {o.name} of type: {o.type} into {str(node)}')
        return node

    def _resolve_parenting(self,
                            blender_object: bpy.types.Object) -> Node:
        """Attempts to find a parent for the argument in the graph. \
            Uses the root node if no candidate node is found at first"""

        parent_candidates = self.root.find_from_blender_object(blender_object.parent)

        return parent_candidates[0] if parent_candidates else self.root

    def contains(self, node: Node) -> bool:
        """Whether this SceneGraph contains the argument"""
        return self.root.contains(node)

    def node_count(self, from_node: Node = None) -> int:
        """Return the number of nodes in this graph, optionally starting
        from 'from_node' but usually from root.

        Keyword Arguments:
            from_node {Node} -- optional node to start counting from
            (default: {None})

        Returns:
            int -- The number of nodes counted
        """
        if self.is_uninitialized():
            return 0

        node = from_node if from_node else self.root
        assert node

        count = node.node_count()
        assert count > 0

        return count

    def is_uninitialized(self):
        return self.root is None

    def find(self, attribute: str, value: Any, n: int = 1) -> List[Node]:
        """Search the SceneGraph looking for nodes in which attribute == value

        Arguments:
            attribute {str} -- Any attribute contained in a node
            value {Any} -- Any value to look for
            n {int} -- The number of matches to return. Defaults to 1 \
                and a value of 0 returns all matches

        Returns:
            List[Node] -- A list containing all the matches.
        """
        return self.root.find(attribute, value, n)

    def find_from_blender_object(self, blender_object: bpy.types.Object) -> List[Node]:
        """A convenience method to find nodes based on the underlying Blender \
            object

        Arguments:
            blender_object {bpy.types.Object} -- The object to look for in the \
                hierarchy

        Returns:
            List[Node] -- A list with matches
        """
        return self.root.find_from_blender_object(blender_object=blender_object)

    def debug(self):
        """A convenience method so we can quickly check if a node does not
        error out on its basic operations"""
        print(self)

    def teardown(self):
        """Tears down the SceneGraph, unallocating resources it might have
        acquired from Blender. Should be called after the export is complete
        so the user does not end up with dangling resources which can be very
        memory intensive"""
        self.root.teardown()
        del self

    def traverse(self, from_node: Node = None):
        """Traverse the SceneGraph, optionally starting at 'from_node', but
        usually from the root itself"""
        node = from_node if from_node is not None else self.root
        assert node
        return node.traverse()

    def __str__(self):
        ret = 'SceneGraph containing:\n'
        ret += self.pretty_print_graph(self.root)
        ret += 'End Scenegraph\n'
        return ret

    def pretty_print_graph(self, current_node, indentation=0):
        current_string = (' ' * indentation) + str(current_node) + '\n'
        indentation += 4

        for child in current_node.children:
            current_string += self.pretty_print_graph(child, indentation)

        return current_string

    def as_groups(self) -> List[GroupNode]:
        """Returns a list of nodes, each representing a Blender view layer.

        This method creates a parent 'GroupNode' and assign it children.
        Aside from the root nodes no other nodes are created, only
        references to the IR SceneGraph are taken.

        Returns:
            List[GroupNode] -- A list of GroupNodes
        """
        return [GroupNode(self, view_layer) for view_layer in self.scene.view_layers]


class MeshNode(Node):
    """A class for meshes that tries to provide its data in a way an
    OpenGL-powered renderer would expect"""

    def __init__(self, blender_object: bpy.types.Object):
        super().__init__(blender_object, name = blender_object.name_full)
        self.mesh = None
        self.init_memory_mesh()

    def teardown(self):
        super().teardown()
        log.debug(f'Freeing allocated BMesh object: "{self.mesh}"')
        self.mesh.free()

    def malformed(self):
        faces = self.get_faces()
        return len(faces) == 0

    def init_memory_mesh(self, triangulate=True):
        bmesh_handle = bmesh.new()
        bmesh_handle.from_mesh(self.blender_object.to_mesh())
        log.debug(f'Instantiated BMesh {bmesh_handle} for MeshNode: {self.name}')

        if triangulate:
            MeshNode.triangulate_mesh(mesh=bmesh_handle, faces=bmesh_handle.faces)
            log.debug(f'Triangulated mesh: {bmesh_handle}')

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


class CameraNode(Node):
    def __init__(self, blender_object: bpy.types.Object):

        super().__init__(blender_object=blender_object,
                         name=blender_object.name_full)

        self.fov = blender_object.data.angle
        # TODO: check against glTF-Blender-IO
        self.horizontal_fov = blender_object.data.angle_x
        self.vertical_fov = blender_object.data.angle_y
        self.z_near = blender_object.data.clip_start
        self.z_far = blender_object.data.clip_end

        # Method to fit image and field of view angle inside the sensor.
        # Either 'AUTO', 'HORIZONTAL' or 'VERTICAL'
        self.sensor_fit = blender_object.data.sensor_fit
        # Vertical size of the image sensor area in millimeters
        self.sensor_height = blender_object.data.sensor_height
        # Horizontal size of the image sensor area in millimeters
        self.sensor_width = blender_object.data.sensor_width

        self.shift_x = blender_object.data.shift_x
        self.shift_y = blender_object.data.shift_y


class PerspectiveCameraNode(CameraNode):
    def __init__(self, blender_object: bpy.types.Object, scene: bpy.types.Scene):

        super().__init__(blender_object=blender_object)

        self.scene = scene
        self.width = self.scene.render.pixel_aspect_x * self.scene.render.resolution_x
        self.height = self.scene.render.pixel_aspect_y * self.scene.render.resolution_y

        self.aspect_ratio = self.width / self.height

        if self.width >= self.height:
            if self.sensor_fit != 'VERTICAL':
                self.vertical_fov = 2.0 * math.\
                    atan(math.tan(self.fov * 0.5) / self.aspect_ratio)
            else:
                pass # Keep the initialization done in CameraNode
        else:
            if self.sensor_fit != 'HORIZONTAL':
                pass # Keep the initialization done in CameraNode
            else:
                self.vertical_fov = 2.0 * math.\
                    atan(math.tan(self.fov * 0.5) / self.aspect_ratio)


class OrthographicCameraNode(CameraNode):
    def __init__(self, blender_object: bpy.types.Object):

        super().__init__(blender_object=blender_object)

        self.x_mag = blender_object.data.ortho_scale
        self.y_mag = blender_object.data.ortho_scale


class LightNode(Node):
    def __init__(self, blender_object: bpy.types.Object):

        super().__init__(blender_object=blender_object,
                         name=blender_object.name_full)

        # Pick everthing, just in case.

        self.color = blender_object.data.color
        self.cutoff_distance = blender_object.data.cutoff_distance
        self.distance = blender_object.data.cutoff_distance
        self.node_tree = None  # TODO
        self.specular_factor = blender_object.data.specular_factor
        self.use_nodes = False # TODO

        self.contact_shadow_bias = blender_object.data.contact_shadow_bias
        self.contact_shadow_distance = blender_object.data.contact_shadow_distance
        self.contact_shadow_soft_size = blender_object.data.contact_shadow_soft_size
        self.contact_shadow_thickness = blender_object.data.contact_shadow_thickness

        self.energy = blender_object.data.energy

        self.shadow_buffer_bias = blender_object.data.shadow_buffer_bias
        self.shadow_buffer_bleed_bias = blender_object.data.shadow_buffer_bleed_bias
        self.shadow_buffer_clip_end = blender_object.data.shadow_buffer_clip_end
        self.shadow_buffer_clip_start = blender_object.data.shadow_buffer_clip_start
        self.shadow_buffer_exp = blender_object.data.shadow_buffer_exp
        self.shadow_buffer_samples = blender_object.data.shadow_buffer_samples
        self.shadow_buffer_soft = blender_object.data.shadow_buffer_soft
        self.shadow_color = blender_object.data.shadow_color
        self.shadow_soft_size = blender_object.data.shadow_soft_size



class PointLightNode(LightNode):
    """Omnidirectional point Light"""

    def __init__(self, blender_object: bpy.types.Object):

        super().__init__(blender_object=blender_object)

        if blender_object.data.type != 'POINT':
            raise RuntimeError('Tried to init a PointLightNode with a '
                              +'incompatible Blender object')

        self.constant_coefficient = blender_object.data.constant_coefficient

        self.falloff_curve = blender_object.data.falloff_curve
        self.falloff_type =  blender_object.data.falloff_type
        self.linear_attenuation = blender_object.data.linear_attenuation
        self.quadratic_coefficient = blender_object.data.quadratic_coefficient

        self.use_contact_shadow = blender_object.data.use_contact_shadow
        self.use_shadow = blender_object.data.use_shadow


class SpotLightNode(LightNode):
    """Directional cone Light"""

    def __init__(self, blender_object: bpy.types.Object):

        super().__init__(blender_object=blender_object)

        if blender_object.data.type != 'SPOT':
            raise RuntimeError('Tried to init a SpotLightNode with a '
                              +'incompatible Blender object')

        self.constant_coefficient = blender_object.data.constant_coefficient

        self.falloff_curve = blender_object.data.falloff_curve
        self.falloff_type =  blender_object.data.falloff_type
        self.linear_attenuation = blender_object.data.linear_attenuation
        self.quadratic_coefficient = blender_object.data.quadratic_coefficient

        self.show_cone = blender_object.data.show_cone
        self.spot_size = blender_object.data.spot_size

        self.use_contact_shadow = blender_object.data.use_contact_shadow
        self.use_shadow = blender_object.data.use_shadow

        self.use_square = blender_object.data.use_square


class SunLightNode(LightNode):
    """Constant direction parallel ray Light"""

    def __init__(self, blender_object: bpy.types.Object):

        super().__init__(blender_object=blender_object)

        if blender_object.data.type != 'SUN':
            raise RuntimeError('Tried to init a SunLightNode with a '
                              +'incompatible Blender object')

        self.angle=blender_object.data.angle

        self.shadow_cascade_count=blender_object.data.shadow_cascade_count
        self.shadow_cascade_exponent=blender_object.data.shadow_cascade_exponent
        self.shadow_cascade_fade=blender_object.data.shadow_cascade_fade
        self.shadow_cascade_max_distance = blender_object.data.shadow_cascade_max_distance

        self.use_contact_shadow = blender_object.data.use_contact_shadow
        self.use_shadow = blender_object.data.use_shadow


class AreaLightNode(LightNode):
    """Directional area Light"""
    def __init__(self, blender_object: bpy.types.Object):

        super().__init__(blender_object=blender_object)

        if blender_object.data.type != 'AREA':
            raise RuntimeError('Tried to init a SunLightNode with a '
                              +'incompatible Blender object')

        self.constant_coefficient = blender_object.data.constant_coefficient

        self.falloff_curve = blender_object.data.falloff_curve
        self.falloff_type =  blender_object.data.falloff_type
        self.linear_attenuation = blender_object.data.linear_attenuation
        self.quadratic_coefficient = blender_object.data.quadratic_coefficient


        self.shadow_color = blender_object.data.shadow_color
        self.shadow_soft_size = blender_object.data.shadow_soft_size

        self.shape=blender_object.data.shape
        self.size = blender_object.data.size
        self.size_y=blender_object.data.size_y


class GroupNode(Node):
    """A node that represents a group of nodes. Should only be created
    after the full scene graph is created so the it can find any
    object it references in the scene graph"""

    def __init__(self, scene_graph: SceneGraph, view_layer: bpy.types.ViewLayer):

        super().__init__(name=f'GroupNode for {view_layer.name}')

        """While most nodes were defined with a pointer to their parent,
        groups hold pointers to their children and do not change the
        existing hierarchy"""
        # TODO: plenty of other interesting options in this bpy_struct,
        # maybe we could use it some more?

        self.scene_graph = scene_graph
        self.view_layer = view_layer
        self.use = view_layer.use
        self.children = []

        for blender_object in self.view_layer.objects:
            ir_nodes = self.scene_graph.find_from_blender_object(blender_object)
            assert len(ir_nodes) == 1
            self.children.extend(ir_nodes)
