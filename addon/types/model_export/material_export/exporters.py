import numpy as np
import cv2
import time

from pathlib import Path

from sourcepp import vtfpp
Flags = vtfpp.VTF.Flags
ImageFormat = vtfpp.ImageFormat

from .types import *
from ..model import Model
from ....utils import mats
from ....props.material_props import SOURCEOPS_AllMaterialsProps



class ExporterCommon:
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, images_arrs):
        start = time.perf_counter()
        self.model = model
        self.images = images_arrs
        self.mat = AllMaterialsProps

        assert self.mat.tex_diffuse != None


        self.np_diffuse = self._img(self.mat.tex_diffuse)


        # Super Secret ARM map
        if (self.mat.tex_ao == self.mat.tex_roughness == self.mat.tex_metallic) and (self.mat.tex_roughness is not None):
            arm_map = self._img(self.mat.tex_roughness)
            self.np_ao = arm_map[:, :, 0]
            self.np_roughness = arm_map[:, :, 1]
            self.np_metallic = arm_map[:, :, 2]
        else:
            self.np_ao = mats.np_grayscale(self._resize_to_target(image=self._img(self.mat.tex_ao), target=self.np_diffuse)) \
                if self.mat.tex_ao else None
            
            self.np_roughness = mats.np_grayscale(self._img(self.mat.tex_roughness)) \
                if self.mat.tex_roughness else None
            
            self.np_metallic  = mats.np_grayscale(self._resize_to_target(image=self._img(self.mat.tex_metallic), target=self.np_roughness)) \
                if (self.mat.tex_metallic and self.mat.tex_roughness) else \
                np.zeros_like(self.np_roughness)


        self.np_emissive = self._img(self.mat.tex_emissive) \
            if self.mat.tex_emissive else None

        self.np_bumbpmap = self._img(self.mat.tex_normal) \
            if self.mat.tex_normal else None

        self.MAX_EXPONENT = self.mat.fakepbr1_max_exponent

        print(f'Exporter __init__ done took: {time.perf_counter()-start:.3f}s')

    #-------------------------------------------------------------------------------------------
    def _img(self, name) -> np.ndarray:
        if name:
            return self.images[name] if self.images[name] is not None else None
        else:
            return None

    def _resize_to_target(self, image, target):
        if image is None or target is None:
            return image
        if image.shape[:2] != target.shape[:2]:
            return cv2.resize(image, target.shape[:2][::-1])
        return image

    def _screen(self, base:np.ndarray, blend:np.ndarray) -> np.ndarray:
        return 1.0 - (1.0 - base) * (1.0 - blend)

    def _specular(self, albedo, metalic):
        dielectric_spec = np.full_like(albedo, 0.04)
        specular = (dielectric_spec * (1.0 - metalic)) + (albedo * metalic)
        return specular



    #-------------------------------------------------------------------------------------------

