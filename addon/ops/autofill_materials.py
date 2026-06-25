import bpy
import bpy_extras
from .. import utils

from ..utils.mats import BlenderInputNodes as Node


class SOURCEOPS_OT_AutofillMaterials(bpy.types.Operator):
    bl_idname = 'sourceops.autofill_materials'
    bl_label = 'Auto Detect and fill materials export list'
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_description = 'Auto Detect and fill materials export list'

    #@classmethod
    #def poll(cls, context):
    #    prefs = utils.common.get_prefs(context)
    #    game = utils.common.get_game(prefs)
    #    sourceops = utils.common.get_globals(context)
    #    model = utils.common.get_model(sourceops)
    #    return prefs and game and sourceops and model

    def invoke(self, context, event):
        prefs = utils.common.get_prefs(context)
        game = utils.common.get_game(prefs)
        sourceops = utils.common.get_globals(context)
        model = utils.common.get_model(sourceops)


        add_report = 0
        exs = 0
        names = set()
        for mat in model.materials_items:
            if mat: names.add(mat.name)

        all_mats = utils.mats.get_mats_from_model(model)
        for mat in all_mats:
            if mat.name not in names:
                add_report += 1
                item = model.materials_items.add()
                item.name = mat.name
            else:
                exs += 1
                item = model.materials_items[ model.materials_items.find(mat.name) ]

            item.diffuse   = utils.mats.probe_bsdf(mat, Node.BaseColor)
            item.roughness = utils.mats.probe_bsdf(mat, Node.Roughness)
            item.metallic  = utils.mats.probe_bsdf(mat, Node.Metallic)
            item.normal    = utils.mats.probe_bsdf(mat, Node.Normal)
            item.emissive  = utils.mats.probe_bsdf(mat, Node.Emissive)

                

        self.report({'INFO'}, f'Auto Detect Completed, Added:{add_report} new items. Updated:{exs} Existing')
        return {'FINISHED'}