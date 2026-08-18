import cv2
import time
import numpy as np

from pathlib import Path
from typing import List

from sourcepp import vtfpp
Flags = vtfpp.VTF.Flags
ImageFormat = vtfpp.ImageFormat

from .types import *
from ..model_export.model import Model

from ...utils import mats
from ...props.material_props import SOURCEOPS_AllMaterialsProps
from ...utils.logger import log


class ExporterCommon:
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, images_arrs):
        start = time.perf_counter()
        self.model = model
        self.images = images_arrs
        self.mat = AllMaterialsProps

        assert self.mat.tex_diffuse != None


        self.np_diffuse = self._img(self.mat.tex_diffuse)

        # Super Secret ARM map
        if (
            self.mat.tex_ao is not None
            and self.mat.tex_ao is self.mat.tex_roughness
            and self.mat.tex_ao is self.mat.tex_metallic
        ):
            arm_map = self._img(self.mat.tex_roughness)
            self.np_ao = arm_map[:, :, 0]
            self.np_roughness = arm_map[:, :, 1]
            self.np_metallic = arm_map[:, :, 2]
        else:

            if self.mat.tex_ao and self.mat.tex_diffuse:
                self.np_ao = mats.np_grayscale(self._resize_to_largest(self._img(self.mat.tex_ao), self.np_diffuse))
            else:
                self.np_ao = None

            if self.mat.tex_roughness and self.mat.tex_metallic:
                self.np_roughness, self.np_metallic = self._resize_list_to_largest([
                    mats.np_grayscale(self._img(self.mat.tex_roughness)),
                    mats.np_grayscale(self._img(self.mat.tex_metallic))
                ])
            elif self.mat.tex_roughness and (not self.mat.tex_metallic):
                self.np_roughness = mats.np_grayscale(self._img(self.mat.tex_roughness))
                self.np_metallic = np.zeros_like(self.np_roughness)
            else:
                self.np_roughness = None
                self.np_metallic = None


        self.np_emissive = self._img(self.mat.tex_emissive) \
            if self.mat.tex_emissive else None

        self.np_bumbpmap = self._img(self.mat.tex_normal) \
            if self.mat.tex_normal else None

        self.MAX_EXPONENT = self.mat.fakepbr1_max_exponent

        log.debug(f'Exporter __init__ done took: {time.perf_counter()-start:.3f}s')

    #-------------------------------------------------------------------------------------------
    def _img(self, name) -> np.ndarray:
        if name:
            return self.images[name] if self.images[name] is not None else None
        else:
            return None

    def _resize_to_target(self, image: np.ndarray, target: np.ndarray) -> np.ndarray:
        if image is None or target is None:
            return image
        if image.shape[:2] != target.shape[:2]:
            return cv2.resize(image, target.shape[:2][::-1])
        return image
    
    def _resize_to_largest(self, image: np.ndarray, target: np.ndarray) -> np.ndarray:
        h1, w1 = image.shape[:2]
        h2, w2 = target.shape[:2]

        if h1 * w1 >= h2 * w2:
            target_size = (w1, h1)
        else:
            target_size = (w2, h2)

        return cv2.resize(image, target_size, interpolation=cv2.INTER_CUBIC)

    def _resize_list_to_largest(self, images: List[np.ndarray]) -> List[np.ndarray]:
        if not images:
            return []

        max_height = 0
        max_width = 0
        
        for img in images:
            h, w = img.shape[:2]
            if h > max_height:
                max_height = h
            if w > max_width:
                max_width = w

        target_size = (max_width, max_height)
        resized_images = []

        for img in images:
            h, w = img.shape[:2]
            if h == max_height and w == max_width:
                resized_images.append(img.copy())
            else:
                img_resized = cv2.resize(img, target_size, interpolation=cv2.INTER_CUBIC)
                resized_images.append(img_resized)

        return resized_images

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
        #roughness_exp = 2
        roughness_exp = self.mat.fakepbr2_envmap_roughness_exp
        left_side = cv2.addWeighted(self.np_metallic, 0.75, self.np_metallic, 0.0, 0.25)
        inv_roughness = cv2.subtract(1.0, self.np_roughness)
        right_side = cv2.pow(inv_roughness, roughness_exp)
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
        diffuse = self.np_diffuse.copy()

        if (self.mat.fakepbr1_darken_albedo) and (self.np_metallic is not None):
            (base_color, metallic) = self._resize_list_to_largest((diffuse, self.np_metallic))

            if (self.mat.basecolor_alpha_mode == 'none'):
                base_color[:, :, 3] = metallic
            else:
                # BaseColor alpha is already used
                base_color[..., :3] *= cv2.multiply(
                    src1=cv2.subtract(1.0, metallic),
                    src2=self.mat.fakepbr1_darken_albedo_factor
                )   
        else:
            base_color = diffuse

        if self.np_ao is not None:
            base_color = self._resize_to_largest(base_color, self.np_ao)
            base_color[..., :3] *= self.np_ao[..., np.newaxis]
        
        return base_color

    def _phong(self) -> np.ndarray:
        if self.mat.fakepbr1_use_albedotint:
            r = self._phongexponent()
            #g = self.np_metallic
            g = np.ones_like(r)
            b = np.ones_like(r)
            return np.dstack( (r,g,b) )
        else:
            return self._phongexponent()

    def _emissive(self) -> np.ndarray:
        if self.np_emissive is not None:
            if self.mat.emissivetype == 'COLOR':
                emissive = self.np_emissive
            elif self.mat.emissivetype == 'MASK':
                emissive = self.np_emissive
            elif self.mat.emissivetype == 'MASK2':
                diff, emiss = self._resize_list_to_largest( [self.np_diffuse,self.np_emissive] )
                emissive = cv2.multiply(diff,emiss)
                #emissive = self.np_diffuse * self.np_emissive
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

        log.debug(f'write {outpath}.vmt')

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

            if (blender_mat.fakepbr1_darken_albedo):
                if (blender_mat.basecolor_alpha_mode == 'none'):
                    f = f'{(1-blender_mat.fakepbr1_darken_albedo_factor):.2f}'
                    vmt.write('\n')
                    vmt.write(f'\t$color2               "[{f} {f} {f}]"\n')
                    vmt.write(f'\t$blendtintbybasealpha "1"\n')

            if envmap:
                #rel = self._relative(export_mat.envmapmask.output_path)
                tint = blender_mat.fakepbr2_envmap_tint
                vmt.write('\n')
                vmt.write(f'\t$envmap                   "env_cubemap"\n')
                vmt.write(f'\t$normalmapalphaenvmapmask "1"\n')
                #vmt.write(f'\t$envmapmask               "{rel}"\n')
                vmt.write(f'\t$envmaptint               "[{tint[0]:.2f} {tint[1]:.2f} {tint[2]:.2f}]"\n')
                #vmt.write(f'\t$envmapcontrast           "1.0"\n')
                #vmt.write(f'\t$envmapfresnel            "1"\n')
                #vmt.write(f'\t$envmaplightscale         "1.0"\n')

            if phong and export_mat.phong:
                rel = self._relative(export_mat.phong.output_path)
                vmt.write('\n')
                vmt.write(f'\t$phong                "1"\n')
                vmt.write(f'\t$phongexponenttexture "{rel}"\n')
                #vmt.write(f'\t$phongexponentfactor  "{self.MAX_EXPONENT}"\n') # Does nothing??
                vmt.write(f'\t$phongfresnelranges   "[0.1 0.8 1.0]"\n')

                vmt.write(f'\t$phongboost           "{str(blender_mat.fakepbr1_albedotint_phongboost)}"\n')
                if blender_mat.fakepbr1_use_albedotint:
                    vmt.write(f'\t$phongalbedotint      "1"\n')
                #else:
                #    vmt.write(f'\t$phongboost           "5.0"\n')

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

