from . import utils
from . import props
from . import types
from . import ops
from . import icons
from . import ui

def post_init():
    # Post Load
    from . import utils
    import bpy
    import logging

    debug = bpy.context.preferences.addons[utils.common.get_package_root()].preferences.debug
    utils.logger.log.info( f'Debug Mode:{debug}' )

    if debug:
        utils.logger.setLevel(logging.DEBUG)

def register():
    props.register()
    ops.register()
    icons.register()
    ui.register()

    post_init()


def unregister():
    ui.unregister()
    icons.unregister()
    ops.unregister()
    props.unregister()