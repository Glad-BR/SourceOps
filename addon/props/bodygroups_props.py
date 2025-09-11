import bpy

class SOURCEOPS_SublistBodygroupProps(bpy.types.PropertyGroup):

    reference: bpy.props.PointerProperty(
        name='Reference',
        description='The bodygroup collection this sublist belongs to',
        type=bpy.types.Collection,
    )


class SOURCEOPS_ModelBodygroupsProps(bpy.types.PropertyGroup):

    name: bpy.props.StringProperty(
        name='Name',
        description='The name of this bodygroup',
        default='bodygroup',
    )
 
    bodygroup_items: bpy.props.CollectionProperty(type=SOURCEOPS_SublistBodygroupProps)
    bodygroup_index: bpy.props.IntProperty(default=0, name='Ctrl click to rename')