#    def _envmapmask(self) -> np.ndarray:
#        roughness_exp = 5
#        return ((self.np_metallic * 0.75) + 0.25) * ((1-self.np_roughness) ** roughness_exp)
#
#    def _phongmask(self) -> np.ndarray:
#        return ((1-self.np_roughness) ** 3) * 1.1
#    
#    def _phongexponent(self) -> np.ndarray:
#        return ((0.8 / self.MAX_EXPONENT) * (self.np_roughness ** -2))

    def _envmapmask(self) -> np.ndarray:
        left_side = cv2.addWeighted(self.np_metallic, 0.75, self.np_metallic, 0.0, 0.25)
        inv_roughness = cv2.subtract(1.0, self.np_roughness)
        right_side = cv2.pow(inv_roughness, 5)
        return cv2.multiply(left_side, right_side)

    def _phongmask(self) -> np.ndarray:
        roughness = self.np_roughness
        if roughness is not None and self.np_bumbpmap is not None and roughness.shape[:2] != self.np_bumbpmap.shape[:2]:
            roughness = cv2.resize(roughness, self.np_bumbpmap.shape[:2][::-1])

        inv_roughness = cv2.subtract(1.0, roughness)
        base_pow3 = cv2.pow(inv_roughness, 3)
        return cv2.multiply(base_pow3, 1.1)

    def _phongexponent(self) -> np.ndarray:
        roughness = self.np_roughness
        if roughness is not None and self.np_bumbpmap is not None and roughness.shape[:2] != self.np_bumbpmap.shape[:2]:
            roughness = cv2.resize(roughness, self.np_bumbpmap.shape[:2][::-1])

        roughness_pow_neg2 = cv2.pow(roughness, -2.0)
        scalar_multiplier = 0.8 / self.MAX_EXPONENT
        return cv2.multiply(roughness_pow_neg2, scalar_multiplier)

    #-------------------------------------------------------------------------------------------

    def _relative(self, path:Path) -> str:
        return path.relative_to(self.model.materials).with_suffix("").as_posix()

    def _basetexture(self) -> np.ndarray:
        img = self.np_diffuse.copy()

        if (self.np_metallic is not None) and (self.mat.fakepbr1_darken_albedo):
            metal = self._resize_to_target(self.np_metallic[..., np.newaxis], img)
            img = self._specular(self.np_diffuse, metal)

        if self.np_ao is not None:
            img[..., :3] *= self.np_ao[..., np.newaxis]
        
        return img


    def _emissive(self) -> np.ndarray:
        if self.np_emissive is not None:
            if self.mat.emissivetype == 'COLOR':
                emissive = self.np_emissive
            elif self.mat.emissivetype == 'MASK':
                emissive = self.np_emissive
            elif self.mat.emissivetype == 'MASK2':
                emissive = self.np_diffuse * self.np_emissive
            return emissive
        return None

    #-------------------------------------------------------------------------------------------

    def _write_vmt(
        self,
        export_mat: ExportMaterial,
        outpath: Path,
        normal_key: str = "$normal",
        phong: bool = False,
        envmap: bool = False,
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

            if envmap:
                #rel = self._relative(export_mat.envmapmask.output_path)
                vmt.write('\n')
                vmt.write(f'\t$envmap                   "env_cubemap"\n')
                vmt.write(f'\t$normalmapalphaenvmapmask "1"\n')
                #vmt.write(f'\t$envmapmask               "{rel}"\n')
                #vmt.write(f'\t$envmaptint               "[0.1 0.1 0.1]"\n')
                #vmt.write(f'\t$envmapcontrast           "1.0"\n')
                #vmt.write(f'\t$envmapfresnel            "1"\n')
                #vmt.write(f'\t$envmaplightscale         "1.0"\n')

            if phong and export_mat.phong:
                rel = self._relative(export_mat.phong.output_path)
                vmt.write('\n')
                vmt.write(f'\t$phong                "1"\n')
                vmt.write(f'\t$phongexponenttexture "{rel}"\n')
                vmt.write(f'\t$phongexponentfactor  "{self.MAX_EXPONENT}"\n')
                vmt.write(f'\t$phongfresnelranges   "[0.1 0.8 1.0]"\n')

                print(blender_mat.fakepbr1_use_albedotint)

                if blender_mat.fakepbr1_use_albedotint:
                    vmt.write(f'\t$phongboost           "{str(blender_mat.fakepbr1_albedotint_phongboost)}"\n')
                    vmt.write(f'\t$phongalbedotint      "1"\n')
                else:
                    vmt.write(f'\t$phongboost           "5.0"\n')

            if export_mat.emissive:
                rel = self._relative(export_mat.emissive.output_path)
                vmt.write('\n')
                if blender_mat.emissivetype in ('COLOR', 'MASK2'):
                    vmt.write(f'\t$detail                "{rel}"\n')
                    vmt.write(f'\t$detailscale           "1"\n')
                    vmt.write(f'\t$detailblendmode       "5"\n')
                elif blender_mat.emissivetype == 'MASK':
                    vmt.write(f'\t$selfillum             "1"\n')
                    vmt.write(f'\t$selfillummask         "{rel}"\n')

            vmt.write("}")

#---------------------------------------------------------------------------------------------------------

class Basic(ExporterCommon):
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, images_arrs):
        super().__init__(model, AllMaterialsProps, images_arrs)


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


    def vmt(self, export_mat, outpath:Path):
        self._write_vmt(export_mat, outpath)

