import unittest
import bpy
from ramses_export.intermediary_representation import *
import ramses_export.debug_utils

class TestVectorUnpack(unittest.TestCase):
    def setUp(self):
        scene = bpy.context.scene

        debug_utils.clear_scene(scene)
        bpy.ops.mesh.primitive_cube_add()
        self.node = MeshNode(blender_object=bpy.context.active_object)

    def tearDown(self):
        pass

    def test_vector_unpack_from_bmesh(self):
        vertices = self.node.get_vertices()
        unpacked = self.node.vector_unpack(vertices)

        i = 0

        for bmesh_vec_seq in vertices:
            vertex = bmesh_vec_seq.co
            for vertex_component in vertex:
                self.assertEqual(vertex_component, unpacked[i])
                i += 1

    def test_vector_unpack_from_mathutils(self):
        import mathutils

        vectors = [mathutils.Vector((1.0, 1.0, 1.0))]
        unpacked = self.node.vector_unpack(vectors)

        i = 0

        for vector in vectors:
            for vector_component in vector:
                self.assertEqual(vector_component, unpacked[i])
                i += 1


    def test_vector_unpack_from_mathutils_input_not_list_exception(self):
        import mathutils

        vectors = mathutils.Vector((1.0, 1.0, 1.0))
        with self.assertRaises(TypeError):
            unpacked = self.node.vector_unpack(vectors)
