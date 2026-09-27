import bpy
import os
import logging
from .. import utils
from . game_props import SOURCEOPS_GameProps



class SOURCEOPS_AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = utils.common.get_package_root()

    wine: bpy.props.StringProperty(
        name='Wine',
        description='Path to your wine installation',
        subtype='FILE_PATH',
        update=utils.common.update_wine,
    )

    debug: bpy.props.BoolProperty(
        name='Debug',
        default=False
    )
    vtf_use_workers: bpy.props.BoolProperty(
        name='VTF Workers',
        description='Instead of running vtf export on the main python process\nSpawn a new process per texture to work on vtf creation.',
        default=True
    )

    threading_export_all: bpy.props.BoolProperty(
        name='Export All',
        description='Use Multithreading to Export all Models\n!!! May cause your pc to explode on lots of models',
        default=True,
    )

    mat_autodetect_mk_emissive_offskin: bpy.props.BoolProperty(
        name='Mat AutoDetect off skin',
        description='test',
        default=True,
    )
    mat_autodetect_mk_emissive_postfix: bpy.props.StringProperty(
        name='Emissive Off Postfix',
        description='test',
        default='_off',
    )

    game_items: bpy.props.CollectionProperty(type=SOURCEOPS_GameProps)
    game_index: bpy.props.IntProperty(default=0, name='Ctrl click to rename')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        if os.name == 'posix':
            layout.prop(self, 'wine')

        col = layout.column()
        col.label(text='Multithreading')
        col.prop(self, 'threading_export_all')

        layout.prop(self, 'debug')
        layout.prop(self, 'vtf_use_workers')

        layout.prop(self, 'mat_autodetect_mk_emissive_offskin')
        layout.prop(self, 'mat_autodetect_mk_emissive_postfix')

        row = layout.row()
        row.operator('sourceops.backup_preferences')
        row.operator('sourceops.restore_preferences')
