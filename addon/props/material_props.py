import bpy

from .vtf_props import SOURCEOPS_VTF_FORMAT
from . surface_props import SOURCEOPS_SurfaceProps

from sourcepp import vtfpp

class SOURCEOPS_MaterialFolderProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name='Relative Path',
        description='$cdmaterials, the folder inside of which to look for materials, relative to your game\'s materials folder',
        default='models/example',
    )

class SOURCEOPS_SkinProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name='Materials',
        description='Space separated list of VMT names, supports quotes.\nThe first line must be the materials currently on your model',
        default='example',
    )

SOURCEOPS_VTFVersion = ([
    ('0', '7.0', ''),
    ('1', '7.1', ''),
    ('2', '7.2', ''),
    ('3', '7.3', ''),
    ('4', '7.4', ''),
    ('5', '7.5', ''),
    ('6', '7.6', ''),
])

SOURCEOPS_NormalMaptypes = ([
    ('OPENGL', 'OpenGL', ''),
    ('DIRECTX', 'DirectX', '')
])
SOURCEOPS_Emissivetypes = ([
    ('COLOR', 'Color | $detail method', ''),
    ('MASK', 'Mask | $selfillum ', '')
])
SOURCEOPS_VMTtypes = ([
    ('VertexLitGeneric', 'VertexLitGeneric', '')
])
SOURCEOPS_MatsConverMethod = ([
    ('simple', 'Simple', ''),
    ('fakepbr1', 'PBR2Source', '')
])


vtf_format_description='VTF export format. Commonly Used Values are\n' \
'DXT1 (also known as BC1). Use for typical textures with NO alpha channel. \n' \
'DXT5 (also known as BC3). Use for typical textures with alpha channel.\n' \
'BGRA8888 Use for textures with an alpha channel and very fine gradients (i.e. normal maps or light halos). It can also be used to produce Very High quality textures. '


class SOURCEOPS_AllMaterialsProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name='name',
        description='Name',
        default='MyMaterialName',
    )
    type: bpy.props.EnumProperty(
        name='Shader',
        description='dev',
        items=SOURCEOPS_VMTtypes,
        default='VertexLitGeneric',
    )
    convert_method: bpy.props.EnumProperty(
        name='Method',
        description='dev',
        items=SOURCEOPS_MatsConverMethod,
        default='simple',
    )
    surfaceprop: bpy.props.EnumProperty(
        name='Surface Property',
        description='$surfaceprop, this affects decals and how it sounds in game',
        items=SOURCEOPS_SurfaceProps,
        default='default',
    )

    tex_diffuse: bpy.props.PointerProperty(
        name='Base Color',
        type=bpy.types.Image,
    )
    tex_ao: bpy.props.PointerProperty(
        name='AO',
        type=bpy.types.Image,
    )
    tex_roughness: bpy.props.PointerProperty(
        name='Roughness',
        type=bpy.types.Image,
    )
    tex_metallic: bpy.props.PointerProperty(
        name='Metallic',
        type=bpy.types.Image,
    )
    tex_normal: bpy.props.PointerProperty(
        name='Normal',
        type=bpy.types.Image,
    )
    tex_emissive: bpy.props.PointerProperty(
        name='Emission Color',
        type=bpy.types.Image,
    )


    normaltype: bpy.props.EnumProperty(
        name='Format',
        description='The format of the normalmap, by default blender uses OpenGL.\nSource uses DirectX, if OpenGL is selected the map is automatically converted to DirectX',
        items=SOURCEOPS_NormalMaptypes,
        default='OPENGL',
    )
    emissivetype: bpy.props.EnumProperty(
        name='Type',
        description='What type of emissive texture it is, self colored or a mask of the base color',
        items=SOURCEOPS_Emissivetypes,
        default='COLOR',
    )


    basetexture_format: bpy.props.EnumProperty(
        name='Basetexture',
        description=vtf_format_description,
        items=SOURCEOPS_VTF_FORMAT,
        default=vtfpp.ImageFormat.DXT5.name,
    )
    emissive_format: bpy.props.EnumProperty(
        name='Emissive',
        description=vtf_format_description,
        items=SOURCEOPS_VTF_FORMAT,
        default=vtfpp.ImageFormat.DXT1.name,
    )
    normal_format: bpy.props.EnumProperty(
        name='Bumbmap',
        description=vtf_format_description,
        items=SOURCEOPS_VTF_FORMAT,
        default=vtfpp.ImageFormat.BGRA8888.name,
    )
    phong_format: bpy.props.EnumProperty(
        name='Phong',
        description=vtf_format_description,
        items=SOURCEOPS_VTF_FORMAT,
        default=vtfpp.ImageFormat.I8.name,
    )