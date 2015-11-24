"""
Labtronyx Project

:author: Kevin Kennedy
"""
from __future__ import absolute_import
import logging
import logging.handlers
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
from .common import *

from .manager import InstrumentManager
from .remote import RemoteManager, RemoteResource

from .bases import *
from . import gui


def logConsole(logLevel=logging.DEBUG):
    logger = logging.getLogger('labtronyx')
    logger.setLevel(logLevel)

    ch = logging.StreamHandler()
    ch.setLevel(logLevel)
    ch.setFormatter(log_formatter)
    logger.addHandler(ch)
    logger.info("Console logging enabled")


def logFile(filename, backupCount=1, logLevel=logging.DEBUG):
    logger = logging.getLogger('labtronyx')
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
    instr_manager = InstrumentManager()

    plugin_manager = instr_manager.plugin_manager
    main_plugins = plugin_manager.extractPlugins(sys.modules['__main__'])

    main_scripts = [p_cls for p_cls in main_plugins.values() if issubclass(p_cls, ScriptBase) and p_cls != ScriptBase]

    if len(main_scripts) == 0:
        raise EnvironmentError("No scripts found")

    elif len(main_scripts) > 1:
        raise EnvironmentError("More than one script object found, unable to choose")

    else:
        import argparse

        script_cls = main_scripts[0]
        script_attrs = script_cls.getClassAttributes()
        script_params = script_cls.getParameterInfo()

        # Build CLI argument parser
        parser = argparse.ArgumentParser(description=script_attrs.get('description'))
        for param_attr, param_info in script_params.items():
            parser.add_argument("--" + param_attr,
                required=param_info.get('required', False),
                help=param_info.get('description')
            )
        args = parser.parse_args()

        cli_params = {p_attr: getattr(args, p_attr) for p_attr in script_params}

        script_obj = script_cls(instr_manager, logger=logger, **cli_params)
        script_obj.start()
        script_obj.join()

        script_result = script_obj.current_test_result

        if script_result.result == ScriptResult.PASS:
            sys.exit(0)
        else:
            sys.exit(-1)