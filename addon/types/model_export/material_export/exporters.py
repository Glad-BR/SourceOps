import numpy as np

from pathlib import Path
from PIL import Image, ImageChops

from sourcepp import vtfpp
Flags = vtfpp.VTF.Flags
ImageFormat = vtfpp.ImageFormat

from .types import ExportMaterial, VTF_ALPHAS
from ..model import Model
from ....utils import mats
from ....props.material_props import SOURCEOPS_AllMaterialsProps



class ExporterBasic:
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, pil_images):
        self.model = model
        self.images = pil_images
        self.mat = AllMaterialsProps

        assert self.mat.tex_diffuse != None

        ao = self._img(self.mat.tex_ao)
        diffuse = self._img(self.mat.tex_diffuse)
        self.np_diffuse_r = diffuse[:, :, 0]
        self.np_diffuse_g = diffuse[:, :, 1]
        self.np_diffuse_b = diffuse[:, :, 2]
        self.np_diffuse_a = diffuse[:, :, 3]
        self.np_ao = mats.np_grayscale( mats.norm_size(ao, diffuse) )

    def _img(self, name) -> np.ndarray:
        if name: return self.images[name] if self.images[name] is not None else None


    def basetexture(self) -> np.ndarray:
        r = self.np_diffuse_r * self.np_ao if self.np_ao is not None else self.np_diffuse_r
        g = self.np_diffuse_g * self.np_ao if self.np_ao is not None else self.np_diffuse_g
        b = self.np_diffuse_b * self.np_ao if self.np_ao is not None else self.np_diffuse_b
        a = self.np_diffuse_a

        rgb_array = np.dstack( (r, g, b, a) )
        return rgb_array

    def normal(self) -> np.ndarray:
        return self._img(self.mat.tex_normal)
    
    def emissive(self) -> np.ndarray:
        return self._img(self.mat.tex_emissive)

    def phong(self) -> np.ndarray:
        return None
    
    def envmapmask(self) -> np.ndarray:
        return None


    def _relative(self, path:Path) -> str:
        return path.relative_to(self.model.materials).with_suffix("").as_posix()

    def vmt(self, export_mat:ExportMaterial, outpath:Path):
            blender_mat = export_mat.source

            with open(f"{outpath}.vmt", "w") as vmt:

                vmt.write(f"{blender_mat.type}\n")
                vmt.write("{\n")

                rel = self._relative(export_mat.basetexture.output_path)
                vmt.write(f'\t$basetexture  "{rel}"\n')
                
                if export_mat.normal:
                    rel = self._relative(export_mat.normal.output_path)
                    vmt.write(f'\t$normal      "{rel}"\n')

                if blender_mat.surfaceprop and blender_mat.surfaceprop != 'default':
                    vmt.write('\n')
                    vmt.write(f'\t$surfaceprop\t"{str(blender_mat.surfaceprop)}"\n')

                if blender_mat.basetexture_format in VTF_ALPHAS:
                    vmt.write('\n')
                    vmt.write(f'\t$translucent      "1"\n')
                
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



