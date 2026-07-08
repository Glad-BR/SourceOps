import bpy
import time
import hashlib
import traceback

import numpy as np

from rich import print
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from sourcepp import vtfpp
Flags = vtfpp.VTF.Flags
ImageFormat = vtfpp.ImageFormat

from . import vtf
from .types import *
from .exporters import Basic, fakepbr1, fakepbr2, ExoPBR1
from ..model import Model
from ....utils import mats
from ....props.material_props import SOURCEOPS_AllMaterialsProps



class ExporterMain:

    def __init__(self, model:Model):

        self.model = model

        self.images_arrs = {}
        self.textures = {}

        self.materials = []
        self.errors = []

        assert self.model.material_folder_items is not None

        self.relative_path = Path(self.model.material_folder_items[0].name)
        self.mat_folder = Path(self.model.materials / self.relative_path)
        self.tex_folder = self.mat_folder / Path(self.model.name).name

        self.tex_folder.mkdir(parents=True, exist_ok=True)

        self.tex_search_list = (
            'tex_ao',
            'tex_diffuse',
            'tex_roughness',
            'tex_metallic',
            'tex_normal',
            'tex_emissive',
        )


    def _hashimg(self, image:np.ndarray):
        if image is not None:
            return hashlib.sha1(image.tobytes()).hexdigest()
        else:
            return None


    def _exporter(self, mat:SOURCEOPS_AllMaterialsProps):
        if (mat.type == 'VertexLitGeneric') or (mat.type == 'UnlitGeneric'):
            if mat.convert_method == 'simple':
                return Basic(model=self.model, AllMaterialsProps=mat,images_arrs=self.images_arrs)
            elif mat.convert_method == 'fakepbr1':
                return fakepbr1(model=self.model, AllMaterialsProps=mat,images_arrs=self.images_arrs)
            elif mat.convert_method == 'fakepbr2':
                return fakepbr2(model=self.model, AllMaterialsProps=mat,images_arrs=self.images_arrs)
        elif mat.type == 'ExoPBR':
            return ExoPBR1(model=self.model, AllMaterialsProps=mat,images_arrs=self.images_arrs)
    

    def _build_unique_tex(self):
        print(f"Building unique texture list for {len(self.model.materials_items)} materials")
        for mat in self.model.materials_items:
            for name in self.tex_search_list:
                image = getattr(mat, name, None)
                
                if image and image not in self.images_arrs:
                    print(f'Adding New Image to list: [{image}]')
                    self.images_arrs[image] = mats.blender_to_numpy(image)
    

    def _register_texture(self, image, image_name, format, flags=None, invert_green=False):
        if image is None: return None
        if flags is None: flags = ()

        image_hash = self._hashimg(image)

        key = (
            image_hash,
            format,
            flags,
            invert_green,
        )
        tex = self.textures.get(key)

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
            self.textures[key] = tex
        return tex


    def _mk_vtf(self, tex: ExportTexture):
        print(f'Submitting VTF create job {tex.image.shape} {tex.image_name} {tex.image_hash[:8]} -> {tex.output_path.relative_to(self.model.materials)}')
        opts = vtfpp.VTF.CreationOptions()
        opts.version = self.model.vtf_version
        opts.output_format = tex.format
        opts.invert_green_channel = tex.invert_green
        vtf.create_vtf(
            image=tex.image,
            output_path=tex.output_path,
            options=opts,
            flags=tex.flags,
            exists_ok=False,
        )


    def _convert_textures(self, mat:SOURCEOPS_AllMaterialsProps):
        if not mat.tex_diffuse: return "!!!!!! Base Color Not Found"
        
        exporter = self._exporter(mat)
        print(f'Using Exporter: {exporter}')
        export = ExportMaterial(source=mat)

        flags = tuple()

        # Use Phong thingy for ExoPBR ARM texture
        if mat.type == 'ExoPBR':
            phong_format = ImageFormat.BGR888
        elif mat.fakepbr1_use_albedotint:
            phong_format = ImageFormat.BGR888
        else:
            phong_format = ImageFormat.I8
        

        if mat.emissivetype in ('COLOR', 'MASK2'):
            emissive_format = ImageFormat[mat.emissive_format]
        elif mat.emissivetype == 'MASK':
            emissive_format = ImageFormat.I8

        export.normal = self._register_texture(
            image=exporter.normal(),
            image_name='normal',
            format=ImageFormat[mat.normal_format],
            flags=flags,
        )
        export.phong = self._register_texture(
            image=exporter.phong(),
            image_name='phong',
            format=phong_format,
            flags=flags,
        )
        export.envmapmask = self._register_texture(
            image=exporter.envmapmask(),
            image_name='envmapmask',
            format=ImageFormat.IA88,
            flags=flags,
        )
        export.basetexture = self._register_texture(
            image=exporter.basetexture(),
            image_name='basetexture',
            format=ImageFormat[mat.basetexture_format],
            flags=flags,
        )
        export.emissive = self._register_texture(
            image=exporter.emissive(),
            image_name='emissive',
            format=emissive_format,
            flags=flags,
        )

        self.materials.append(export)

    #-------------------------------------------------------------------------------------------

    def export(self):
        start = time.perf_counter()
        print(f"Exporting Material {self.model.name}")

        #Step 1
        self._build_unique_tex()

        # Step 2: Convert textures for each material
        print(f"Converting textures for {len(self.model.materials_items)} materials")
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self._convert_textures, mat) for mat in self.model.materials_items]
            for future in as_completed(futures):
                try:
                    res = future.result()
                    if isinstance(res, str):
                        self.errors.append(res)
                        print(f"Texture conversion returned error: {res}")
                except Exception as exc:
                    self.errors.append(exc)
                    print(f"Thread failed with error: {exc}")
                    traceback.print_exception(type(exc), exc, exc.__traceback__)
                
        # Assign filenames
        for tex in self.textures.values():
            tex: ExportTexture
            tex.output_path = self.tex_folder / f"{bpy.path.clean_name(tex.image_name)}_{tex.image_hash[:8]}.vtf"

        # Step 3: create textures and save as vtf
        print(f"Exporting {len(self.textures.values())} VTF textures to {self.tex_folder}")


        for tex in self.textures.values():
            self._mk_vtf(tex)


        print(f"Converted {len(self.textures)} textures in {time.perf_counter()-start:.3f}s")

        # Write VMTs
        for mat in self.materials:
            mat:ExportMaterial # Me like type
            blender_mat = mat.source
            exporter = self._exporter(blender_mat)
            exporter.vmt(export_mat=mat, outpath=(self.mat_folder / blender_mat.name))

        return self.errors if self.errors else None




def export_materials(model:Model):
    e = ExporterMain(model=model)
    return e.export()
