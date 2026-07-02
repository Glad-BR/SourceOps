import bpy
from .. import utils
from ..types.model_export.model import Model

from ..types.model_export.material_export import material

class SOURCEOPS_OT_ExportMaterials(bpy.types.Operator):
    bl_idname = 'sourceops.export_materials'
    bl_options = {'REGISTER'}
    bl_label = 'Export Materials'
    bl_description = 'Export this model\'s materials'

    @classmethod
    def poll(cls, context):
        prefs = utils.common.get_prefs(context)
        game = utils.common.get_game(prefs)
        sourceops = utils.common.get_globals(context)
        model = utils.common.get_model(sourceops)
        return prefs and game and sourceops and model

    def invoke(self, context, event):
        prefs = utils.common.get_prefs(context)
        game = utils.common.get_game(prefs)
        sourceops = utils.common.get_globals(context)
        model = utils.common.get_model(sourceops)

        if not utils.game.verify(game):
            self.report({'ERROR'}, 'Game is invalid')
            return {'CANCELLED'}

        source_model = Model(game, model)
        error = Model.export_materials(source_model)

        if error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        self.report({'INFO'}, f'Materials exported successfully')
        return {'FINISHED'}



#Open Folder Operator
class SOURCEOPS_OT_OpenMaterialFolder(bpy.types.Operator):
    bl_idname = 'sourceops.open_material_folder'
    bl_options = {'REGISTER'}
    bl_label = 'Open Material Folder'
    bl_description = 'Open the folder where this model\'s materials are exported'

    @classmethod
    def poll(cls, context):
        prefs = utils.common.get_prefs(context)
        game = utils.common.get_game(prefs)
        sourceops = utils.common.get_globals(context)
        model = utils.common.get_model(sourceops)
        return prefs and game and sourceops and model

    def invoke(self, context, event):
        prefs = utils.common.get_prefs(context)
        game = utils.common.get_game(prefs)
        sourceops = utils.common.get_globals(context)
        model = utils.common.get_model(sourceops)

        if not utils.game.verify(game):
            self.report({'ERROR'}, 'Game is invalid')
            return {'CANCELLED'}

        source_model = Model(game, model)
        error = source_model.open_material_folder()

        if error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        self.report({'INFO'}, 'Opened material folder')
        return {'FINISHED'}