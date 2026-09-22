import logging
from . import common

NAME = common.get_name()
#FORMAT = "[%(name)s] | %(message)s"
FORMAT = "[%(name)s]: %(message)s"

try:
    from rich.logging import RichHandler
    print('Rich Found')
    
    logging.basicConfig(
        level=logging.DEBUG,
        format=FORMAT,
        handlers=[RichHandler(
            rich_tracebacks=True,
            show_time=False
            )
        ],
    )

except ImportError:
    logging.basicConfig(
        level=logging.DEBUG,
        format=FORMAT,
    )
    


log = logging.getLogger(NAME)
log.setLevel(logging.DEBUG)
log.debug('TEST')
log.debug(common.get_package_root())
log.setLevel(logging.INFO)

def setLevel(Level, logger=log):
    logger.setLevel(Level)

def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(log.getEffectiveLevel())
    return logger