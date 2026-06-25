import bpy
from .. import utils
from ..types.model_export.model import Model
from ..types.model_export import qc

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
        error = qc.generate_qc(source_model)

        if error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        forced_static = not model.armature and not model.static
        static_message = ' (forced static due to lack of armature)' if forced_static else ''

        self.report({'INFO'}, f'Generated QC for {model.name}{static_message}')
        return {'FINISHED'}
