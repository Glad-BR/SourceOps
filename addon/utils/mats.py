import bpy

import time

from pathlib import Path
from enum import Enum

from PIL import Image, ImageChops
import numpy as np

class BlenderInputNodes(Enum):
    BaseColor = 'Base Color'
    Diffuse = BaseColor #Alias
    Roughness = 'Roughness'
    Metallic = 'Metallic'
    Normal = 'Normal'
    Emissive = 'Emission Color'


def save_blender_img(image, save_path:str|Path, name_override:str=None) -> Path:
    name = f'{image.name if not name_override else name_override}.{str(image.file_format).lower()}' # i cry
    file = (Path(save_path) / name)
    image.save(filepath=str(file))

    if file.exists():
        return file
    else:
        print(f'Failed to save {file}')
        print(image)
        return None


def blender_to_numpy(bpy_img) -> np.ndarray:
    '''Converts a Blender image to a numpy array with shape (height, width, channels) as a float32 array with values in the range [0, 1].'''
    width = bpy_img.size[0]
    height = bpy_img.size[1]
    channels = 4
    
    float_pixels = np.empty(width * height * channels, dtype=np.float32)
    bpy_img.pixels.foreach_get(float_pixels)

    float_pixels = float_pixels.reshape((height, width, channels))
    flipped = float_pixels[::-1, :, :]
    return flipped
    
def blender_to_byte(bpy_img) -> bytes:
    '''Converts a Blender image to a byte array with shape (height, width, channels) as a uint8 array with values in the range [0, 255].'''
    flipped = (np.clip(blender_to_numpy(bpy_img) * 255, 0, 255).astype(np.uint8))
    return flipped.tobytes()


def blender_to_pil(bpy_img) -> Image.Image:
    '''Converts a Blender image to a PIL Image object.'''
    return Image.frombytes("RGBA", (bpy_img.size[0], bpy_img.size[1]), blender_to_byte(bpy_img))


from sourcepp import vtfpp
def create_vtf(image:Image.Image, output_path:str|Path, options:vtfpp.VTF.CreationOptions = None, flags:list(vtfpp.VTF.Flags) = None):

    if not image: return None
    if not output_path: return None

    if not options:
        options = vtfpp.VTF.CreationOptions()
        options.output_format = vtfpp.ImageFormat.DXT5
        options.version = 2

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(exist_ok=True, parents=True)

    # Just to make sure
    options.compute_mips = True
    options.compute_thumbnail = True
    options.compute_reflectivity = True

    vtf = vtfpp.VTF.create(
        image_data=image.tobytes(), # Convert to RGBA just in case
        format=vtfpp.ImageFormat.RGBA8888,
        width=image.width,
        height=image.height,
        creation_options=options
    )

    if flags:
        for flag in flags:
            vtf.add_flags(flag.value)

    err = vtf.bake_to_file(vtf_path=output_path)

    if output_path.exists():
        print(f'VTF Created {str(output_path)} {err}')
        return output_path
    else:
        print(err)



def probe_bsdf(material, probe_node:BlenderInputNodes):

    if material and material.node_tree:
        principled = next(
            (n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'),
            None
        )

        if principled:
            base_color_input = principled.inputs[probe_node.value]

            #for x in principled.inputs:
            #    print(x)

            if base_color_input.is_linked:
                from_node = base_color_input.links[0].from_node

                if from_node.type == 'TEX_IMAGE':
                    image = from_node.image
                    if image:
                        return image
    return None


def get_all_mats(collection) -> set:
    materials = set()
    for obj in collection.all_objects:
        if hasattr(obj.data, "materials"):
            for mat in obj.data.materials:
                if mat is not None:
                    materials.add(mat)
    return materials

def get_all_coll(model) -> set:

    colls = set()

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

def mats_from_model(model) -> set:

    materials = set()

    colls = get_all_coll(model)

    for collection in colls:

        mats = get_all_mats(collection)
        if mats:
            for mat in mats:
                materials.add(mat)

    return materials