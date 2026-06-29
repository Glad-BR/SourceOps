import bpy
import time
import zlib
import hashlib

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from ...utils import common, mats
from PIL import Image, ImageChops
from sourcepp import vtfpp
Flags = vtfpp.VTF.Flags
ImageFormat = vtfpp.ImageFormat

from .model import Model
from ...props.material_props import SOURCEOPS_AllMaterialsProps


class ExporterBasic:
    def __init__(self, model:Model, pil_images):
        self.model = model
        self.images = pil_images

    def basetexture(self, mat:SOURCEOPS_AllMaterialsProps) -> Image.Image:
        if mat.tex_ao:
            return mats.multiply(self.images[mat.tex_ao], self.images[mat.tex_diffuse])
        else:
            return self.images[mat.tex_diffuse]

    def normal(self, mat:SOURCEOPS_AllMaterialsProps) -> Image.Image:
        if mat.tex_normal:
            return self.images[mat.tex_normal]
        else:
            return None

    def emissive(self, mat:SOURCEOPS_AllMaterialsProps) -> Image.Image:
        if mat.tex_emissive:
            return self.images[mat.tex_emissive]
        else:
            return None

    def phong(self, mat:SOURCEOPS_AllMaterialsProps) -> Image.Image:
        return None



@dataclass
class ExportTexture:
    image: Image.Image
    image_hash: str
    image_name: str

    output_path: Path = None

    format: ImageFormat = None
    flags: tuple[Flags, ...] = ()
    invert_green: bool = False

@dataclass
class ExportMaterial:
    source: SOURCEOPS_AllMaterialsProps
    basetexture: ExportTexture = None
    normal: ExportTexture = None
    emissive: ExportTexture = None
    phong: ExportTexture = None


def _hashimg(image:Image.Image):
    if image:
        return hashlib.sha1(image.tobytes()).hexdigest()
    else:
        return None


