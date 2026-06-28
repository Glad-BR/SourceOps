import bpy

from ...utils import common, mats


from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import time



from sourcepp import vtfpp
Flags = vtfpp.VTF.Flags
ImageFormat = vtfpp.ImageFormat


from PIL import Image, ImageChops

from .model import Model

import hashlib



from ...props.material_props import SOURCEOPS_AllMaterialsProps


class ExporterBasic:


    def basecolor(self, mat:SOURCEOPS_AllMaterialsProps):



        mat.



        None


    None




def export_materials(self:Model):

    t = bpy.context.preferences.filepaths.temporary_directory
    tmp = Path(t if t else bpy.app.tempdir)

    error = []

    relative_path = Path(self.material_folder_items[0].name)

    mat_folder = Path(self.materials / relative_path)
    tex_folder = mat_folder / Path(self.name).name

    tex_folder.mkdir(parents=True, exist_ok=True)

    # Build unique texture list
    tex_search_list = (
        'tex_ao',
        'tex_diffuse',
        'tex_roughness',
        'tex_metallic',
        'tex_normal',
        'tex_emissive'
    )
    pil_images = {}

    for mat in self.materials_items:
        for name in tex_search_list:
            image = mat[name]

            if image and image not in pil_images:
                pil_images[image] = mats.blender_to_pil(image)




    # Thingy
    for mat in self.materials_items:

        if not mat.tex_diffuse:
            return "BaseColor Not Found"
        
        
        pil_diffuse = pil_images[mat.tex_diffuse]

        if mat.tex_ao:
            pil_ao = pil_images[mat.tex_ao]
            pil_diffuse = mats.multiply(pil_diffuse, pil_ao)

        
        

        print(mat)




        opts = vtfpp.VTF.CreationOptions()
        opts.version = self.vtf_version
        opts.output_format = ImageFormat[mat.basetexture_format]
        

        #mats.create_vtf(
        #    image=pil_diffuse,
        #    output_path=tex_folder / 'basecolor.vtf',
        #    options=opts
        #)


        




















@dataclass
class ExportTexture:
    image: bpy.types.Image

    image: Image.Image | None = None

    output_path: Path | None = None

    format: ImageFormat = None
    flags: tuple[Flags, ...] = ()

    invert_green: bool = False


@dataclass
class ExportMaterial:
    source: object

    diffuse: ExportTexture = None
    normal: ExportTexture = None
    emissive: ExportTexture = None
    phong: ExportTexture = None


def _export_materials(self:Model):
    t = bpy.context.preferences.filepaths.temporary_directory
    tmp = Path(t if t else bpy.app.tempdir)

    error = []

    relative_path = Path(self.material_folder_items[0].name)

    mat_folder = Path(self.materials / relative_path)
    tex_folder = mat_folder / Path(self.name).name

    tex_folder.mkdir(parents=True, exist_ok=True)

    # Build unique texture list

    textures = {}
    materials = []

    def get_texture(image, format, flags=None, invert_green=False):

        if image is None:
            return None

        if flags is None:
            flags = ()

        key = (
            image,
            format,
            tuple(sorted(flags)),
            invert_green,
        )

        tex = textures.get(key)

        if tex is None:

            tex = ExportTexture(
                image=image,
                output_path=None,
                format=format,
                flags=list(flags),
                invert_green=invert_green,
            )

            textures[key] = tex

        return tex
    
    


    for mat in self.materials_items:

        if not mat.tex_diffuse:
            return "BaseColor Not Found"

        export = ExportMaterial(source=mat)

        export.diffuse = get_texture(
            mat.tex_diffuse,
            ImageFormat[mat.basetexture_format],
        )

        export.normal = get_texture(
            mat.tex_normal,
            ImageFormat[mat.normal_format],
            flags=(Flags.V0_NORMAL,),
            invert_green=(mat.normaltype == 'OPENGL'),
        )

        export.emissive = get_texture(
            mat.tex_emissive,
            ImageFormat[mat.normal_format],
        )

        materials.append(export)

    # Assign filenames

    for tex in textures.values():

        name = bpy.path.clean_name(tex.image.name)
        tex.output_path = tex_folder / f'{name}.vtf'

    # Export textures




    def export_texture(tex: ExportTexture):

        opts = vtfpp.VTF.CreationOptions()

        opts.version = self.vtf_version
        opts.output_format = tex.format
        opts.invert_green_channel = tex.invert_green

        image = mats.blender_to_pil(tex.image)

        mats.create_vtf(
            image=tex.pil_image,
            output_path=tex.output_path,
            options=opts,
            flags=tex.flags,
        )

    for tex in textures.values():
        tex.pil_image = mats.blender_to_pil(tex.image)


    start = time.perf_counter()

    with ThreadPoolExecutor() as executor:
        list(executor.map(export_texture, textures.values()))

    print(f"Converted {len(textures)} textures in {time.perf_counter()-start:.3f}s")






    # Write VMTs

    for mat in materials:

        blender_mat = mat.source

        outpath = mat_folder / blender_mat.name

        with open(f"{outpath}.vmt", "w") as vmt:

            vmt.write(f"{blender_mat.type}\n")
            vmt.write("{\n")

            rel = mat.diffuse.output_path.relative_to(self.materials)

            vmt.write(f'\t$basetexture "{rel.as_posix()}"\n')

            if mat.normal:
                rel = mat.normal.output_path.relative_to(self.materials)
                vmt.write(f'\t$bumpmap "{rel.as_posix()}"\n')

            if mat.emissive:
                rel = mat.emissive.output_path.relative_to(self.materials)
                vmt.write('\n')
                vmt.write(f'\t$emissiveBlendEnabled 1\n')
                vmt.write(f'\t$emissiveBlendStrength 1\n')
                vmt.write(f'\t$emissiveBlendBaseTexture "{rel.as_posix()}"\n')
                vmt.write(f'\t$emissiveBlendTexture "vgui/white"\n')
                vmt.write(f'\t$emissiveBlendFlowTexture "vgui/white"\n')
                vmt.write(f'\t$emissiveBlendTint "[ 1 1 1 ]"\n')
                vmt.write(f'\t$emissiveBlendScrollVector "[ 0 0 ]"\n')

            vmt.write("}")

    return error if error else None
