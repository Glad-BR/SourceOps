import bpy
import time
import subprocess
import os

from shutil import move
from pathlib import Path
from traceback import print_exc
from ... utils import common, mats
from ... import props
from . smd import SMD
from . fbx import export_fbx
from ...utils.logger import log, getLogger

from concurrent.futures import ThreadPoolExecutor
import subprocess

class Model:
    def __init__(self, game:props.SOURCEOPS_GameProps, model:props.SOURCEOPS_ModelProps):
        self.prefs = common.get_prefs(bpy.context)
        self.wine = Path(common.get_wine(self.prefs))

        self.game = Path(game.game)
        self.bin = Path(game.bin)
        self.studiomdl = Path(game.studiomdl)
        self.hlmv = Path(game.hlmv)
        if model.static and model.static_prop_combine:
            self.modelsrc = self.game.parent.parent.joinpath('content', self.game.name, 'models')
        else:
            self.modelsrc = Path(game.modelsrc)
        self.materials = Path(game.materials)
        self.models = Path(game.models)
        self.mapsrc = Path(game.mapsrc)
        self.mesh_type = game.mesh_type

        self.name = Path(model.name).with_suffix('').as_posix()
        self.stem = common.clean_filename(Path(self.name).stem)
        if model.static and model.static_prop_combine:
            directory = self.modelsrc.joinpath(self.name).parent
        else:
            directory = self.modelsrc.joinpath(self.name)
        self.directory = common.verify_folder(directory)


        self.material_folder_items = model.material_folder_items
        self.skin_items = model.skin_items

        self.materials_items = model.materials_items
        self.materials_index = model.materials_index



        self.vtf_version = game.vtf_version #



        self.sequence_items = model.sequence_items
        self.attachment_items = model.attachment_items
        self.particle_items = model.particle_items

        self.armature = model.armature
        self.reference = model.reference
        self.collision = model.collision
        self.stacking = model.stacking

        self.bodygroups = model.bodygroups_items
        self.lods_items = model.lods_items

        self.rename_material = model.rename_material
        self.surface = model.surface
        self.glass = model.glass
        self.static = model.static
        self.fastbuild = model.fastbuild
        self.static_prop_combine = model.static_prop_combine
        self.joints = model.joints
        self.illumposition = common.get_illumposition(model)
        self.mass = model.mass

        self.prepend_armature = model.prepend_armature
        self.ignore_transforms = model.ignore_transforms

        self.origin_source = model.origin_source
        self.origin_object = model.origin_object

        self.origin = model.origin
        self.rotation = model.rotation

        if model.unitscale_fix:
            self.scale = (model.scale * bpy.context.scene.unit_settings.scale_length)
        else:
            self.scale = model.scale


    def export_meshes(self):
        self.ensure_modelsrc_folder()
        # self.remove_modelsrc_old()  # Commented out because it might be annoying.


        def export_objects(ref):
            if ref:
                objects = self.get_all_objects(ref)
                path = self.get_body_path(ref)
                self.export_mesh(self.armature, objects, path)
    

        if not self.sequence_items:
            idle_path = self.directory.joinpath('anims', 'idle.SMD')
            self.export_anim(self.armature, None, idle_path)
        else:
            for sequence in self.sequence_items:
                path = self.directory.joinpath('anims', f'{common.clean_filename(sequence.name)}.SMD')
                self.export_anim(self.armature, sequence.action, path)
    

        export_objects(self.reference)
        export_objects(self.collision)
    
        if self.bodygroups:
            for bodygroup in self.bodygroups:
                for sublist in getattr(bodygroup, 'sublist_items', []):
                    export_objects(getattr(sublist, 'reference', None))
    
        if self.lods_items:
            # Export blank if needed
            if any(
                replace.target is None
                for lod in self.lods_items
                for replace in getattr(lod, 'replacemodel_items', [])
            ):
                blank_path = self.directory.joinpath('blank.SMD')
                self.export_anim(self.armature, None, blank_path)
    
            for lod in self.lods_items:
                for replace in getattr(lod, 'replacemodel_items', []):
                    if replace.source and replace.target:
                        export_objects(replace.target)
    
        if self.stacking:
            for collection in getattr(self.stacking, 'children', []):
                export_objects(collection)



    def export_anim(self, armature, action, path):
        self.export_smd(armature, [], action, path)

    def export_mesh(self, armature, objects, path):
        if self.mesh_type == 'SMD':
            self.export_smd(armature, objects, None, path)
        elif self.mesh_type == 'FBX':
            self.export_fbx(armature, objects, path)

    def export_smd(self, armature, objects, action, path):
        try:
            smd_file = path.open('w')
        except:
            self.report(f'Failed to export: {path}', exception=True)
        else:
            start = time.time()

            smd = SMD(self.prepend_armature, self.ignore_transforms)
            smd.from_blender(armature, objects, action)

            smd_file.write(smd.to_string())
            smd_file.close()

            log.info(f'Exported: {path} in {round(time.time() - start, 1)} seconds')

    def export_fbx(self, armature, objects, path):
        start = time.time()

        try:
            export_fbx(path, armature, objects, self.prepend_armature, self.ignore_transforms)
        except:
            self.report(f'Failed to export: {path}', exception=True)
        else:
            log.info(f'Exported: {path} in {round(time.time() - start, 1)} seconds')

    def get_all_objects(self, collection):
        return common.remove_duplicates(collection.all_objects) if collection else []

    def get_body_path(self, collection):
        name = common.clean_filename(collection.name)
        return self.directory.joinpath(f'{name}.{self.mesh_type}')

    def compile_qc(self):
        qc = self.directory.joinpath(f'{self.stem}.qc')
        if qc.is_file():
            log.info(f'Compiling: {qc}')
            self.ensure_models_folder()
            self.remove_models_old()

            # Use wine to run StudioMDL on Linux.
            # Run winepath to get a sure path

            fastbuild = '-fastbuild' if self.fastbuild else ''

            env = os.environ.copy()
            if (os.name == 'posix') and (self.studiomdl.suffix == '.exe'):
                cwd = self.game.parent
                args = [str(self.wine), common.winepath(self.studiomdl), '-nop4', '-fullcollide', fastbuild, '-game', common.winepath(self.game), common.winepath(qc)]
                env['WINEDEBUG'] = '-all'
            else:
                cwd = None
                args = [str(self.studiomdl), '-nop4', '-fullcollide', fastbuild, '-game', str(self.game), str(qc)]
            
            logfile = self.directory.joinpath(f'{self.stem}.log')

            with logfile.open('wb') as f:
                with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, env=env) as pipe:
                    l = getLogger('studiomdl')
                    for line in pipe.stdout:
                        f.write(line)
                        l.debug(line.decode('utf-8').rstrip())

            code = pipe.returncode

            if code == 0:
                self.move_files()
            else:
                return self.report(f'Failed to compile: {qc}')
        else:
            return self.report(f'Unable to find: {qc}')


    def export_materials(self):
        from ..material_export import material
        return material.export_materials(self)


    def open_folder(self):
        try:
            log.info(f'Opening: {self.directory}')
            self.directory.mkdir(exist_ok=True)
            bpy.ops.wm.path_open(filepath=str(self.directory))
        except:
            return self.report(f'Failed to open: {self.directory}', exception=True)
    
    def open_material_folder(self):
        relative_path = Path(self.material_folder_items[0].name)
        mat_folder = Path(self.materials / relative_path)
        try:
            log.info(f'Opening: {mat_folder}')
            mat_folder.mkdir(exist_ok=True)
            bpy.ops.wm.path_open(filepath=str(mat_folder))
        except:
            return self.report(f'Failed to open: {mat_folder}', exception=True)

    def view_model(self):
        model = self.models.joinpath(self.name)
        mdl = model.with_suffix('.mdl')
        dx90 = model.with_suffix('.dx90.vtx')

        # Use wine to run HLMV on Linux.
        # Run winepath to get a sure path

        env = os.environ.copy()

        if (os.name == 'posix') and (self.studiomdl.suffix == '.exe'):
            cwd = self.game.parent
            args = [str(self.wine), common.winepath(self.hlmv), '-game',
                    common.winepath(self.game), common.winepath(mdl)]
            env['WINEDEBUG'] = '-all'
        else:
            cwd = None
            args = [str(self.hlmv), '-game', str(self.game), str(mdl)]

        if dx90.is_file():
            log.info(f'Viewing: {mdl}')
            subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env)
        else:
            return self.report(f'Failed to view: {mdl}')

    def move_files(self):
        path_src = self.game.joinpath('models', self.name)
        path_dst = self.models.joinpath(self.name)

        if path_src == path_dst:
            return

        log.info(f'Moving to: {self.models}')
        common.verify_folder(path_dst.parent)

        for suffix in ('.dx90.vtx', '.dx80.vtx', '.sw.vtx', '.vvd', '.mdl', '.phy'):
            src = path_src.with_suffix(suffix)
            dst = path_dst.with_suffix(suffix)

            if src.exists():
                try:
                    log.info(f'Moving {src} > {dst}')
                    move(src, dst)
                except:
                    self.report(f'Failed to move {src} to {dst}', exception=True)
            else:
                log.warning(f'{src} Does not exist')

    def ensure_modelsrc_folder(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        self.directory.joinpath('anims').mkdir(parents=True, exist_ok=True)

    def remove_modelsrc_old(self):
        for file in self.directory.rglob('*'):
            if file.suffix in ('.SMD', '.FBX'):
                if file.is_file():
                    file.unlink()

    def ensure_models_folder(self):
        destination = self.models.joinpath(self.name).parent
        destination.mkdir(parents=True, exist_ok=True)

    def remove_models_old(self):
        model = self.models.joinpath(self.name)
        for suffix in ('.dx90.vtx', '.dx80.vtx', '.sw.vtx', '.vvd', '.mdl', '.phy'):
            path = model.with_suffix(suffix)
            if path.is_file():
                path.unlink()

    def report(self, message, exception=False):
        log.info(message)

        if exception:
            log.exception(exception)

        return message
