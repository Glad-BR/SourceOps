import bpy

from pathlib import Path
from enum import Enum

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


def probe_bsdf(material, probe_node:BlenderInputNodes = BlenderInputNodes.BaseColor):

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


def get_mats_from_model(model) -> set:

    materials = set()

    colls = get_all_coll(model)

    for collection in colls:

        mats = get_all_mats(collection)
        if mats:
            for mat in mats:
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

