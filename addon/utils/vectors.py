import bpy
import math
import bmesh
from functools import cache, lru_cache
from mathutils import Vector
from .logger import log




def get_illumposition(model) -> Vector:

    def get_collection_illumpos(collection: bpy.types.Collection) -> Vector:
        scene:bpy.types.Scene = bpy.context.scene
        depsgraph = bpy.context.evaluated_depsgraph_get()

        current_frame = scene.frame_current
        scene.frame_set(0)

        verts_world = []
 
        for obj in collection.all_objects:
            if obj.type != 'MESH':
                continue

            eval_obj = obj.evaluated_get(depsgraph)
            mesh = eval_obj.to_mesh()
            bm = bmesh.new()
            bm.from_mesh(mesh)

            for v in bm.verts:
                verts_world.append(eval_obj.matrix_world @ v.co)

            bm.free()
            eval_obj.to_mesh_clear()

        scene.frame_set(current_frame)

        if verts_world:
            return sum(verts_world, Vector()) / len(verts_world)
        else:
            return None


    if model.illumposition_source == 'MANUAL':
        return Vector(model.illumposition_vector)
    elif model.illumposition_source == 'REFERENCE':
        return Vector(get_collection_illumpos(model.reference)) if model.reference else None
    elif model.illumposition_source == 'COLLISION':
        return Vector(get_collection_illumpos(model.collision)) if model.collision else None
    elif model.illumposition_source == '3DCURSOR':
        return Vector(bpy.context.scene.cursor.location)
    else:
        return Vector((0,0,0))


def get_origin(model) -> Vector:

    if model.origin_source == 'MANUAL':
        vec = Vector(model.origin)

    elif model.origin_source == '3DCURSOR':
        vec = Vector(bpy.context.scene.cursor.location)

    elif model.origin_source == 'OBJECT' and model.origin_object:
        vec = Vector(model.origin_object.location)
    
    else:
        vec = Vector((0,0,0))

    return vec


def blender_to_source(vec: Vector) -> Vector:
    return Vector((vec.y, -vec.x, vec.z))


def rotate_z(vec: Vector, angle_degrees: float) -> Vector:
    theta = math.radians(angle_degrees)
    x, y, z = vec
    x_new = x * math.cos(theta) - y * math.sin(theta)
    y_new = x * math.sin(theta) + y * math.cos(theta)
    return Vector((x_new, y_new, z))