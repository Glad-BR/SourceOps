import bpy
import time
import string
import shutil
import tomllib
import platform
import subprocess
import unicodedata

from pathlib import Path
from functools import cache, lru_cache

with open(Path(__file__).parent.parent.parent / 'blender_manifest.toml', 'rb') as f:
    manifest = tomllib.load(f)
    version = manifest['version']
    name = manifest['name']

def get_version():
    return version

def get_name():
    return name

@cache
def debug(context=bpy.context):
    prefs = get_prefs(context)
    return prefs.debug

@cache
def get_package_root():
    package_root = __package__.rpartition('.')[0] if '.' in __package__ else __package__
    if "bl_ext" in package_root:
        parts = package_root.split('.')
        package_root = ".".join(parts[:3])
    else:
        package_root = package_root.split('.')[0]
    return package_root


def get_prefs(context):
    package_root = get_package_root()
    try:
        return context.preferences.addons[package_root].preferences
    except KeyError:
        from .logger import log
        log.exception(f"Extension preferences key '{package_root}' not found.")
        return None


def get_game(prefs):
    try:
        return prefs.game_items[prefs.game_index]
    except:
        return None


def get_globals(context):
    try:
        return context.scene.sourceops
    except:
        return None


def get_model(sourceops):
    try:
        return sourceops.model_items[sourceops.model_index]
    except:
        return None


def get_bodygroups(model):
    try:
        return model.bodygroups_items[model.bodygroups_index]
    except:
        return None
def get_sub_bodygroups(bodygroups):
    try:
        return bodygroups.sublist_items[bodygroups.sublist_index]
    except:
        return None


def get_lods(model):
    try:
        return model.lods_items[model.lods_index]
    except:
        return None
def get_sub_lods(lods):
    try:
        return lods.replacemodel_items[lods.replacemodel_index]
    except:
        return None


def get_material_folder(model):
    try:
        return model.material_folder_items[model.material_folder_index]
    except:
        return None


def get_material(model):
    try: 
        return model.materials_items[model.materials_index]
    except:
        return None


def get_skin(model):
    try:
        return model.skin_items[model.skin_index]
    except:
        return None


def get_sequence(model):
    try:
        return model.sequence_items[model.seqvectoruence_index]
    except:
        return None


def get_event(sequence):
    try:
        return sequence.event_items[sequence.event_index]
    except:
        return None


def get_attachment(model):
    try:
        return model.attachment_items[model.attachment_index]
    except:
        return None

def get_particle(model):
    try:
        return model.particle_items[model.particle_index]
    except:
        return None

def get_map(sourceops):
    try:
        return sourceops.map_items[sourceops.map_index]
    except:
        return None


def split_column(layout):
    col = layout.column()
    col.use_property_split = True
    col.use_property_decorate = False
    return col

def align_column(layout):
    col = layout.column(align=True)
    col.use_property_split = True
    col.use_property_decorate = False
    return col

def center_label(layout, text:str):
    r = layout.row()
    r.alignment = 'CENTER'
    r.label(text=text)

filename_chars_valid = '-_.() %s%s' % (string.ascii_letters, string.digits)
filename_chars_replace = ' '
filename_char_limit = 255

@cache
def clean_filename(filename, whitelist=filename_chars_valid, replace=filename_chars_replace, char_limit=filename_char_limit):
    for r in replace:
        filename = filename.replace(r, '_')
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    return cleaned_filename[:char_limit]

def verify_folder(path:Path) -> Path:
    if not path.is_dir():
        try:
            path.mkdir(parents=True, exist_ok=True)
        except:
            from .logger import log
            log.exception(f'Failed to create directory: {path}')
            #print(f'Failed to create directory: {path}')
            #traceback.print_exc()
    return path


def remove_duplicates(list_with_duplicates):
    return list(dict.fromkeys(list(list_with_duplicates)))

@cache
def documents():
    if platform.system() == 'Windows':
        import ctypes.wintypes
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)

        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 1, buf)
        return Path(buf.value)

    else:
        return Path.home()

@cache
def appdata():
    user = bpy.utils.resource_path('USER')
    return Path(user).resolve()

@cache
def temp() -> Path:
    t = bpy.context.preferences.filepaths.temporary_directory
    tmp = Path(t if t else bpy.app.tempdir)
    return tmp.resolve()

@cache
def resolve(path) -> Path:
    if path:
        return str(Path(bpy.path.abspath(path)).resolve())
    else:
        return ''


def update_wine(self, context):
    self['wine'] = resolve(self.wine)

@cache
def get_wine(self) -> Path:
    wine = Path(self.wine)
    which_path = shutil.which('wine')
    which = Path(which_path) if which_path is not None else None

    if wine.is_file():
        return Path(wine)
    elif which is not None and which.is_file():
        return Path(which)
    else:
        raise Exception('Wine executable not found. Make sure Wine is installed and accessible by Blender')

@cache
def winepath(path: Path | str) -> str:
    start_t = time.perf_counter()

    from .logger import log

    cmd = ['winepath', '-w', str(path)]

    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.DEVNULL, 
            text=True
        )
        windows_path = process.stdout.readline().strip()
        log.debug(windows_path)

        process.terminate()
        log.debug(f"winepath took {time.perf_counter() - start_t:.4f} seconds {windows_path}")

        return windows_path
    except Exception as e:
        log.exception(f"Error running winepath: {e}")
        return str(path)


def serialize_obj(obj):
    data = {}
    for item in dir(obj):
        if item.startswith('_') or callable(getattr(obj, item)):
            continue
            
        val = getattr(obj, item)
        if type(val).__module__ != 'builtins' and hasattr(val, 'value'):
            val = val.value
            
        data[item] = val
    return data