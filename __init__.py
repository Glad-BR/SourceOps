from . import dependency_setup

bl_info = {
    'name': 'SourceOps',
    'author': 'bonjorno7, Almaas, Cabbage McGravel, CryptAlchemy, Gorange, Krystian, RED_EYE, SethTooQuick, Yonder, Blueberry_pie, Glad_BR',
    'description': 'A more convenient alternative to Blender Source Tools',
    'blender': (2, 83, 0),
    'version': (0, 8, 0),
    'location': '3D View > Sidebar',
    'category': 'Import-Export',
}

dependency_setup.run()

from . import addon

def register():
    addon.register()


def unregister():
    addon.unregister()
