from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from sourcepp import vtfpp
Flags = vtfpp.VTF.Flags
ImageFormat = vtfpp.ImageFormat

from ....props.material_props import SOURCEOPS_AllMaterialsProps


import numpy as np



@dataclass
class ExportTexture:
    image: Image.Image | np.ndarray
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
    envmapmask: ExportTexture = None