import bpy
import os
from .. import utils
from . game_props import SOURCEOPS_GameProps


class SOURCEOPS_AddonPrefs(bpy.types.AddonPreferences):
    bl_idname =  __name__.partition('.')[0]

    game_items: bpy.props.CollectionProperty(type=SOURCEOPS_GameProps) #type:ignore
    game_index: bpy.props.IntProperty(default=0, name='Ctrl click to rename') #type:ignore

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False


        row = layout.row()
        row.operator('sourceops.backup_preferences')
        row.operator('sourceops.restore_preferences')
