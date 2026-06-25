import bpy


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



SOURCEOPS_NormalMaptypes = ([
    ('OPENGL', 'OpenGL', ''),
    ('DIRECTX', 'DirectX', '')
])

SOURCEOPS_Emissivetypes = ([
    ('COLOR', 'Color', ''),
    ('MASK', 'Mask', '')
])


class SOURCEOPS_AllMaterialsProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name='name',
        description='Name',
        default='MyMaterialName',
    )

    diffuse: bpy.props.PointerProperty(
        name='Base Color',
        type=bpy.types.Image,
    )

    ao: bpy.props.PointerProperty(
        name='Ambient Occlusion',
        type=bpy.types.Image,
    )

    roughness: bpy.props.PointerProperty(
        name='Roughness Map',
        type=bpy.types.Image,
    )

    metallic: bpy.props.PointerProperty(
        name='Metallic Map',
        type=bpy.types.Image,
    )

    normal: bpy.props.PointerProperty(
        name='Normal Map',
        type=bpy.types.Image,
    )

    normaltype: bpy.props.EnumProperty(
        name='Normal Map Format',
        description='The format of the normalmap, by default blender uses OpenGL.\nSource uses DirectX, if OpenGL is selected the map is automatically converted to DirectX',
        items=SOURCEOPS_NormalMaptypes,
        default='OPENGL',
    )

    emissive: bpy.props.PointerProperty(
        name='Emission Color',
        type=bpy.types.Image,
    )

    emissivetype: bpy.props.EnumProperty(
        name='Emissive Texture Type',
        description='What type of emissive texture it is, self colored or a mask of the base color',
        items=SOURCEOPS_Emissivetypes,
        default='COLOR',
    )