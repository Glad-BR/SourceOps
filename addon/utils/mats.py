import bpy
import cv2
import numpy as np

from enum import Enum

class BlenderInputNodes(Enum):
    BaseColor = 'Base Color'
    Roughness = 'Roughness'
    Metallic = 'Metallic'
    Normal = 'Normal'
    Emissive = 'Emission Color'



def blender_to_numpy(img: bpy.types.Image) -> np.ndarray:
    '''Converts a Blender image to a numpy array with shape (height, width, channels) as a float32 array with values in the range [0, 1].'''

    width, height = img.size
    channels = img.channels

    pixel_count = width * height * channels
    flat_array = np.empty(pixel_count, dtype=np.float32)

    img.pixels.foreach_get(flat_array)

    image_array = flat_array.reshape((height, width, channels))
    image_array = np.flipud(image_array)

    return image_array


#def blender_to_byte(bpy_img: bpy.types.Image) -> bytes:
#    '''Converts a Blender image to a byte array with shape (height, width, channels) as a uint8 array with values in the range [0, 255].'''
#    flipped = (np.clip(blender_to_numpy(bpy_img) * 255, 0, 255).astype(np.uint8))
#    return flipped.tobytes()

#def blender_to_pil(bpy_img: bpy.types.Image) -> Image.Image:
#    '''Converts a Blender image to a PIL Image object.'''
#    return Image.frombytes("RGBA", (bpy_img.size[0], bpy_img.size[1]), blender_to_byte(bpy_img))


def np_grayscale(image: np.ndarray) -> np.ndarray:
    if image is not None:
        gray = np.mean(image[:, :, :3], axis=2).astype(np.float32)
        return gray
        #return image[:, :, 0]
    else:
        return None


def norm_size(image1: np.ndarray, image2: np.ndarray) -> np.ndarray:
    if image1 is not None: 
        if image2 is not None:
            if image1.shape[:2] != image2.shape[:2]:
                target_size = image2.shape[:2][::-1] 
                return cv2.resize(image1, target_size)
        return image1
    return None



def get_bsdf_node(material: bpy.types.Material, node_type: str = 'BSDF_PRINCIPLED') -> bpy.types.ShaderNodeBsdfPrincipled|None:
    if material and material.node_tree:
        principled = next(
            (n for n in material.node_tree.nodes if n.type == node_type),
            None
        )
        return principled
    return None


def probe_bsdf(material: bpy.types.Material, probe_node: BlenderInputNodes) -> bpy.types.Image|None:

    if material and material.node_tree:
        principled = get_bsdf_node(material, node_type='BSDF_PRINCIPLED')

        if principled:
            selected_input = principled.inputs[probe_node.value]
            if selected_input.is_linked:
                from_node = selected_input.links[0].from_node

                if from_node.type == 'NORMAL_MAP':
                    normal_map_node = from_node
                    normal_map_input = normal_map_node.inputs['Color']

                    if normal_map_input.is_linked:
                        from_node = normal_map_input.links[0].from_node

                        if from_node.type == 'TEX_IMAGE':
                            image = from_node.image
                            if image:
                                return image

                if from_node.type == 'TEX_IMAGE':
                    image = from_node.image
                    if image:
                        return image
    return None





def get_all_mats(collection: bpy.types.Collection) -> set[bpy.types.Material]:
    materials: set[bpy.types.Material] = set()
    for obj in collection.all_objects:
        if hasattr(obj.data, "materials"):
            for mat in obj.data.materials:
                if mat is not None:
                    materials.add(mat)
    return materials


def get_all_coll(model) -> set[bpy.types.Collection]:

    colls: set[bpy.types.Collection] = set()

    reference = model.reference
    bodygroups = model.bodygroups_items
    lods_items = model.lods_items

    if reference:
        colls.add(reference)

    if bodygroups:
        for bodygroup in bodygroups:
            if bodygroup.sublist_items:
                for sublist in bodygroup.sublist_items:
                    if sublist.reference:
                        colls.add(sublist.reference)

    if lods_items:
        for lod in lods_items:
            if lod.replacemodel_items:
                for replace in lod.replacemodel_items:
                    if replace.source:
                        colls.add(replace.source)
                    if replace.target:
                        colls.add(replace.target)
    return colls


def mats_from_model(model) -> set[bpy.types.Material]:

    materials: set[bpy.types.Material] = set()

    colls = get_all_coll(model)

    for collection in colls:

        mats = get_all_mats(collection)
        if mats:
            for mat in mats:
                materials.add(mat)

    return materials