#---------------------------------------------------------------------------------------------------------

class fakepbr1(ExporterCommon):
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, images_arrs):
        super().__init__(model, AllMaterialsProps, images_arrs)
        assert self.mat.tex_normal    != None
        assert self.mat.tex_roughness != None


    def basetexture(self) -> np.ndarray:
        return self._basetexture()

    def normal(self) -> np.ndarray:
        img = self.np_bumbpmap.copy()
        img[..., 3] = self._phongmask()
        return img
    
    def emissive(self) -> np.ndarray:
        return self._emissive()

    def phong(self) -> np.ndarray:
        if self.mat.fakepbr1_use_albedotint:
            r = self._phongexponent()
            g = np.ones_like(r)
            b = g
            return np.dstack( (r,g,b) )
        else:
            return self._phongexponent()
    
    def envmapmask(self) -> np.ndarray: # can't use both envmapmask and phongmask 
        return None


    def vmt(self, export_mat, outpath:Path):
        self._write_vmt(export_mat, outpath, normal_key="$bumpmap", phong=True)

#---------------------------------------------------------------------------------------------------------

class fakepbr2(ExporterCommon):
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, images_arrs):
        super().__init__(model, AllMaterialsProps, images_arrs)
        assert self.mat.tex_normal    != None
        assert self.mat.tex_roughness != None


    def basetexture(self) -> np.ndarray:
        return self._basetexture()

    def normal(self) -> np.ndarray:
        img = self.np_bumbpmap.copy()
        img[..., 3] = self._envmapmask()
        return img
    
    def emissive(self) -> np.ndarray:
        return self._emissive()

    def phong(self) -> np.ndarray:
        return None
    
    def envmapmask(self) -> np.ndarray:
        return None


    def vmt(self, export_mat:ExportMaterial, outpath:Path):
        self._write_vmt(export_mat, outpath, normal_key="$bumpmap", envmap=True,)

#---------------------------------------------------------------------------------------------------------

class ExoPBR1(ExporterCommon):
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, images_arrs):
        super().__init__(model, AllMaterialsProps, images_arrs)
        assert self.mat.tex_normal    != None
        assert self.mat.tex_roughness != None


    def basetexture(self) -> np.ndarray:
        return self.np_diffuse
    
    def normal(self) -> np.ndarray:
        return self.np_bumbpmap

    def emissive(self) -> np.ndarray:
        return self._emissive()
    
    def phong(self) -> np.ndarray:
        # $texture2 ARM map
        r = mats.norm_size(self.np_ao, self.np_roughness) if self.np_ao is not None else np.ones_like(self.np_roughness)
        g = self.np_roughness
        b = self.np_metallic

        ARM = np.dstack((r,g,b))
        return ARM
    
    def envmapmask(self) -> np.ndarray:
        return None
    
    def vmt(self, export_mat:ExportMaterial, outpath:Path):
        blender_mat = export_mat.source

        print(f'write {outpath}.vmt')

        with open(f"{outpath}.vmt", "w") as vmt:
            vmt.write(f"screenspace_general_8tex\n")
            vmt.write("{\n")

            rel = self._relative(export_mat.basetexture.output_path)
            vmt.write(f'\t$basetexture "{rel}"\n')

            rel = self._relative(export_mat.phong.output_path)
            vmt.write(f'\t$texture1    "{rel}"\n') #ARM map

            rel = self._relative(export_mat.normal.output_path)
            vmt.write(f'\t$texture2    "{rel}"\n') # Normal 

            if export_mat.emissive:
                rel = self._relative(export_mat.emissive.output_path)
                vmt.write('\n')
                vmt.write(f'\t$texture3 "{rel}"\n') # Emissive

            if blender_mat.basecolor_alpha_mode != 'none':
                vmt.write('\n')
                vmt.write(f'\t$alphablend "1"\n')

            vmt.write('\n')
            vmt.write('\t$model "1"\n')
            vmt.write('\t$cull  "1"\n')

            vmt.write('\n')
            vmt.write('\tProxies {\n')
            vmt.write('\t\tExoPBR {}\n')
            vmt.write('\t}')

            vmt.write('\n')
            vmt.write("}")
