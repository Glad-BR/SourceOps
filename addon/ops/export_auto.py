import bpy
import time
import multiprocessing
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.logger import log

from .. import utils
from ..types.model_export.model import Model
from ..types.model_export import qc

class SOURCEOPS_OT_ExportAuto(bpy.types.Operator):
    bl_idname = 'sourceops.export_auto'
    bl_options = {'REGISTER'}
    bl_label = 'Export Auto'
    bl_description = 'Export meshes, generate QC, compile QC, view model.\nShift click to export all models.\nCtrl click to customize export steps'

    ctrl: bpy.props.BoolProperty(name='Ctrl', description='Whether Ctrl was held during invoke', options={'HIDDEN', 'SKIP_SAVE'})
    shift: bpy.props.BoolProperty(name='Shift', description='Whether Shift was held during invoke', options={'HIDDEN', 'SKIP_SAVE'})

    all_models: bpy.props.BoolProperty(name='All Models', description='Export all models in the scene', default=False)
    export_meshes: bpy.props.BoolProperty(name='Export Meshes', description='Export the meshes and animations as SMD/FBX', default=True)
    export_materials: bpy.props.BoolProperty(name='Export Materials', description='Export the model materials', default=True)
    generate_qc: bpy.props.BoolProperty(name='Generate QC', description='Generate the QC based on your settings', default=True)
    compile_qc: bpy.props.BoolProperty(name='Compile QC', description='Compile the QC to an MDL', default=True)
    view_model: bpy.props.BoolProperty(name='View Model', description='Open the selected model in HLMV', default=False)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, 'all_models')

        col.prop(self, 'export_meshes')
        col.prop(self, 'export_materials')
        col.prop(self, 'generate_qc')
        col.prop(self, 'compile_qc')

        row = col.row()
        row.enabled = not self.all_models
        row.prop(self, 'view_model')

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

        if not utils.game.verify(game):
            self.report({'ERROR'}, 'Game is invalid')
            return {'CANCELLED'}

        self.ctrl = event.ctrl
        self.shift = event.shift

        if self.ctrl:
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def execute(self, context):
        prefs = utils.common.get_prefs(context)
        game = utils.common.get_game(prefs)
        sourceops = utils.common.get_globals(context)

        start = time.time()

        self._lock = Lock()
        self._results = []

        _WAIT = True

        self._executor = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()-1 if prefs.threading_export_all else 1)
        
        def _export_model_list(source_models: list[Model]):
            futures = [self._executor.submit(self.export_mat, source_model) for source_model in source_models]

            log.info(f'Exporting {len(source_models)} models in the scene')
            for source_model in source_models:
                error = self.export(source_model)
                if error:
                    self.report({'ERROR'}, error)
                    return {'CANCELLED'}

            log.info(f'Completed {len(source_models)} models')
            log.debug(f'Started Threaded Compilation of {len(source_models)} models')

            futures += [self._executor.submit(self.compile, source_model) for source_model in source_models]

            if _WAIT:
                for future in as_completed(futures):
                    log.debug(f'Future completed: {future}')
                    error = future.result()
                    if error:
                        with self._lock:
                            self._results.append(error)
                        log.error(f'Error during export: {error}')
                        #self._executor.shutdown(wait=False, cancel_futures=True)


        if (not self.ctrl and self.shift) or (self.ctrl and self.all_models):
            source_models = [Model(game, model, self._executor) for model in sourceops.model_items]
            try:
                _export_model_list(source_models)
            except KeyboardInterrupt as error:
                self.report({'ERROR'}, error)
                self._executor.shutdown(wait=False, cancel_futures=True)
                return {'CANCELLED'}

            for error in self._results:
                self.report({'ERROR'}, error)

            if self._results:
                return {'CANCELLED'}

            self.report({'INFO'}, f'Exported all models in the scene in {round(time.time() - start, 1)} seconds')
            return {'FINISHED'}

        else:
            model = utils.common.get_model(sourceops)
            source_model = Model(game, model, self._executor)

            try:
                _export_model_list([source_model])
            except KeyboardInterrupt as error:
                self.report({'ERROR'}, error)
                self._executor.shutdown(wait=False, cancel_futures=True)
                return {'CANCELLED'}

            for error in self._results:
                self.report({'ERROR'}, error)

            if self._results:
                return {'CANCELLED'}

            forced_static = not model.armature and not model.static
            static_message = ' (forced static due to lack of armature)' if forced_static else ''

            self.report({'INFO'}, f'Exported {model.name} in {round(time.time() - start, 1)} seconds{static_message}')
            return {'FINISHED'}

    def export(self, source_model: Model):
        if not self.ctrl or self.export_meshes:
            error = source_model.export_meshes()
            if error:
                return error

        if not self.ctrl or self.generate_qc:
            error = qc.generate_qc(source_model)
            if error:
                return error
            
    def export_mat(self, source_model: Model):
        if not self.ctrl or self.export_materials:
            error = source_model.export_materials()
            if error:
                return error

    def compile(self, source_model: Model):
        if not self.ctrl or self.compile_qc:
            error = source_model.compile_qc()
            if error:
                return error

        if self.ctrl and (not self.all_models and self.view_model):
            error = source_model.view_model()
            if error:
                return error
