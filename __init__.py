
bl_info = {
    'name': 'SourceOps',
    'author': 'bonjorno7, Almaas, Cabbage McGravel, CryptAlchemy, Gorange, Krystian, RED_EYE, SethTooQuick, Yonder, Blueberry_pie, Glad_BR',
    'description': 'A more convenient alternative to Blender Source Tools',
    'blender': (2, 83, 0),
    'version': (0, 8, 0),
    'location': '3D View > Sidebar',
    'category': 'Import-Export',
}

import sys
print(f'Starting {bl_info['name']} Version {bl_info["version"]}')
print(f'GIL:{sys._is_gil_enabled()}')

from . import dependency
dependency.register()

from . import addon

def register():
    addon.register()


def unregister():
    addon.unregister()
