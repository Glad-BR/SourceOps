import bpy
import cv2
import numpy as np

from rich import print
from pathlib import Path
from enum import Enum
from PIL import Image
from sourcepp import vtfpp

from ..types.model_export.material_export.types import PIL_VTF_map

class BlenderInputNodes(Enum):
    BaseColor = 'Base Color'
    Diffuse = BaseColor #Alias
    Roughness = 'Roughness'
    Metallic = 'Metallic'
    Normal = 'Normal'
    Emissive = 'Emission Color'


def save_blender_img(image: bpy.types.Image, save_path: str|Path, name_override: str|None = None) -> Path|None:
    name = f'{image.name if not name_override else name_override}.{str(image.file_format).lower()}' # i cry
    file = (Path(save_path) / name)
    image.save(filepath=str(file))

    if file.exists():
        return file
    else:
        print(f'Failed to save {file}')
        print(image)
        return None


def blender_to_numpy(bpy_img: bpy.types.Image) -> np.ndarray:
    '''Converts a Blender image to a numpy array with shape (height, width, channels) as a float32 array with values in the range [0, 1].'''
    width = bpy_img.size[0]
    height = bpy_img.size[1]
    channels = 4
    
    float_pixels = np.empty(width * height * channels, dtype=np.float32)
    bpy_img.pixels.foreach_get(float_pixels)

    float_pixels = float_pixels.reshape((height, width, channels))
    flipped = float_pixels[::-1, :, :]
    return flipped.astype(dtype=np.float32)
    
def blender_to_byte(bpy_img: bpy.types.Image) -> bytes:
    '''Converts a Blender image to a byte array with shape (height, width, channels) as a uint8 array with values in the range [0, 255].'''
    flipped = (np.clip(blender_to_numpy(bpy_img) * 255, 0, 255).astype(np.uint8))
    return flipped.tobytes()

def blender_to_pil(bpy_img: bpy.types.Image) -> Image.Image:
    '''Converts a Blender image to a PIL Image object.'''
    return Image.frombytes("RGBA", (bpy_img.size[0], bpy_img.size[1]), blender_to_byte(bpy_img))


def np_grayscale(image: np.ndarray) -> np.ndarray:
    if image is not None:
        gray = np.mean(image[:, :, :3], axis=2).astype(np.float32)
        return gray
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




def create_vtf(image: Image.Image|np.ndarray, output_path: str|Path, options: vtfpp.VTF.CreationOptions|None = None, flags: list[vtfpp.VTF.Flags]|None = None):
    if image is None: return None
    if not output_path: return None

    if not options:
        options = vtfpp.VTF.CreationOptions()
        options.output_format = vtfpp.ImageFormat.DXT5
        options.version = 2

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(exist_ok=True, parents=True)

    # Just to make sure
    options.compute_mips         = True if not options.compute_mips         else options.compute_mips
    options.compute_thumbnail    = True if not options.compute_thumbnail    else options.compute_thumbnail
    options.compute_reflectivity = True if not options.compute_reflectivity else options.compute_reflectivity

    if isinstance(image, Image.Image):
        DATA = image.tobytes()
        WIDTH = image.width
        HEIGHT = image.height
        FORMAT = PIL_VTF_map[image.mode].value
    
    elif isinstance(image, np.ndarray):
        image = np.clip(image * 255.0, 0, 255).astype(np.uint8)

        if image.ndim == 2:
            HEIGHT, WIDTH = image.shape
            DATA = image.tobytes()
            FORMAT = vtfpp.ImageFormat.I8
        elif image.ndim == 3:
            HEIGHT, WIDTH, CHANNELS = image.shape
            if CHANNELS == 1:
                DATA = image.tobytes()
                FORMAT = vtfpp.ImageFormat.I8
            elif CHANNELS == 2:
                DATA = image.tobytes()
                FORMAT = vtfpp.ImageFormat.IA88
            elif CHANNELS == 3:
                DATA = image.tobytes()
                FORMAT = vtfpp.ImageFormat.RGB888
            elif CHANNELS == 4:
                DATA = image.tobytes()
                FORMAT = vtfpp.ImageFormat.RGBA8888
            else:
                raise ValueError(f"Unsupported number of channels: {CHANNELS}")
        else:
            raise ValueError(f"Unsupported number of dimensions: {image.ndim}")


    vtf = vtfpp.VTF.create(
        image_data=DATA,
        format=FORMAT,
        width=WIDTH,
        height=HEIGHT,
        creation_options=options
    )

    if flags:
        for flag in flags:
            vtf.add_flags(flag.value)

    err = vtf.bake_to_file(vtf_path=output_path)

    if output_path.exists():
        print('VTF Created', output_path, err)
        return output_path
    else:
        print(err)


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