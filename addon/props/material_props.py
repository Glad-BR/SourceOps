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