import bpy
import os
from .. import utils
from . game_props import SOURCEOPS_GameProps



class SOURCEOPS_AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = utils.common.get_name()

    wine: bpy.props.StringProperty(
        name='Wine',
        description='Path to your wine installation',
        subtype='FILE_PATH',
        update=utils.common.update_wine,
    )

    threading_export_all: bpy.props.BoolProperty(
        name='Export All',
        description='Use Multithreading to Export all Models\n!!! May cause your pc to explode on lots of models',
        default=True,
    )

    game_items: bpy.props.CollectionProperty(type=SOURCEOPS_GameProps)
    game_index: bpy.props.IntProperty(default=0, name='Ctrl click to rename')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        if os.name == 'posix':
            layout.prop(self, 'wine')

        layout.prop(self, 'threading_export_all')

        row = layout.row()
        row.operator('sourceops.backup_preferences')
        row.operator('sourceops.restore_preferences')
