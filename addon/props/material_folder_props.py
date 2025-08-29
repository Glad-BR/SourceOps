import bpy


class SOURCEOPS_MaterialFolderProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name='Relative Path',
        description='$cdmaterials, the folder inside of which to look for materials, relative to your game\'s materials folder',
        default='models/example',
    ) #type:ignore
