import bpy
from .vtf_props import SOURCEOPS_VTF_FORMAT
from . surface_props import SOURCEOPS_SurfaceProps
from .. import utils

from sourcepp import vtfpp

class SOURCEOPS_MaterialFolderProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name='Relative Path',
        description='$cdmaterials, the folder inside of which to look for materials, relative to your game\'s materials folder',
        default='models/example',
        subtype='DIR_PATH',
        update=utils.game.update_mat_folder
    )

class SOURCEOPS_SkinProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name='Materials',
        description='Space separated list of VMT names, supports quotes.\nThe first line must be the materials currently on your model',
        default='example',
    )

SOURCEOPS_VTFVersion = ([
    ('2', '7.2', ''),
    ('3', '7.3', ''),
    ('4', '7.4', ''),
    ('5', '7.5', ''),
    ('6', '7.6', ''),
])

SOURCEOPS_BaseColorAlphaMode = ([
    ('none',        'None',        ''),
    ('translucent', 'Translucent', ''),
    ('alphatest',   'Alphatest',   ''),
    ('additive',    'Additive',    ''),
])
SOURCEOPS_NormalMaptypes = ([
    ('OPENGL',  'OpenGL',  ''),
    ('DIRECTX', 'DirectX', ''),
])
SOURCEOPS_Emissivetypes = ([
    ('COLOR', 'Color | $detail',     ''),
    ('MASK',   'Mask | $selfillum ', ''),
    ('MASK2',  'Mask | $detail',     ''),
])
SOURCEOPS_VMTtypes = ([
    ('VertexLitGeneric', 'VertexLitGeneric', ''),
    ('UnlitGeneric',     'UnlitGeneric',     ''),
    ('ExoPBR',           'ExoPBR (GMOD)',    ''),
])
SOURCEOPS_MatsConverMethod = ([
    ('simple',   'Simple',          ''),
    ('fakepbr1', 'FakePBR $phong',  ''),
    ('fakepbr2', 'FakePBR &envmap', ''),
])

vtf_format_description = 'VTF export format. Commonly Used Values are\n' \
'DXT1 (also known as BC1). Use for typical textures with NO alpha channel. \n' \
'DXT5 (also known as BC3). Use for typical textures with alpha channel.\n' \
'BGRA8888 Use for textures with an alpha channel and very fine gradients (i.e. normal maps or light halos). It can also be used to produce Very High quality textures. '

vtf_version_description = 'VTF versions from the Valve wiki:\n' \
'7.2 | Supported by Source 2004 and later engine branches.\n' \
'7.3 | Supported by Source 2007 and newer engine branches.\n' \
'7.4 | Supported by Source 2007 and newer engine branches; used for Xbox 360/PlayStation 3 VTFs.\n' \
'7.5 | Supported by Alien Swarm and newer engine branches; mainly used for newer Games. Not compatible with older Source 2004/Source 2013-era branches.\n' \
'7.6 | Unofficially supported by Strata Source; adds deflate/zstd compression and BC6H/BC7 support.\n'

basecolor_alpha_mode_description = 'Witch shader parameter should be used to acheive transparency:\n\n' \
'None: Material is not transparent\n\n' \
'Additive: Specifies that the material should be rendered additively; that is, its colour values will be added to underlying pixels.\n\n' \
'Translucent: Specifies that the material should be partially see-through. The alpha channel of the $basetexture is used to decide translucency per-pixel.\n\n' \
'Alphatest: Specifies a mask to use to determine binary opacity. White represents fully opaque, while black represents fully transparent. Any values in-between are rounded to either 0 or 1'

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
    basecolor_alpha_mode: bpy.props.EnumProperty(
        name='Translucency',
        description=basecolor_alpha_mode_description,
        items=SOURCEOPS_BaseColorAlphaMode,
        default='none',
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


    fakepbr1_max_exponent: bpy.props.IntProperty(
        name='Max Exponent',
        description='Max Exponent',
        default=32,
        min=0,
    )
    fakepbr1_use_albedotint: bpy.props.BoolProperty(
        name='$phongalbedotint',
        description='$phongalbedotint',
        default=True,
    )
    fakepbr1_albedotint_phongboost: bpy.props.IntProperty(
        name='$phongboost',
        description='$phongboost',
        min=0,
        default=50,
    )
    fakepbr1_darken_albedo: bpy.props.BoolProperty(
        name='darken albedo',
        description='Uses Metallic Map to darken BaseColor',
        default=False
    )
    fakepbr1_darken_albedo_factor: bpy.props.FloatProperty(
        name='factor',
        description='How much should the $basetexture be darkend by metallic map',
        default=0.5,
        min=0.0,
        max=1.0,
    )

    fakepbr2_use_phong: bpy.props.BoolProperty(
        name='test',
        description='test',
        default=False
    )
    fakepbr2_envmap_roughness_exp: bpy.props.FloatProperty(
        name='test',
        description='test',
        min=0,
        max=5,
        default=5
    )

    # VertexLitGeneric and UnlitGeneric stuff
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

    # ExoPBR stuff
    pbr1_arm_format: bpy.props.EnumProperty(
        name='ARM map',
        description=vtf_format_description,
        items=SOURCEOPS_VTF_FORMAT,
        default=vtfpp.ImageFormat.ATI2N.name,
    )
    pbr1_normal_format: bpy.props.EnumProperty(
        name='ARM map',
        description=vtf_format_description,
        items=SOURCEOPS_VTF_FORMAT,
        default=vtfpp.ImageFormat.ATI2N.name,
    )

