from __future__ import annotations
import bpy

from .. import utils
from ..utils.mats import BlenderInputNodes as Node
from ..utils.logger import log
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from ..props import SOURCEOPS_AllMaterialsProps

class SOURCEOPS_OT_AutofillMaterials(bpy.types.Operator):
    bl_idname = 'sourceops.autofill_materials'
    bl_label = 'Auto Detect and fill materials export list'
    bl_options = {'REGISTER'}
    bl_description = 'Auto Detect and fill materials export list'

    def execute(self, context):
        prefs = utils.common.get_prefs(context)
        sourceops = utils.common.get_globals(context)
        model = utils.common.get_model(sourceops)

        materials_items = model.materials_items

        emissive_postfix = prefs.mat_autodetect_mk_emissive_postfix
        off_skin = prefs.mat_autodetect_mk_emissive_offskin

        add_report = 0
        Updated = 0
        names = set()
        for mat in materials_items:
            mat: SOURCEOPS_AllMaterialsProps
            if mat: names.add(mat.name)

        emissive_mats:set[SOURCEOPS_AllMaterialsProps] = set()

        all_mats = utils.mats.mats_from_model(model)
        for blender_mat in all_mats:
            if blender_mat.name not in names:
                add_report += 1
                mat:SOURCEOPS_AllMaterialsProps = materials_items.add()
                mat.name = blender_mat.name
            else:
                Updated += 1
                mat:SOURCEOPS_AllMaterialsProps = materials_items[materials_items.find(blender_mat.name)]

            mat.tex_diffuse   = utils.mats.probe_bsdf(blender_mat, Node.BaseColor)
            mat.tex_roughness = utils.mats.probe_bsdf(blender_mat, Node.Roughness)
            mat.tex_metallic  = utils.mats.probe_bsdf(blender_mat, Node.Metallic)
            mat.tex_normal    = utils.mats.probe_bsdf(blender_mat, Node.Normal)
            mat.tex_emissive  = utils.mats.probe_bsdf(blender_mat, Node.Emissive)

            if off_skin and (mat.tex_emissive is not None):
                emissive_mats.add(mat)

        if off_skin:
            log.debug(emissive_mats)

            for source_mat in emissive_mats:
                new_name = source_mat.name + emissive_postfix

                if new_name not in materials_items:
                    add_report += 1
                    new_mat: SOURCEOPS_AllMaterialsProps = materials_items.add()
                    new_mat.name = new_name
                    
                    source_index = materials_items.find(source_mat.name)
                    
                    if source_index != -1:
                        last_index = len(materials_items) - 1
                        target_index = source_index + 1
                        materials_items.move(last_index, target_index)
                else:
                    Updated += 1
                    new_mat: SOURCEOPS_AllMaterialsProps = materials_items[materials_items.find(new_name)]

                for key, value in source_mat.items():
                    if key in ('name', 'tex_emissive'):
                        continue
                    log.debug(f'{key} --> {value}')
                    new_mat[key] = value


        self.report({'INFO'}, f'Auto Detect Completed, Added:{add_report} new items. Updated:{Updated} Existing')
        return {'FINISHED'}