def export_materials(self:Model):
    start = time.perf_counter()

    t = bpy.context.preferences.filepaths.temporary_directory
    tmp = Path(t if t else bpy.app.tempdir)

    error = []

    relative_path = Path(self.material_folder_items[0].name)

    mat_folder = Path(self.materials / relative_path)
    tex_folder = mat_folder / Path(self.name).name

    tex_folder.mkdir(parents=True, exist_ok=True)


    pil_images = {}

    textures = {}
    materials = []

    # Build unique texture list
    tex_search_list = (
        'tex_ao',
        'tex_diffuse',
        'tex_roughness',
        'tex_metallic',
        'tex_normal',
        'tex_emissive'
    )

    for mat in self.materials_items:
        for name in tex_search_list:
            image = mat[name]

            if image and image not in pil_images:
                print(f'Adding New Image to list: [{image}]')
                pil_images[image] = mats.blender_to_pil(image)




    opts = vtfpp.VTF.CreationOptions()
    opts.version = self.vtf_version



    def register_texture(image, image_name, format, flags=None, invert_green=False):

        if image is None: return None
        if flags is None: flags = ()

        image_hash = _hashimg(image)

        key = (
            image_hash,
            format,
            flags,
            invert_green,
        )
        tex = textures.get(key)

        if tex is None:

            tex = ExportTexture(
                image=image,
                image_hash=image_hash,
                image_name=image_name,
                output_path=None,
                format=format,
                flags=flags,
                invert_green=invert_green,
            )

            textures[key] = tex

        return tex


    def _exporter(mat:SOURCEOPS_AllMaterialsProps):
        if mat.convert_method == 'simple':
            return ExporterBasic(model=self, pil_images=pil_images)
        else:
            return ExporterBasic(model=self, pil_images=pil_images)


    def convert_textures(mat:SOURCEOPS_AllMaterialsProps):
        if not mat.tex_diffuse: return "!!!!!! Base Color Not Found"
        
        flags = tuple()
        exporter = _exporter(mat)
        export = ExportMaterial(source=mat)

        export.basetexture = register_texture(
            image=exporter.basetexture(mat),
            image_name='basetexture',
            format=ImageFormat[mat.basetexture_format],
            flags=flags,
        )
        export.normal = register_texture(
            image=exporter.normal(mat),
            image_name='normal',
            format=ImageFormat[mat.normal_format],
            flags=flags,
        )
        export.emissive = register_texture(
            image=exporter.emissive(mat),
            image_name='emissive',
            format=ImageFormat[mat.emissive_format],
            flags=flags,
        )
        export.phong = register_texture(
            image=exporter.phong(mat),
            image_name='phong',
            format=ImageFormat[mat.phong_format],
            flags=flags,
        )

        materials.append(export)


    # Export textures
    def export_texture(tex: ExportTexture):

        opts = vtfpp.VTF.CreationOptions()

        opts.version = self.vtf_version
        opts.output_format = tex.format
        opts.invert_green_channel = tex.invert_green

        mats.create_vtf(
            image=tex.image,
            output_path=tex.output_path,
            options=opts,
            flags=tex.flags,
        )



    with ThreadPoolExecutor() as executor:
        list(executor.map(convert_textures, self.materials_items))


    # Assign filenames
    for tex in textures.values():
        tex.output_path = tex_folder / f"{bpy.path.clean_name(tex.image_name)}_{tex.image_hash[:8]}.vtf"
    

    with ThreadPoolExecutor() as executor:
        list(executor.map(export_texture, textures.values()))

    print(f"Converted {len(textures)} textures in {time.perf_counter()-start:.3f}s")




    # Write VMTs

    for mat in materials:
        mat:ExportMaterial # Me like type

        blender_mat = mat.source

        outpath = mat_folder / blender_mat.name

        with open(f"{outpath}.vmt", "w") as vmt:

            vmt.write(f"{blender_mat.type}\n")
            vmt.write("{\n")

            rel = mat.basetexture.output_path.relative_to(self.materials).with_suffix("").as_posix()
            vmt.write(f'\t$basetexture "{rel}"\n')

            if mat.normal:
                rel = mat.normal.output_path.relative_to(self.materials).with_suffix("").as_posix()

                if (blender_mat.emissivetype == 'COLOR_DETAIL') and (mat.emissive) and (not mat.phong):
                    vmt.write(f'\t$normal "{rel}"\n') # Detail only works with $normal but it breaks phong for some reason
                else:
                    vmt.write(f'\t$bumpmap "{rel}"\n')

            if blender_mat.surfaceprop:
                vmt.write('\n')
                vmt.write(f'\t$surfaceprop "{str(blender_mat.surfaceprop)}"\n')

            if mat.emissive:
                rel = mat.emissive.output_path.relative_to(self.materials).with_suffix("").as_posix()
                vmt.write('\n')

                if blender_mat.emissivetype == 'COLOR_DETAIL' and not mat.phong:
                    vmt.write(f'\t$detail {rel}\n')
                    vmt.write(f'\t$detailscale 1\n')
                    vmt.write(f'\t$detailblendmode 5\n')
                elif blender_mat.emissivetype == 'MASK':
                    vmt.write(f'\t$selfillum 1\n')
                    vmt.write(f'\t$selfillummask {rel}\n')
                else: #Fallback to emissiveBlend
                    vmt.write(f'\t$emissiveBlendEnabled 1\n')
                    vmt.write(f'\t$emissiveBlendStrength 1\n')
                    vmt.write(f'\t$emissiveBlendBaseTexture "{rel}"\n')
                    vmt.write(f'\t$emissiveBlendTexture "vgui/white"\n')
                    vmt.write(f'\t$emissiveBlendFlowTexture "vgui/white"\n')
                    vmt.write(f'\t$emissiveBlendTint "[ 1 1 1 ]"\n')
                    vmt.write(f'\t$emissiveBlendScrollVector "[ 0 0 ]"\n')

            vmt.write("}")

    return error if error else None