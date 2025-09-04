import bpy
from ..utils.game import update_loddefault

class SOURCEOPS_LodsReplaceModel(bpy.types.PropertyGroup):

    source: bpy.props.PointerProperty(
        name='Source',
        description='The object to be replaced by the target',
        type=bpy.types.Collection,
        #default=update_loddefault
    ) #type:ignore


    def poll_target(self, object):
        return object not in (self.source)

    target: bpy.props.PointerProperty(
        name='Target',
        description='The object to use as a replacement for this LOD',
        type=bpy.types.Collection,
        poll=poll_target
    ) #type:ignore



class SOURCEOPS_ModelLods(bpy.types.PropertyGroup):

    distance: bpy.props.IntProperty(
        name='Distance',
        description='The distance at which this LOD becomes active',
        default=25,
        min=0
    ) #type:ignore
    
    replace_model_items: bpy.props.CollectionProperty(type=SOURCEOPS_LodsReplaceModel) #type:ignore
    replace_model_index: bpy.props.IntProperty(default=0, name='Ctrl click to rename') #type:ignore