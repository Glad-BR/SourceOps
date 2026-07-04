import bpy
import time
import hashlib

from rich import print
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from sourcepp import vtfpp
Flags = vtfpp.VTF.Flags
ImageFormat = vtfpp.ImageFormat

from .types import *
from .exporters import Basic, fakepbr1
from ..model import Model
from ....utils import mats
from ....props.material_props import SOURCEOPS_AllMaterialsProps


def _hashimg(image:np.ndarray):
    if image is not None:
        return hashlib.sha1(image.tobytes()).hexdigest()
    else:
        return None


def export_materials(self:Model, vmt_only:bool=False, tex_only:bool=False):
    start = time.perf_counter()

    print(f"Exporting Material {self.name}")

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
        'tex_emissive',
    )
    
    print(f"Building unique texture list for {len(self.materials_items)} materials")
    for mat in self.materials_items:
        mat:SOURCEOPS_AllMaterialsProps

        for name in tex_search_list:
            image = mat[name]

            if image and image not in pil_images:
                print(f'Adding New Image to list: [{image}]')
                pil_images[image] = mats.blender_to_numpy(image)


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
            return Basic(model=self, AllMaterialsProps=mat,pil_images=pil_images)
        elif mat.convert_method == 'fakepbr1':
            return fakepbr1(model=self, AllMaterialsProps=mat,pil_images=pil_images)


    def convert_textures(mat:SOURCEOPS_AllMaterialsProps):
        if not mat.tex_diffuse: return "!!!!!! Base Color Not Found"
        
        exporter = _exporter(mat)
        print(f'Using Exporter: {exporter}')
        export = ExportMaterial(source=mat)


        flags = tuple(Flags.V0_NORMAL)
        export.normal = register_texture(
            image=exporter.normal(),
            image_name='normal',
            format=ImageFormat[mat.normal_format],
            flags=flags,
        )
        flags = tuple()
        export.phong = register_texture(
            image=exporter.phong(),
            image_name='phong',
            format=ImageFormat.I8,
            flags=flags,
        )
        flags = tuple()
        export.envmapmask = register_texture(
            image=exporter.envmapmask(),
            image_name='envmapmask',
            format=ImageFormat.I8,
            flags=flags,
        )

        if int(self.vtf_version) >= 5:
            flags = tuple(Flags.V5_SRGB)
        elif int(self.vtf_version) >= 4:
            flags = tuple(Flags.V4_SRGB)
        else:
            flags = tuple()

        export.basetexture = register_texture(
            image=exporter.basetexture(),
            image_name='basetexture',
            format=ImageFormat[mat.basetexture_format],
            flags=flags,
        )
        export.emissive = register_texture(
            image=exporter.emissive(),
            image_name='emissive',
            format=ImageFormat[mat.emissive_format] if mat.emissivetype == 'COLOR' else ImageFormat.I8,
            flags=flags,
        )

        materials.append(export)


    # Export textures
    def export_texture(tex: ExportTexture):

        opts = vtfpp.VTF.CreationOptions()

        opts.version = self.vtf_version
        opts.output_format = tex.format
        opts.invert_green_channel = tex.invert_green

        print(f'Submitting VTF create job {tex.image.shape} {tex.image_name} {tex.image_hash[:8]} -> {tex.output_path.relative_to(self.materials)}')

        mats.create_vtf(
            image=tex.image,
            output_path=tex.output_path,
            options=opts,
            flags=tex.flags,
        )

    # Step 2: Convert textures for each material
    print(f"Converting textures for {len(self.materials_items)} materials")
    with ThreadPoolExecutor() as executor:
        #executor.map(convert_textures, self.materials_items)
        futures = [executor.submit(convert_textures, mat) for mat in self.materials_items]
        wait(futures) 
        for future in futures: 
            if future.exception(): print(f"Thread failed with error: {future.exception()}")

    #for mat in self.materials_items: #Debug
    #    convert_textures(mat)



    # Assign filenames
    for tex in textures.values():
        tex: ExportTexture
        tex.output_path = tex_folder / f"{bpy.path.clean_name(tex.image_name)}_{tex.image_hash[:8]}.vtf"
    

    if not vmt_only:
        # Step 3: create textures and save as vtf
        print(f"Exporting {len(textures.values())} VTF textures to {tex_folder}")
        with ThreadPoolExecutor() as executor: # Very fun
            #executor.map(export_texture, textures.values())
            futures = [executor.submit(export_texture, tex) for tex in textures.values()]
            wait(futures) 
            for future in futures:
                if future.exception(): print(f"Thread failed with error: {future.exception()}")


    print(f"Converted {len(textures)} textures in {time.perf_counter()-start:.3f}s")

    if not tex_only:
        # Write VMTs
        for mat in materials:
            mat:ExportMaterial # Me like type
            blender_mat = mat.source
            exporter = _exporter(blender_mat)
            exporter.vmt(export_mat=mat, outpath=(mat_folder / blender_mat.name))

        return error if error else None