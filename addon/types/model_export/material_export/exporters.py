import bpy

from pathlib import Path
from PIL import Image, ImageChops

from sourcepp import vtfpp
Flags = vtfpp.VTF.Flags
ImageFormat = vtfpp.ImageFormat

from ..model import Model
from ....props.material_props import SOURCEOPS_AllMaterialsProps


from .types import ExportMaterial


import numpy as np

def _norm_img(source:Image.Image, target:Image.Image) -> Image.Image:
    if source.size != target.size:
        source = source.resize(target.size)
    if source.mode != target.mode:
        source = source.convert(target.mode)
    return source

def _multiply(image1:Image.Image, image2:Image.Image) -> Image.Image:
    return ImageChops.multiply(_norm_img(image1, image2), image2)

AAAA = Path('/home/glad/Desktop/GMOD DEV/GarrysMod/garrysmod/addons/test/materials/models/props_gbr/lamps/FlourecentLamp002a/')


class ExporterBasic:
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, pil_images):
        self.model = model
        self.images = pil_images
        self.mat = AllMaterialsProps

    def basetexture(self) -> Image.Image:
        if self.mat.tex_ao:
            return _multiply(self.images[self.mat.tex_ao], self.images[self.mat.tex_diffuse])
        else:
            return self.images[self.mat.tex_diffuse]

    def normal(self) -> Image.Image:
        if self.mat.tex_normal:
            return self.images[self.mat.tex_normal]
        else:
            return None

    def emissive(self) -> Image.Image:
        if self.mat.tex_emissive:
            return self.images[self.mat.tex_emissive]
        else:
            return None

    def phong(self) -> Image.Image:
        return None
    
    def envmapmask(self) -> Image.Image:
        return None

    def vmt(self, export_mat:ExportMaterial, outpath:Path):
            blender_mat = export_mat.source

            with open(f"{outpath}.vmt", "w") as vmt:

                vmt.write(f"{blender_mat.type}\n")
                vmt.write("{\n")

                rel = export_mat.basetexture.output_path.relative_to(self.model.materials).with_suffix("").as_posix()
                vmt.write(f'\t$basetexture      "{rel}"\n')
                vmt.write(f'\t$normal           "{rel}"\n')

                if export_mat.normal:
                    rel = export_mat.normal.output_path.relative_to(self.model.materials).with_suffix("").as_posix()
                    

                if blender_mat.surfaceprop:
                    vmt.write('\n')
                    vmt.write(f'\t$surfaceprop "{str(blender_mat.surfaceprop)}"\n')

                if export_mat.emissive:
                    rel = export_mat.emissive.output_path.relative_to(self.model.materials).with_suffix("").as_posix()
                    vmt.write('\n')

                    if blender_mat.emissivetype == 'COLOR':
                        vmt.write(f'\t$detail           "{rel}"\n')
                        vmt.write(f'\t$detailscale      "1"\n')
                        vmt.write(f'\t$detailblendmode  "5"\n')
                    elif blender_mat.emissivetype == 'MASK':
                        vmt.write(f'\t$selfillum        "1"\n')
                        vmt.write(f'\t$selfillummask    "{rel}"\n')

                vmt.write("}")







# PBR-2-SOURCE secret sauce


# Magic numbers and actual PBR-2-Source implementation differ

