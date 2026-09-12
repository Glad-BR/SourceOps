import bpy
import time
import hashlib
import multiprocessing
import threading
import numpy as np

from concurrent.futures import as_completed
from pathlib import Path
from sourcepp import vtfpp
from . import vtf
Flags = vtfpp.VTF.Flags
ImageFormat = vtfpp.ImageFormat

from . import vtf
from .types import *
from .exporters import *
from ..model_export.model import Model
from ...utils import mats
from ...props.material_props import SOURCEOPS_AllMaterialsProps
from ...utils.logger import log



class ExporterMain:

    def __init__(self, model:Model):

        self.model = model
        self.executor = model.executor

        self.images_arrs = {}
        self.textures = {}

        self.materials = []
        self.errors = []

        self._lock = threading.Lock()

        if model.prefs.threading_mat_export:
            self._max_workers = multiprocessing.cpu_count()-1
        else:
            self._max_workers = 1

        assert self.model.material_folder_items is not None

        self.relative_path = Path(self.model.material_folder_items[0].name)
        self.mat_folder = Path(self.model.materials / self.relative_path)
        self.tex_folder = self.mat_folder / Path(self.model.name).name

        self.mat_folder.mkdir(parents=True, exist_ok=True)

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
            #return test1(model=self.model, AllMaterialsProps=mat,images_arrs=self.images_arrs)
            if mat.convert_method == 'simple':
                return Basic(model=self.model, AllMaterialsProps=mat,images_arrs=self.images_arrs)
            elif mat.convert_method == 'fakepbr1':
                return fakepbr1(model=self.model, AllMaterialsProps=mat,images_arrs=self.images_arrs)
            elif mat.convert_method == 'fakepbr2':
                return fakepbr2(model=self.model, AllMaterialsProps=mat,images_arrs=self.images_arrs)
        elif mat.type == 'ExoPBR':
            return ExoPBR1(model=self.model, AllMaterialsProps=mat,images_arrs=self.images_arrs)
    

    def _build_unique_tex(self):
        log.debug(f"Building unique texture list for {len(self.model.materials_items)} materials")
        start_t = time.perf_counter()
        for mat in self.model.materials_items:
            if mat.export:
                for name in self.tex_search_list:
                    image = getattr(mat, name, None)
                    
                    if image and image not in self.images_arrs:
                        start = time.perf_counter()
                        self.images_arrs[image] = mats.blender_to_numpy(image)
                        log.debug(f'Loaded Blender Image: [{image}] Took: {time.perf_counter()-start:.16f}')
        
        log.debug(f'Finish Build unique texture list Took: {time.perf_counter()-start_t:.16f}')
    

    def _register_texture(self, image, image_name, format, flags=None, invert_green=False, parent_name=None):
        if image is None: return None
        if flags is None: flags = ()

        image_hash = self._hashimg(image)

        key = (
            image_hash,
            format,
            flags,
            invert_green,
        )
        with self._lock:
            tex = self.textures.get(key)

            if tex is None:
                tex = ExportTexture(
                    image=image,
                    image_hash=image_hash,
                    image_name=image_name,
                    parent_name=parent_name,
                    output_path=None,
                    format=format,
                    flags=flags,
                    invert_green=invert_green,
                )
                self.textures[key] = tex
            elif (parent_name, image_name) < (tex.parent_name, tex.image_name):
                tex.parent_name = parent_name
                tex.image_name = image_name
            return tex


    def _mk_vtf(self, tex: ExportTexture):
        log.info(f'Submitting VTF create job {tex.image.shape} {tex.image_name} {tex.image_hash[:8]} -> {tex.output_path.relative_to(self.model.materials)}')
        opts = vtfpp.VTF.CreationOptions()
        opts.version = self.model.vtf_version
        opts.output_format = tex.format
        opts.invert_green_channel = tex.invert_green
        vtf.create_vtf( #Pain
            image=tex.image,
            output_path=tex.output_path,
            options=opts,
            flags=tex.flags,
            exists_ok=False,
        )


    def _convert_textures(self, mat:SOURCEOPS_AllMaterialsProps):
        if not mat.tex_diffuse: return "!!!!!! Base Color Not Found"
        
        exporter = self._exporter(mat)
        log.debug(f'Using Exporter: {exporter}')
        export = ExportMaterial(source=mat)

        flags = tuple()

        # Use Phong thingy for ExoPBR ARM texture
        if mat.type == 'ExoPBR':
            phong_format = ImageFormat.BGR888
        elif mat.fakepbr1_use_albedotint:
            phong_format = ImageFormat.BGR888
        else:
            phong_format = ImageFormat.I8
        

        if mat.emissivetype in ColorMasks:
            emissive_format = ImageFormat[mat.emissive_format]
        elif mat.emissivetype in GrayMasks:
            emissive_format = ImageFormat.I8

        export.normal = self._register_texture(
            image=exporter.normal(),
            image_name='normal',
            format=ImageFormat[mat.normal_format],
            flags=tuple(Flags.V0_NORMAL),
            parent_name=mat.name
        )
        export.phong = self._register_texture(
            image=exporter.phong(),
            image_name='phong',
            format=phong_format,
            flags=flags,
            parent_name=mat.name
        )
        #export.envmapmask = self._register_texture(
        #    image=exporter.envmapmask(),
        #    image_name='envmapmask',
        #    format=ImageFormat.IA88,
        #    flags=flags,
        #    parent_name=mat.name
        #)
        export.basetexture = self._register_texture(
            image=exporter.basetexture(),
            image_name='basetexture',
            format=ImageFormat[mat.basetexture_format],
            flags=flags,
            parent_name=mat.name
        )
        export.emissive = self._register_texture(
            image=exporter.emissive(),
            image_name='emissive',
            format=emissive_format,
            flags=flags,
            parent_name=mat.name
        )

        return export

    #-------------------------------------------------------------------------------------------


    def export(self):
        start = time.perf_counter()
        log.info(f"Exporting Material {self.model.name}")

        self._build_unique_tex()

        # Step 2: Convert textures
        log.info(f"Converting textures for {len(self.model.materials_items)} materials")
        futures = [self.executor.submit(self._convert_textures, mat) for mat in self.model.materials_items if mat.export]
        results = {}
        for index, future in enumerate(futures):
            try:
                res = future.result()
                if isinstance(res, str):
                    self.errors.append(res)
                    log.error(f"Texture conversion returned error: {res}")
                elif res is not None:
                    results[index] = res
            except Exception as exc:
                self.errors.append(exc)
                log.exception(f"Thread failed with error: {exc}")

        self.materials = [results[index] for index in sorted(results)]
        

        # Assign filenames
        for tex in self.textures.values():
            tex: ExportTexture
            tex.output_path = self.mat_folder / bpy.path.clean_name(tex.parent_name) / f"{bpy.path.clean_name(tex.image_name)}.vtf"


        # Write VMTs
        for mat in self.materials:
            mat:ExportMaterial # Me like type
            blender_mat = mat.source
            exporter = self._exporter(blender_mat)
            outpath = self.mat_folder / blender_mat.name
            log.info(f'Writing VMT [{blender_mat.name}]')
            exporter.vmt(mat, outpath)


        self.images_arrs.clear()
        

        # Step 3: Save VTF
        log.info(f"Exporting {len(self.textures.values())} VTF textures to {self.tex_folder}")

        futures = {self.executor.submit(self._mk_vtf, tex): tex for tex in self.textures.values()}
        for future in as_completed(futures):
            tex_obj = futures[future]
            try:
                res = future.result()
                if isinstance(res, str):
                    self.errors.append(res)
                    log.error(f"Texture bake error encountered on '{tex_obj.image_name}': {res}")
            except Exception as exc:
                self.errors.append(exc)
                log.exception(f"Parallel dispatch worker thread collapsed on '{tex_obj.image_name}' with error: {exc}")

        log.info(f"Converted all {len(self.textures.values())} textures in {time.perf_counter() - start:.3f}s")



        return self.errors if self.errors else None




def export_materials(model:Model):
    e = ExporterMain(model=model)
    return e.export()