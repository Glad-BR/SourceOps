import numpy as np

from dataclasses import dataclass
from pathlib import Path
from sourcepp import vtfpp

from ...props.material_props import SOURCEOPS_AllMaterialsProps

@dataclass
class ExportTexture:
    image: np.ndarray
    image_hash: str
    image_name: str
    parent_name : str

    output_path: Path = None

    format: vtfpp.ImageFormat = None
    flags: tuple[vtfpp.VTF.Flags, ...] = ()
    invert_green: bool = False

@dataclass
class ExportMaterial:
    source: SOURCEOPS_AllMaterialsProps
    basetexture: ExportTexture = None
    normal: ExportTexture = None
    emissive: ExportTexture = None
    phong: ExportTexture = None
    envmapmask: ExportTexture = None

ColorMasks = ('COLOR', 'COLOR2', 'MASK2', 'MASK3')
GrayMasks = ('MASK')