class test1(ExporterCommon):
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, images_arrs):
        super().__init__(model, AllMaterialsProps, images_arrs)
        assert self.mat.tex_normal    != None
        assert self.mat.tex_roughness != None

        roughness, metallic, base = self._resize_list_to_largest([
            self.np_roughness,
            self.np_metallic,
            self.np_diffuse
        ])
        luma = (
            0.2126 * base[..., 0] +
            0.7152 * base[..., 1] +
            0.0722 * base[..., 2]
        )
        reflectance = (
            0.04 * (1.0 - self.np_metallic) +
            luma * self.np_metallic
        )
        exp = self.mat.fakepbr2_envmap_roughness_exp
        power = exp * metallic
        log.critical(exp)
        avg_color_bgr = cv2.mean(base)[:3]
        log.critical(avg_color_bgr)
        reflectance *= np.power((1.0 - roughness), exp)
        reflectance = np.clip(reflectance, 0.0, 1.0)
        self.env_mask = reflectance
        self.phong_exp = reflectance

    def basetexture(self) -> np.ndarray:
        return self._basetexture()

    def normal(self) -> np.ndarray:
        img = self.np_bumbpmap.copy()
        img[..., 3] = self.env_mask
        return img
    
    def emissive(self) -> np.ndarray:
        return self._emissive()

    def phong(self) -> np.ndarray:
        return self._phong()

    def envmapmask(self) -> np.ndarray: # can't use both envmapmask and phongmask 
        return None

    def vmt(self, export_mat, outpath:Path):
        self._write_vmt(export_mat, outpath, normal_key="$bumpmap", phong=self.mat.fakepbr2_use_phong, envmap=True)

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
        mask = self._phongmask()
        img[..., 3] = self._resize_to_target(mask, img)
        return img
    
    def emissive(self) -> np.ndarray:
        return self._emissive()

    def phong(self) -> np.ndarray:
        return self._phong()
    
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
        mask = self._envmapmask()
        img[..., 3] = self._resize_to_target(mask, img)
        return img
    
    def emissive(self) -> np.ndarray:
        return self._emissive()

    def phong(self) -> np.ndarray:
        return self._phong()
    
    def envmapmask(self) -> np.ndarray:
        return None

    def vmt(self, export_mat:ExportMaterial, outpath:Path):
        self._write_vmt(
            export_mat=export_mat,
            outpath=outpath,
            normal_key="$bumpmap",
            envmap=self.mat.fakepbr2_use_envmap,
            phong=self.mat.fakepbr2_use_phong
        )

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

        (r,g,b) = self._resize_list_to_largest([
            self.np_ao if self.np_ao is not None else np.ones_like(self.np_roughness),
            self.np_roughness,
            self.np_metallic
        ])
        #r = mats.norm_size(self.np_ao, self.np_roughness) if self.np_ao is not None else np.ones_like(self.np_roughness)
        #g = self.np_roughness
        #b = self.np_metallic

        ARM = np.dstack((r,g,b))
        return ARM
    
    def envmapmask(self) -> np.ndarray:
        return None
    
    def vmt(self, export_mat:ExportMaterial, outpath:Path):
        blender_mat = export_mat.source

        log.debug(f'write {outpath}.vmt')

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
