"""
Labtronyx Project

:author: Kevin Kennedy
"""
import logging
import sys

# Logging
logger = logging.getLogger('labtronyx')

log_format = '%(asctime)s %(levelname)-8s %(name)s - %(message)s'
log_formatter = logging.Formatter(log_format)

# Default handler
logger.addHandler(logging.NullHandler())

# Import modules into the labtronyx namespace
try:
    from . import version
    __version__ = version.ver_sem
except ImportError:
    version = object()
    __version__ = "unknown"

# Import exceptions
from . import common
from .common import errors, events, plugin
from .common.errors import *

from .manager import InstrumentManager
from .remote import RemoteManager, RemoteResource

from .bases import *

from .cli import main


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


def runScriptMain():
    """
    Bootstrap helper function to run a Labtronyx Script when invoked interactively from the command line. An
    InstrumentManager object is automatically instantiated and passed to a valid script object is located in the
    `__main__` module.
    """
    logConsole(logging.INFO)
    manager = InstrumentManager()

    plugin_manager = common.plugin.PluginManager()
    main_plugins = plugin_manager.extractPlugins(sys.modules['__main__'])

    main_scripts = [p_cls for p_cls in main_plugins.values() if issubclass(p_cls, ScriptBase) and p_cls != ScriptBase]

    if len(main_scripts) == 0:
        raise EnvironmentError("No scripts found")

    elif len(main_scripts) > 1:
        raise EnvironmentError("More than one script object found, unable to choose")

    else:
        from bases.script import ScriptResult
        script_cls = main_scripts[0]
        script_obj = script_cls(manager, logger=logger)

        script_result = script_obj.start()
        if script_result.result == ScriptResult.PASS:
            sys.exit(0)
        else:
            sys.exit(-1)