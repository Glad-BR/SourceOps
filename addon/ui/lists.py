import bpy


class SOURCEOPS_UL_GameList(bpy.types.UIList):
    bl_idname = 'SOURCEOPS_UL_GameList'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False, translate=False)


class SOURCEOPS_UL_ModelList(bpy.types.UIList):
    bl_idname = 'SOURCEOPS_UL_ModelList'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False, translate=False)


class SOURCEOPS_UL_MaterialFolderList(bpy.types.UIList):
    bl_idname = 'SOURCEOPS_UL_MaterialFolderList'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False, translate=False)


class SOURCEOPS_UL_SkinList(bpy.types.UIList):
    bl_idname = 'SOURCEOPS_UL_SkinList'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False, translate=False)


class SOURCEOPS_UL_SequenceList(bpy.types.UIList):
    bl_idname = 'SOURCEOPS_UL_SequenceList'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False, translate=False)


class SOURCEOPS_UL_EventList(bpy.types.UIList):
    bl_idname = 'SOURCEOPS_UL_EventList'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False, translate=False)


class SOURCEOPS_UL_AttachmentList(bpy.types.UIList):
    bl_idname = 'SOURCEOPS_UL_AttachmentList'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False, translate=False)


class SOURCEOPS_UL_ParticleList(bpy.types.UIList):
    bl_idname = 'SOURCEOPS_UL_ParticleList'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False, translate=False)


class SOURCEOPS_UL_MapList(bpy.types.UIList):
    bl_idname = 'SOURCEOPS_UL_MapList'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False, translate=False)



class SOURCEOPS_UL_LodsList(bpy.types.UIList):
    bl_idname = 'SOURCEOPS_UL_LodsList'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=f'Distance {item.distance}')
        #layout.label(text='LOD')
        #layout.prop(item, 'distance', text='Dist', emboss=False)


class SOURCEOPS_UL_LodsReplaceModelList(bpy.types.UIList):
    bl_idname = 'SOURCEOPS_UL_LodsReplaceModelList'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text='Index')
        layout.prop(item, 'source', text='Replace', emboss=False)
        layout.prop(item, 'target', text='With', emboss=False)    