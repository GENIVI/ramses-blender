import logging
import bpy
import random
import time

def setup_logging(fname: str):
    with open(fname, 'w') as f:
        f.truncate()

    logger = logging.getLogger('ramses-scene-exporter')
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    fh = logging.FileHandler(fname)
    fh.setLevel(logging.DEBUG)


    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(fh)

def get_debug_logger():
    return logging.getLogger('ramses-scene-exporter')

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
