import logging
import sys
import time

class Config(object):
    # Software Branding
    name = 'Labtronyx'
    longname = 'Labtronyx Instrumentation Control Framework'
    
    # Version
    version = '0.1'
    build = '150401' # time.strftime("%y%m%d")
    stage = 'dev'
    
    # Default port for manager objects to setup RPC servers on
    managerPort = 6780
    
    #
    #  Logging
    #
    
    # Format
    logFormat = '%(asctime)s %(levelname)-8s %(module)s - %(message)s'
    #logFormat = '%(asctime)s  %(levelname)-8s %(module)-25s %(message)s'
    
    # Log to file
    logToFile = True
    logFilename = 'Labtronyx.log'
    logBackups = 1
    
    if sys.platform.startswith('win'):
        logPath = 'C:/temp/'
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        logPath = '/var/log/' # User directory
    elif sys.platform.startswith('darwin'):
        logPath = '/Library/logs/' # User directory
    else:
        raise EnvironmentError('Unsupported platform')
    
    # Log levels
    logLevel_console = logging.DEBUG
    logLevel_file = logging.INFO

        