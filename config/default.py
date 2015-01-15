import logging
import sys

class Config(object):
    
    def __init__(self):
        # Version
        self.version = '150114'
        
        #
        #  Logging
        #
        
        # Format
        self.logFormat = '%(asctime)s %(levelname)-8s %(module)s - %(message)s'
        #self.logFormat = '%(asctime)s  %(levelname)-8s %(module)-25s %(message)s'
        
        # Log to file
        self.logToFile = True
        self.logFilename = 'InstrControl.log'
        self.logBackups = 1
        
        if sys.platform.startswith('win'):
            self.logPath = 'C:/temp/'
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            self.logPath = '/var/log/' # User directory
        elif sys.platform.startswith('darwin'):
            self.logPath = '/var/log' # User directory
        else:
            raise EnvironmentError('Unsupported platform')
        
        # Log levels
        self.logLevel_console = logging.DEBUG
        self.logLevel_file = logging.INFO
        
        # System Paths
        self.paths = {"controllers": "controllers",
                      "models": "models",
                      "views": "views"}
        
        # Default port for manager objects to setup RPC servers on
        self.managerPort = 6780
        
        # SVN
        #self.svn_rev = '$Revision: $'

        # UPEL Controller Config
        self.broadcastIP = '192.168.1.255'
        self.UPELPort = 7968
        