class Pbr2Source:
    def __init__(self, model:Model, AllMaterialsProps:SOURCEOPS_AllMaterialsProps, pil_images):
        self.model = model
        self.images = pil_images
        self.mat = AllMaterialsProps

        assert self.mat.tex_diffuse != None
        assert self.mat.tex_roughness != None
        assert self.mat.tex_normal != None

        flat_normal_color = (128, 128, 255)

        self.diffuse   = self._img(self.mat.tex_diffuse).convert('RGBA')
        self.roughness = self._img(self.mat.tex_roughness).convert('L')
        self.ao        = self._img(self.mat.tex_ao).convert('L') if self.mat.tex_ao else None
        self.bumbpmap  = self._img(self.mat.tex_normal).convert('RGB').resize(self.roughness.size)
        self.metallic  = self._img(self.mat.tex_metallic).convert('L').resize(self.roughness.size) \
            if self.mat.tex_metallic else Image.new(mode='L', size=self.roughness.size) #Resize Metallic just to be sure

        r, g, b, a = self.diffuse.split()
        self.np_diffuse_r = np.array(r , dtype=np.float32) / 255.0
        self.np_diffuse_g = np.array(g , dtype=np.float32) / 255.0
        self.np_diffuse_b = np.array(b , dtype=np.float32) / 255.0
        self.np_diffuse_a = np.array(a , dtype=np.float32) / 255.0

        r, g, b = self.bumbpmap.split()
        self.np_bumbpmap_x = np.array(r , dtype=np.float32) / 255.0
        self.np_bumbpmap_y = np.array(g , dtype=np.float32) / 255.0
        self.np_bumbpmap_z = np.array(b , dtype=np.float32) / 255.0

        self.np_roughness = np.array(self.roughness , dtype=np.float32) / 255.0
        self.np_metallic  = np.array(self.metallic  , dtype=np.float32) / 255.0
        self.np_ao        = np.array(self.ao        , dtype=np.float32) / 255.0 if self.mat.tex_ao else None

        self.MAX_EXPONENT = self.mat.fakepbr1_max_exponent


    def _img(self, name) -> Image.Image:
        return self.images[name]

    def _envmapmask(self):
        roughness_exp = 5
        return ((self.np_metallic * 0.75) + 0.25) * ((1-self.np_roughness) ** roughness_exp)

    def _phongmask(self):
        return ((1-self.np_roughness) ** 3) * 1.1
    
    def _phongexponent(self):
        
        return ((0.8 / self.MAX_EXPONENT) * (self.np_roughness ** -2))

    def _arr_to_img(self, arr) -> Image.Image:
        clip = np.clip(arr * 255.0, 0, 255)
        return Image.fromarray( clip.astype(np.uint8) )


    def basetexture(self) -> Image.Image:
        r = self.np_diffuse_r * self.np_ao if self.mat.tex_ao else self.np_diffuse_r
        g = self.np_diffuse_g * self.np_ao if self.mat.tex_ao else self.np_diffuse_g
        b = self.np_diffuse_b * self.np_ao if self.mat.tex_ao else self.np_diffuse_b
        a = self.np_diffuse_a

        rgb_array = np.dstack( (r, g, b, a) )
        return self._arr_to_img(rgb_array)
    
    def normal(self) -> Image.Image:
        r = self.np_bumbpmap_x
        g = self.np_bumbpmap_y
        b = self.np_bumbpmap_z
        a = self._phongmask()

        rgb_array = np.dstack( (r, g, b, a) )
        return self._arr_to_img(rgb_array)
    
    def emissive(self) -> Image.Image:
        if self.mat.tex_emissive:
            return self.images[self.mat.tex_emissive]
        else:
            return None

    def phong(self) -> Image.Image:
        r = self._phongexponent()
        g = r
        b = r
        a = np.ones_like(r)

        rgb_array = np.dstack( (r, g, b, a) )
        return self._arr_to_img(rgb_array)
    
    def envmapmask(self) -> Image.Image:
        l = self._envmapmask()
        rgb_array = np.dstack( (l, l, l, np.ones_like(l)) )
        return self._arr_to_img(rgb_array)


    def vmt(self, export_mat:ExportMaterial, outpath:Path):
            blender_mat = export_mat.source

            with open(f"{outpath}.vmt", "w") as vmt:

                vmt.write(f"{blender_mat.type}\n")
                vmt.write("{\n")

                rel = export_mat.basetexture.output_path.relative_to(self.model.materials).with_suffix("").as_posix()
                vmt.write(f'\t$basetexture  "{rel}"\n')
                
                if export_mat.normal:
                    rel = export_mat.normal.output_path.relative_to(self.model.materials).with_suffix("").as_posix()
                    vmt.write(f'\t$bumpmap      "{rel}"\n')

                if blender_mat.surfaceprop:
                    vmt.write('\n')
                    vmt.write(f'\t$surfaceprop\t"{str(blender_mat.surfaceprop)}"\n')

                rel = export_mat.envmapmask.output_path.relative_to(self.model.materials).with_suffix("").as_posix()
                vmt.write('\n')
                vmt.write(f'\t$envmap                "env_cubemap"\n')
                vmt.write(f'\t$envmapmask            "{rel}"\n')
                vmt.write(f'\t$envmaptint            "[0.1 0.1 0.1]"\n')
                vmt.write(f'\t$envmapcontrast        "1.0"\n')
                #vmt.write(f'\t$basealphaenvmapmask   "1"\n')
                vmt.write(f'\t$envmapfresnel         "1"\n')
                vmt.write(f'\t$envmaplightscale      "1.0"\n')

                rel = export_mat.phong.output_path.relative_to(self.model.materials).with_suffix("").as_posix()
                vmt.write('\n')
                vmt.write(f'\t$phong                 "1"\n')
                vmt.write(f'\t$phongexponenttexture  "{rel}"\n')
                vmt.write(f'\t$phongexponentfactor   "{self.MAX_EXPONENT}"\n')
                vmt.write(f'\t$phongboost            "5.0"\n')
                vmt.write(f'\t$phongfresnelranges    "[0.1 0.8 1.0]"\n')
                

                if export_mat.emissive:
                    rel = export_mat.emissive.output_path.relative_to(self.model.materials).with_suffix("").as_posix()
                    vmt.write('\n')
                    if blender_mat.emissivetype == 'COLOR':
                        vmt.write(f'\t$detail                "{rel}"\n')
                        vmt.write(f'\t$detailscale           "1"\n')
                        vmt.write(f'\t$detailblendmode       "5"\n')
                    elif blender_mat.emissivetype == 'MASK':
                        vmt.write(f'\t$selfillum             "1"\n')
                        vmt.write(f'\t$selfillummask         "{rel}"\n')

                vmt.write("}")