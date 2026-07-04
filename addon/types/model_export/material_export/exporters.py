import numpy as np

from pathlib import Path

from sourcepp import vtfpp
Flags = vtfpp.VTF.Flags
ImageFormat = vtfpp.ImageFormat

from .types import ExportMaterial
from ..model import Model
from ....utils import mats
from ....props.material_props import SOURCEOPS_AllMaterialsProps



class ExporterCommon:
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, pil_images):
        self.model = model
        self.images = pil_images
        self.mat = AllMaterialsProps

        assert self.mat.tex_diffuse != None

        self.np_diffuse = self._img(self.mat.tex_diffuse)

        self.np_ao = mats.np_grayscale( mats.norm_size(self._img(self.mat.tex_ao), self.np_diffuse) ) \
            if self.mat.tex_ao else None

        self.np_roughness = mats.np_grayscale(self._img(self.mat.tex_roughness)) \
            if self.mat.tex_roughness else None
        
        self.np_metallic  = mats.np_grayscale(mats.norm_size(self._img(self.mat.tex_metallic), self.np_roughness)) \
            if (self.mat.tex_metallic and self.mat.tex_roughness) else None

        self.np_emissive = self._img(self.mat.tex_emissive) \
            if self.mat.tex_emissive else None

        self.np_bumbpmap = self._img(self.mat.tex_normal)\
            if self.mat.tex_normal else None

        self.MAX_EXPONENT = self.mat.fakepbr1_max_exponent

    # -------------------------------------------------------------------------------------------
    def _img(self, name) -> np.ndarray:
        if name:
            return self.images[name] if self.images[name] is not None else None
        else:
            return None

    def _relative(self, path:Path) -> str:
        return path.relative_to(self.model.materials).with_suffix("").as_posix()

    def _basetexture(self) -> np.ndarray:
        if self.np_ao is not None:
            self.np_diffuse[..., :3] *= self.np_ao[..., np.newaxis]
        return self.np_diffuse

    def _emissive(self) -> np.ndarray:
        return self.np_emissive

    def _write_vmt(
        self,
        export_mat: ExportMaterial,
        outpath: Path,
        normal_key: str = "$normal",
    ):
        blender_mat = export_mat.source

        surfaceprop = (blender_mat.surfaceprop and blender_mat.surfaceprop != 'default')

        print(f'write {outpath}.vmt')

        with open(f"{outpath}.vmt", "w") as vmt:
            vmt.write(f"{blender_mat.type}\n")
            vmt.write("{\n")

            rel = self._relative(export_mat.basetexture.output_path)
            vmt.write(f'\t$basetexture  "{rel}"\n')

            if export_mat.normal:
                rel = self._relative(export_mat.normal.output_path)
                vmt.write(f'\t{normal_key}      "{rel}"\n')

            if surfaceprop:
                vmt.write('\n')
                vmt.write(f'\t$surfaceprop\t"{str(blender_mat.surfaceprop)}"\n')

            if blender_mat.basecolor_alpha_mode != 'none':
                vmt.write('\n')
                vmt.write(f'\t${str(blender_mat.basecolor_alpha_mode)}\t"1"\n')

            if export_mat.envmapmask:
                rel = self._relative(export_mat.envmapmask.output_path)
                vmt.write('\n')
                vmt.write(f'\t$envmap                "env_cubemap"\n')
                vmt.write(f'\t$envmapmask            "{rel}"\n')
                vmt.write(f'\t$envmaptint            "[0.1 0.1 0.1]"\n')
                vmt.write(f'\t$envmapcontrast        "1.0"\n')
                vmt.write(f'\t$envmapfresnel         "1"\n')
                vmt.write(f'\t$envmaplightscale      "1.0"\n')

            if export_mat.phong:
                rel = self._relative(export_mat.phong.output_path)
                vmt.write('\n')
                vmt.write(f'\t$phong                 "1"\n')
                vmt.write(f'\t$phongexponenttexture  "{rel}"\n')
                vmt.write(f'\t$phongexponentfactor   "{self.MAX_EXPONENT}"\n')
                vmt.write(f'\t$phongboost            "5.0"\n')
                vmt.write(f'\t$phongfresnelranges    "[0.1 0.8 1.0]"\n')

            if export_mat.emissive:
                rel = self._relative(export_mat.emissive.output_path)
                vmt.write('\n')
                if blender_mat.emissivetype == 'COLOR':
                    vmt.write(f'\t$detail                "{rel}"\n')
                    vmt.write(f'\t$detailscale           "1"\n')
                    vmt.write(f'\t$detailblendmode       "5"\n')
                elif blender_mat.emissivetype == 'MASK':
                    vmt.write(f'\t$selfillum             "1"\n')
                    vmt.write(f'\t$selfillummask         "{rel}"\n')

            vmt.write("}")

#---------------------------------------------------------------------------------------------------------

class Basic(ExporterCommon):
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, pil_images):
        super().__init__(model, AllMaterialsProps, pil_images)


    def basetexture(self) -> np.ndarray:
        return self._basetexture()

    def normal(self) -> np.ndarray:
        return self.np_bumbpmap
    
    def emissive(self) -> np.ndarray:
        return self._emissive()

    def phong(self) -> np.ndarray:
        return None
    
    def envmapmask(self) -> np.ndarray:
        return None



    def vmt(self, export_mat:ExportMaterial, outpath:Path):
        self._write_vmt(export_mat, outpath)

#---------------------------------------------------------------------------------------------------------

class fakepbr1(ExporterCommon):
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, pil_images):
        super().__init__(model, AllMaterialsProps, pil_images)

        assert self.mat.tex_normal    != None
        assert self.mat.tex_roughness != None


    def _envmapmask(self):
        roughness_exp = 5
        return ((self.np_metallic * 0.75) + 0.25) * ((1-self.np_roughness) ** roughness_exp)

    def _phongmask(self):
        return ((1-self.np_roughness) ** 3) * 1.1
    
    def _phongexponent(self):
        return ((0.8 / self.MAX_EXPONENT) * (self.np_roughness ** -2))



    def basetexture(self) -> np.ndarray:
        return self._basetexture()

    def normal(self) -> np.ndarray:
        self.np_bumbpmap[..., 3] = self._phongmask()
        return self.np_bumbpmap
    
    def emissive(self) -> np.ndarray:
        return self._emissive()

    def phong(self) -> np.ndarray:
        return self._phongexponent()
    
    def envmapmask(self) -> np.ndarray: # can't use both envmapmask and phongmask 
        return None


    def vmt(self, export_mat:ExportMaterial, outpath:Path):
        self._write_vmt(export_mat, outpath, normal_key="$bumpmap")