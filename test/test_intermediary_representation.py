
#  -------------------------------------------------------------------------
#  Copyright (C) 2019 Daniel Werner Lima Souza de Almeida
#                     dwlsalmeida@gmail.com
#  -------------------------------------------------------------------------
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
#  -------------------------------------------------------------------------


import unittest
import bpy
from ramses_export.intermediary_representation import *
import ramses_export.debug_utils
from ramses_export.test.exporter_test_base import ExporterTestBase


class TestVectorUnpack(ExporterTestBase, unittest.TestCase):
    def __init__(self, methodName='runTest'):
        # Deriving from ExporterTestBase makes passing arguments easier
        unittest.TestCase.__init__(self, methodName)
        ExporterTestBase.__init__(self)

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


class TestFind(unittest.TestCase):
    def setUp(self):
        scene = bpy.context.scene

        debug_utils.clear_scene(scene)
        bpy.ops.mesh.primitive_cube_add()
        self.node = MeshNode(blender_object=bpy.context.active_object)

    def tearDown(self):
        pass

    def test_find_from_blender_object_None_returns_EmptyList(self):
        blender_object = None
        found = self.node.find_from_blender_object(blender_object)
        self.assertEqual(found, [])
