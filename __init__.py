bl_info = {
    "name": "RAMSES Scene Exporter",
    "author": "#TODO",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "View3D",
    "description": "A add-on for exporting RAMSES scenes from Blender scenes",
    "category": "Import-Export",
    "Warning": "Under development!",
    "wiki-url": "",
    "tracker-url": ""
}

def in_development_mode():
    return 'bpy' in locals()

import bpy
import logging
import random
import time
import gpu
from .ramses_blender_exporter import RamsesBlenderExporter


log = logging.getLogger('ramses-scene-exporter')


def monkey_create_random(scene, n: int):
    for i in range(n):
        r = random.Random()
        r.seed(time.time())

        x = r.randint(0, 25)
        y = r.randint(0, 25)
        z = r.randint(0, 25)

        loc = (x, y, z)
        bpy.ops.mesh.primitive_monkey_add(location=loc)  # Adds Suzanne.


def print_objects(scene):
    for o in scene_get_objects(scene):
        print(f"In scene {str(scene)} found object {str(o)}")


def clear_scene(scene):
    objects = scene_get_objects(scene)
    for o in objects:
        o.select_set(state = True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.delete()  # Delete the currently selected object


def print_materials():
    materials = bpy.data.materials
    raise NotImplementedError
    # TODO


def object_print_local_coords(objects):
    for o in objects:
        print(f"Now printing local coordinates for object {str(o)}")
        try:
            vertices = o.data.vertices
            index = 0
            for vertex in vertices:
                print(f"vertex {index} local coordinates are:{vertex.co[0]}, {vertex.co[1]}, {vertex.co[2]}")
                index += 1
        except AttributeError:
            print(f"Object {str(o)} has no vertex attribute.")


def object_print_global_coords(objects):
    for o in objects:
        print(f"Now printing global coordinates for object {str(o)}")
        world_matrix = o.matrix_world
        try:
            vertices = o.data.vertices
            index = 0
            for vertex in o.data.vertices:
                global_co = world_matrix @ vertex.co
                print(f"vertex {index} global coordinates are:{global_co[0]}, {global_co[1]}, {global_co[2]}")
                index += 1
        except AttributeError:
            print(f"Object {str(o)} has no vertex attribute.")


def object_print_transformation_matrix(objects):
    for o in objects:
        print(f"Transformation matrix (world matrix) for object {str(o)} is {str(o.matrix_world)}")


def scene_get_objects(scene):
    return scene.objects


def scene_print_objects(scene):
    print("Now printing all objects on the current scene.")
    objects = scene_get_objects(scene)
    for o in objects:
        print(o)


class SceneDumpOperator(bpy.types.Operator):
    bl_idname = "object.scenedumpoperator"
    bl_label = "SceneDumpOperator"

    def execute(self, context):
        scene = bpy.context.scene
        clear_scene(scene)

        monkey_create_random(scene, 5)

        scene_print_objects(scene)
        objects = scene_get_objects(scene)


        exporter = RamsesBlenderExporter(bpy.data.scenes)
        exporter.extract_from_blender_scene()

        return {'FINISHED'}


def register():
    log.info("RAMSES Scene Exporter: Add-on registered.")
    bpy.utils.register_class(SceneDumpOperator)
    print("RAMSES Scene Exporter: Add-on registered.")


def unregister():
    bpy.utils.unregister_class(SceneDumpOperator)
    log.info("RAMSES Scene Exporter: Add-on unregistered.")