#
# Logging
#
import logging

logger = logging.getLogger('labtronyx')

log_format = '%(asctime)s %(levelname)-8s %(module)s - %(message)s'
log_formatter = logging.Formatter(log_format)

# Default handler
logger.addHandler(logging.NullHandler())

def logConsole(logLevel=logging.DEBUG):
    logger.setLevel(logLevel)

    ch = logging.StreamHandler()
    ch.setLevel(logLevel)
    ch.setFormatter(log_formatter)
    logger.addHandler(ch)
    logger.info("Console logging enabled")

def logFile(filename, backupCount=1, logLevel=logging.DEBUG):
    logger.setLevel(logLevel)

    fh = logging.handlers.RotatingFileHandler(filename, backupCount)
    fh.setLevel(logLevel)
    fh.setFormatter(log_formatter)
    logger.addHandler(fh)
    fh.doRollover()


# Import modules into the labtronyx namespace
try:
    from . import version
    __version__ = version.ver_sem
except ImportError:
    version = object()
    __version__ = "unknown"

from .manager import InstrumentManager
from .remote import RemoteManager, RemoteResource
from .lab import LabManager
from . import bases
from . import common
from .common import errors

__all__ = ['InstrumentManager']
