import numpy as np

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from PIL import Image

from sourcepp import vtfpp
Flags = vtfpp.VTF.Flags
ImageFormat = vtfpp.ImageFormat

from ....props.material_props import SOURCEOPS_AllMaterialsProps


@dataclass
class ExportTexture:
    #image: Image.Image
    image: np.ndarray
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

class PIL_VTF_map(Enum):
    RGB = ImageFormat.RGB888
    RGBA = ImageFormat.RGBA8888
    L = ImageFormat.I8
    LA = ImageFormat.IA88

VTF_ALPHAS = (
    'ABGR8888',
    'BGRA4444',
    'BGRA5551',
    'BGRA8888',
    'DXT3',
    'DXT5',
    'IA88',
    'RGBA16161616',
    'RGBA16161616F',
    'RGBA8888',
)