# PBR-2-SOURCE secret sauce
# Magic numbers galore
class Pbr2Source:
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, pil_images):
        self.model = model
        self.images = pil_images
        self.mat = AllMaterialsProps

        assert self.mat.tex_diffuse != None
        assert self.mat.tex_roughness != None
        assert self.mat.tex_normal != None

        flat_normal_color = (128, 128, 255)

        self.np_roughness = mats.np_grayscale( self._img(self.mat.tex_roughness) )
        self.np_metallic  = mats.np_grayscale( mats.norm_size(self._img(self.mat.tex_metallic), self.np_roughness) )

        self.np_emissive_rgba = self._img(self.mat.tex_emissive)

        ao = self._img(self.mat.tex_ao)
        diffuse = self._img(self.mat.tex_diffuse)
        self.np_diffuse_r = diffuse[:, :, 0]
        self.np_diffuse_g = diffuse[:, :, 1]
        self.np_diffuse_b = diffuse[:, :, 2]
        self.np_diffuse_a = diffuse[:, :, 3]
        self.np_ao = mats.np_grayscale( mats.norm_size(ao, diffuse) )

        normal = self._img(self.mat.tex_normal)
        self.np_bumbpmap_x = normal[:, :, 0]
        self.np_bumbpmap_y = normal[:, :, 1]
        self.np_bumbpmap_z = normal[:, :, 2]


        self.MAX_EXPONENT = self.mat.fakepbr1_max_exponent


    def _img(self, name) -> np.ndarray:
        if name: return self.images[name] if self.images[name] is not None else None

    def _envmapmask(self):
        roughness_exp = 5
        return ((self.np_metallic * 0.75) + 0.25) * ((1-self.np_roughness) ** roughness_exp)

    def _phongmask(self):
        return ((1-self.np_roughness) ** 3) * 1.1
    
    def _phongexponent(self):
        return ((0.8 / self.MAX_EXPONENT) * (self.np_roughness ** -2))



    def basetexture(self) -> np.ndarray:
        r = self.np_diffuse_r * self.np_ao if self.np_ao is not None else self.np_diffuse_r
        g = self.np_diffuse_g * self.np_ao if self.np_ao is not None else self.np_diffuse_g
        b = self.np_diffuse_b * self.np_ao if self.np_ao is not None else self.np_diffuse_b
        a = self.np_diffuse_a
        rgb_array = np.dstack( (r, g, b, a) )
        return rgb_array

    def normal(self) -> np.ndarray:
        r = self.np_bumbpmap_x
        g = self.np_bumbpmap_y
        b = self.np_bumbpmap_z
        a = self._phongmask()

        rgb_array = np.dstack( (r, g, b, a) )
        return rgb_array
    
    def emissive(self) -> np.ndarray:
        return self._img(self.mat.tex_emissive)

    def phong(self) -> np.ndarray:
        l = self._phongexponent()
        return l
    
    def envmapmask(self) -> np.ndarray: # can't use both envmapmask and phongmask 
        return None



    def _relative(self, path:Path) -> str:
        return path.relative_to(self.model.materials).with_suffix("").as_posix()

    def vmt(self, export_mat:ExportMaterial, outpath:Path):
            blender_mat = export_mat.source

            with open(f"{outpath}.vmt", "w") as vmt:

                vmt.write(f"{blender_mat.type}\n")
                vmt.write("{\n")

                rel = self._relative(export_mat.basetexture.output_path)
                vmt.write(f'\t$basetexture  "{rel}"\n')
                
                if export_mat.normal:
                    rel = self._relative(export_mat.normal.output_path)
                    vmt.write(f'\t$bumpmap      "{rel}"\n')

                if blender_mat.surfaceprop and blender_mat.surfaceprop != 'default':
                    vmt.write('\n')
                    vmt.write(f'\t$surfaceprop\t"{str(blender_mat.surfaceprop)}"\n')

                if blender_mat.basetexture_format in VTF_ALPHAS:
                    vmt.write('\n')
                    vmt.write(f'\t$translucent      "1"\n')

                if export_mat.envmapmask:
                    rel = self._relative(export_mat.envmapmask.output_path)
                    vmt.write('\n')
                    vmt.write(f'\t$envmap                "env_cubemap"\n')
                    vmt.write(f'\t$envmapmask            "{rel}"\n')
                    vmt.write(f'\t$envmaptint            "[0.1 0.1 0.1]"\n')
                    vmt.write(f'\t$envmapcontrast        "1.0"\n')
                    #vmt.write(f'\t$basealphaenvmapmask   "1"\n')
                    vmt.write(f'\t$envmapfresnel         "1"\n')
                    vmt.write(f'\t$envmaplightscale      "1.0"\n')

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