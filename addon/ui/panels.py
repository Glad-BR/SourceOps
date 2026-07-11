import bpy
from .. utils import common
from .. import icons


class SOURCEOPS_PT_MainPanel(bpy.types.Panel):
    bl_idname = 'SOURCEOPS_PT_MainPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SourceOps'
    bl_label = f'SourceOps    -    {common.get_version()}'

    def draw(self, context):
        layout = self.layout

        prefs = common.get_prefs(context)
        game = common.get_game(prefs)
        sourceops = common.get_globals(context)
        model = common.get_model(sourceops)
        bodygroups = common.get_bodygroups(model)
        lods = common.get_lods(model)
        material_folder = common.get_material_folder(model)
        material = common.get_material(model)
        skin = common.get_skin(model)
        sequence = common.get_sequence(model)
        event = common.get_event(sequence)
        attachment = common.get_attachment(model)
        particle = common.get_particle(model)
        map_props = common.get_map(sourceops)

        if sourceops:
            box = layout.box()
            row = box.row()
            row.scale_x = row.scale_y = 1.5
            row.label(text='Panel')
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(sourceops, 'panel', expand=True, icon_only=True)

        if prefs and sourceops.panel == 'GAMES':
            box = layout.box()
            common.center_label(box, text='Games')

            row = box.row()
            row.template_list('SOURCEOPS_UL_GameList', '', prefs, 'game_items', prefs, 'game_index', rows=5)
            col = row.column(align=True)
            self.draw_list_buttons(col, 'GAMES')

            if game:
                col = common.align_column(box)
                col.prop(game, 'name')
                col.prop(game, 'game')
                col = common.align_column(box)
                col.prop(game, 'bin')
                col.prop(game, 'studiomdl')
                col.prop(game, 'hlmv')
                col = common.align_column(box)
                col.prop(game, 'usecustom')
                if game.usecustom:
                    col.prop(game, 'customname')
                #col = common.align_column(box)
                col.prop(game, 'materials')
                col.prop(game, 'models')
                col.prop(game, 'modelsrc')
                col.prop(game, 'mapsrc')
                col = common.split_column(box)
                col.prop(game, 'mesh_type')
                col.prop(game, 'vtf_version')


        elif sourceops and sourceops.panel == 'MODELS':
            box = layout.box()
            common.center_label(box, text='Models')

            row = box.row()
            row.template_list('SOURCEOPS_UL_ModelList', '', sourceops, 'model_items', sourceops, 'model_index', rows=5)
            col = row.column(align=True)
            self.draw_list_buttons(col, 'MODELS')

            if model:
                col = common.split_column(box)
                col.prop(model, 'name')
                col.prop(model, 'armature')
                col.prop(model, 'reference')
                col.prop(model, 'collision')
                #col.prop(model, 'bodygroups')
                col.prop(model, 'stacking')

        elif model and sourceops.panel == 'MODEL_BODYGROUPS':

            box = layout.box()
            common.center_label(box, text='Bodygroups')

            row = box.row()
            row.template_list('SOURCEOPS_UL_ModelBodygroupsList', '', model, 'bodygroups_items', model, 'bodygroups_index', rows=5)
            col = row.column(align=True)
            self.draw_list_buttons(col, 'MODEL_BODYGROUPS')
            
            if bodygroups:
                col = common.split_column(box)
                col.prop(bodygroups, 'name')

                box = layout.box()
                common.center_label(box, text='studio')

                row = box.row()
                row.template_list('SOURCEOPS_UL_BodygroupsSublist', '', bodygroups, 'sublist_items', bodygroups, 'sublist_index', rows=5)
                col = row.column(align=True)
                self.draw_list_buttons(col, 'BODYGROUPS_SUBLIST')

                sublist = common.get_sub_bodygroups(bodygroups)
                if sublist:
                    col = common.split_column(box)
                    col.prop(sublist, 'reference')


        elif model and sourceops.panel == 'MODEL_LODS':
            box = layout.box()
            common.center_label(box, text='Level of Details (LODs)')

            row = box.row()
            row.template_list('SOURCEOPS_UL_ModelLodsList', '', model, 'lods_items', model, 'lods_index', rows=5)
            col = row.column(align=True)
            self.draw_list_buttons(col, 'MODEL_LODS')
            
            if lods:
                col = common.split_column(box)
                col.prop(lods, 'distance')

                box = layout.box()
                common.center_label(box, text='Replacemodels')

                row = box.row()
                row.template_list('SOURCEOPS_UL_LodsReplaceList', '', lods, 'replacemodel_items', lods, 'replacemodel_index', rows=5)
                col = row.column(align=True)
                self.draw_list_buttons(col, 'LODS_REPLACE')

                replacemodel = common.get_sub_lods(lods)

                if replacemodel:
                    col = common.split_column(box)
                    col.prop(replacemodel, 'source')
                    col.prop(replacemodel, 'target')


        elif model and sourceops.panel == 'MODEL_OPTIONS':
            box = layout.box()
            common.center_label(box, text='Model Options')

            col = common.split_column(box)
            col.prop(model, 'surface')
            col.prop(model, 'glass')
            col.prop(model, 'static')
            col.prop(model, 'fastbuild')
            col.prop(model, 'rename_material')
            row = col.row()
            row.enabled = model.static
            row.prop(model, 'static_prop_combine')
            col.prop(model, 'joints')
            col.prop(model, 'illumposition_source')
            col.prop(model, 'illumposition_vector') if model.illumposition_source == 'MANUAL' else None
            col.prop(model, 'mass')

            box = layout.box()
            common.center_label(box, text='Transform Options')

            col = common.split_column(box)
            col.prop(model, 'prepend_armature')
            col.prop(model, 'ignore_transforms')

            sub = col.column()
            sub.enabled = not (model.static and model.static_prop_combine)
            sub.prop(model, 'origin_source')

            if model.origin_source == 'MANUAL':
                align = sub.column(align=True)
                align.prop(model, 'origin', text='Origin')
                sub.prop(model, 'rotation')
            elif model.origin_source == 'OBJECT':
                sub.prop(model, 'origin_object')


            col.prop(model, 'scale')
            col.prop(model, 'unitscale_fix')

            col = box.column(align=True)
            col.label(text='Tip: Use scale 39.37 to get a 1:1 export')
            col.label(text='Source runs on imperial, a 16" cube will equal 16 hammer units (more or less)')


        elif model and sourceops.panel == 'TEXTURES':
            row1 = layout.row(align=True).split(factor=0.5, align=True)

            box = row1.box()
            common.center_label(box, text='Material Folders')

            row = box.row()
            row.template_list('SOURCEOPS_UL_MaterialFolderList', '', model, 'material_folder_items', model, 'material_folder_index', rows=5)
            col = row.column(align=True)
            self.draw_list_buttons(col, 'MATERIAL_FOLDERS')

            if material_folder:
                col = common.split_column(box)
                col.prop(material_folder, 'name')

            box = row1.box()
            common.center_label(box, text='Skins')

            row = box.row()
            row.template_list('SOURCEOPS_UL_SkinList', '', model, 'skin_items', model, 'skin_index', rows=5)
            col = row.column(align=True)
            self.draw_list_buttons(col, 'SKINS')

            if skin:
                col = common.split_column(box)
                col.prop(skin, 'name')

            box = layout.box()
            common.center_label(box, text='Materials')

            row = box.row()
            row.template_list('SOURCEOPS_UL_AllMaterialsList', '', model, 'materials_items', model, 'materials_index', rows=5)
            col = row.column(align=True)
            self.draw_list_buttons(col, 'MATERIALS')

            col = common.split_column(box)
            if material:
                col.prop(material, 'surfaceprop')
            col.operator('sourceops.autofill_materials', text='Auto Detect')

            row = layout.row(align=True).split(factor=0.5, align=True)

            if material:
                box = row.box()
                common.center_label(box, text='Textures')

                col1 = box.column(align=True)
                col1.prop(material, 'tex_diffuse')
                col1.prop(material, 'basecolor_alpha_mode')

                col1.separator()
                col1.prop(material, 'tex_ao')
                col1.prop(material, 'tex_roughness')
                col1.prop(material, 'tex_metallic')
                col1.separator()
                col1.prop(material, 'tex_normal')
                col1.prop(material, 'normaltype')
                col1.separator()
                col1.prop(material, 'tex_emissive')
                col1.prop(material, 'emissivetype')
                col1.separator()

                c = row.column(align=True)
                box = c.box()
                common.center_label(box, text='VTF Format')

                col2 = box.column(align=True)
                col2.prop(material, 'basetexture_format')
                col2.prop(material, 'emissive_format')
                col2.prop(material, 'normal_format')

                col2.separator()
                common.center_label(col2, text='Export Settings')

                col2.separator()

                col2.prop(game, 'vtf_version')
                col2.prop(material, 'type')


                def _phong(col2):
                    split = col2.split(factor=factor, align=True)
                    split.label(text='Max Exponent')
                    split.prop(material, 'fakepbr1_max_exponent', text='')

                    split = col2.split(factor=factor, align=True)
                    split.prop(material, 'fakepbr1_use_albedotint', text='Albedo Tint')
                    c2 = split.row()
                    c2.enabled = material.fakepbr1_use_albedotint
                    c2.prop(material, 'fakepbr1_albedotint_phongboost')

                    split = col2.split(factor=factor, align=True)
                    split.enabled = (material.tex_metallic is not None)
                    split.prop(material, 'fakepbr1_darken_albedo', text='Darken Albedo')

                    c = split.row()
                    c.enabled = (material.tex_metallic is not None) and (material.fakepbr1_darken_albedo)
                    c.prop(material, 'fakepbr1_darken_albedo_factor', text='Factor')

                if (material.type == 'ExoPBR'):
                    box.separator(factor=9.7)
                else:
                    col2.prop(material, 'convert_method')

                    col2.separator()

                    factor = 0.23

                    if material.convert_method == 'fakepbr1':
                        _phong(col2)

                    
                    elif material.convert_method == 'fakepbr2':
                        col2.prop(material, 'fakepbr2_use_phong', text='Also Use Phong')

                        if material.fakepbr2_use_phong:
                            _phong(col2)

                    if not material.tex_diffuse:
                        col2.alert = True
                        col2.label(text=f'Base Color is required for Export', icon='ERROR')

                    if material.convert_method != 'simple':
                        if not material.tex_normal:
                            col2.alert = True 
                            col2.label(text=f'Normalmap is required for FakePBR Export', icon='ERROR')
                        if not material.tex_roughness:
                            col2.alert = True 
                            col2.label(text=f'Roughness is required for FakePBR Export', icon='ERROR')
                

                #col2.separator(factor=2)


        elif model and sourceops.panel == 'SEQUENCES':
            box = layout.box()
            common.center_label(box, text='Sequences')

            row = box.row()
            row.template_list('SOURCEOPS_UL_SequenceList', '', model, 'sequence_items', model, 'sequence_index', rows=5)
            col = row.column(align=True)
            self.draw_list_buttons(col, 'SEQUENCES')

            if sequence:
                col = common.split_column(box)
                col.prop(sequence, 'name')
                col.prop(sequence, 'action')

                col.prop(sequence, 'use_framerate')
                sub = col.column()
                sub.enabled = sequence.use_framerate
                sub.prop(sequence, 'framerate')

                col.prop(sequence, 'use_range')
                sub = col.column()
                sub.enabled = sequence.use_range
                sub.prop(sequence, 'start')
                sub.prop(sequence, 'end')

                col.prop(sequence, 'activity')
                col.prop(sequence, 'weight')
                col.prop(sequence, 'snap')
                col.prop(sequence, 'loop')


        elif sequence and sourceops.panel == 'EVENTS':
            box = layout.box()
            common.center_label(box, text='Events')

            row = box.row()
            row.template_list('SOURCEOPS_UL_EventList', '', sequence, 'event_items', sequence, 'event_index', rows=5)
            col = row.column(align=True)
            self.draw_list_buttons(col, 'EVENTS')

            if event:
                col = common.split_column(box)
                col.prop(event, 'name')
                col.prop(event, 'event')
                col.prop(event, 'frame')
                col.prop(event, 'value')


        elif model and sourceops.panel == 'PARTICLES':
            box = layout.box()
            common.center_label(box, text='Particles')
            
            row = box.row()
            row.template_list('SOURCEOPS_UL_ParticleList', '', model, 'particle_items', model, 'particle_index', rows=5)
            col = row.column(align=True)
            self.draw_list_buttons(col, 'PARTICLES')

            if particle:
                col = common.split_column(box)
                col.prop(particle, 'name')
                col.prop(particle, 'attachment_type')
                col.prop(particle, 'attachment_point')


        elif model and sourceops.panel == 'ATTACHMENTS':
            box = layout.box()
            common.center_label(box, text='Attachments')

            row = box.row()
            row.template_list('SOURCEOPS_UL_AttachmentList', '', model, 'attachment_items', model, 'attachment_index', rows=5)
            col = row.column(align=True)
            self.draw_list_buttons(col, 'ATTACHMENTS')

            if attachment:
                col = common.split_column(box)
                col.prop(attachment, 'name')

                armature = model.armature
                if armature and armature.data:
                    col.prop_search(attachment, 'bone', armature.data, 'bones')

                col.prop(attachment, 'offset')
                col.prop(attachment, 'rotation')
                col.prop(attachment, 'absolute')
                col.prop(attachment, 'rigid')

        if sourceops.panel in {
                'GAMES',
                'MODELS',
                'MODEL_BODYGROUPS',
                'MODEL_LODS',
                'MODEL_OPTIONS',
                'TEXTURES',
                'SEQUENCES',
                'EVENTS',
                'ATTACHMENTS',
                'PARTICLES'}:

            box = layout.box()
            row = box.row()
            row.scale_x = 1.5
            row.scale_y = 1.5
            row.label(text='Export')

            row = row.row(align=True)
            row.alignment = 'RIGHT'

            r = row.row(align=True)
            r.scale_x = 0.45
            #r.scale_y = 1.5
            r.operator('sourceops.open_folder', text='MDL', icon='FILEBROWSER')
            r.operator('sourceops.open_material_folder', text='TEX', icon='FILEBROWSER')
            row.separator()
            row.operator('sourceops.export_meshes', text='', icon_value=icons.id('smd'))
            row.operator('sourceops.generate_qc', text='', icon_value=icons.id('qc'))
            row.operator('sourceops.compile_qc', text='', icon_value=icons.id('mdl'))
            row.operator('sourceops.export_materials', text='', icon='TEXTURE')
            row.operator('sourceops.view_model', text='', icon_value=icons.id('hlmv'))
            row.operator('sourceops.export_auto', text='', icon='AUTO')

        if sourceops and sourceops.panel == 'MAPS':
            box = layout.box()
            common.center_label(box, text='Maps')

            row = box.row()
            row.template_list('SOURCEOPS_UL_MapList', '', sourceops, 'map_items', sourceops, 'map_index', rows=5)
            col = row.column(align=True)
            self.draw_list_buttons(col, 'MAPS')

            if map_props:
                col = common.split_column(box)
                col.prop(map_props, 'name')
                col.prop(map_props, 'brush_collection')
                col.prop(map_props, 'disp_collection')
                col.prop(map_props, 'geometry_scale')
                col.prop(map_props, 'texture_scale')
                col.prop(map_props, 'lightmap_scale')
                col.prop(map_props, 'allow_skewed_textures')
                col.prop(map_props, 'align_to_grid')

            box = layout.box()
            row = box.row()
            row.scale_x = row.scale_y = 1.5
            row.label(text='Export')
            row = row.row(align=True)
            row.alignment = 'RIGHT'

            row.operator('sourceops.export_vmf', text='', icon_value=icons.id('vmf'))

        if sourceops and sourceops.panel == 'SIMULATION':
            box = layout.box()
            common.center_label(box, text='Simulation')

            col = common.split_column(box)
            col.prop(sourceops, 'simulation_input')
            col.prop(sourceops, 'simulation_output')
            box.operator('sourceops.rig_simulation', text='Rig Simulation')

        if sourceops and sourceops.panel == 'MISC':
            box = layout.box()

            common.center_label(box, text='Misc')

            col = box.column()
            col.operator('sourceops.weighted_normal')
            col.operator('sourceops.triangulate')
            col.operator('sourceops.pose_bone_transforms', text='Copy Pose Bone Translation').type = 'TRANSLATION'
            col.operator('sourceops.pose_bone_transforms', text='Copy Pose Bone Rotation').type = 'ROTATION'

    def draw_list_buttons(self, layout, item):
        op = layout.operator('sourceops.list_operator', text='', icon='ADD')
        op.mode, op.item = 'ADD', item
        op = layout.operator('sourceops.list_operator', text='', icon='REMOVE')
        op.mode, op.item = 'REMOVE', item

        layout.separator()
        op = layout.operator('sourceops.list_operator', text='', icon='DUPLICATE')
        op.mode, op.item = 'COPY', item
        layout.separator()

        op = layout.operator('sourceops.list_operator', text='', icon='TRIA_UP')
        op.mode, op.item = 'MOVE_UP', item
        op = layout.operator('sourceops.list_operator', text='', icon='TRIA_DOWN')
        op.mode, op.item = 'MOVE_DOWN', item
