import logging

NAME = 'SourceOps++'

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


def getLogger(name):
    return logging.getLogger(name)