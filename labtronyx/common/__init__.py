import socket
import importlib
import logging
import os
import sys

def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
        
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
            
        except socket.error:
            return False
        
    except socket.error:  # not a valid address
        return False

    return True

def is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
        
    except socket.error:  # not a valid address
        return False
    
    return True

def resolve_hostname(hostname):
    return socket.gethostbyname(hostname)

            
class ICF_Common(object):
    """
    ICF_Common provides a uniform base of functions for objects in the 
    Instrument Control Model-View-Controller framework
    
    Dynamically import configuration files given a filename
    
    Configuration:
    - Accessing configuration information
    >>> self.config.<attribute>
    
    """

    loggerName = "InstrumentControl"
    loggerOverride = None
    
    logger = None
    config = None
    
    def __init__(self):
        # Get the root path
        can_path = os.path.dirname(os.path.realpath(os.path.join(__file__, os.pardir)))
        self.rootPath = os.path.abspath(can_path) # Resolves symbolic links
        
        if not self.rootPath in sys.path:
            sys.path.append(self.rootPath)
        
        if self.config is None:
            self.loadConfig('default')
            
        if self.logger is None:
            self.configureLogger()
            
    def getRootPath(self):
        return self.rootPath
        
    #===========================================================================
    # Config
    #===========================================================================
    
    def loadConfig(self, configFile):
        
        try:
            cFile = importlib.import_module('config.%s' % configFile)
            self.config = cFile.Config()
            
        except Exception as e:
            print("FATAL ERROR: Unable to import config file")
            sys.exit()
        
    def getConfig(self):
        return self.config
        
    #===========================================================================
    # Logger
    #===========================================================================
        
    def setLogger(self, new_logger):
        self.logger = new_logger
        
    def getLogger(self):
        return self.logger
    
    def configureLogger(self):
        self.logger = logging.getLogger(__name__)
        formatter = logging.Formatter(self.config.logFormat)
                
         # Configure logging level
        self.logger.setLevel(self.config.logLevel_console)
            
        # Logging Handler configuration, only done once
        if self.logger.handlers == []:
            # Console Log Handler
            lh_console = logging.StreamHandler(sys.stdout)
            lh_console.setFormatter(formatter)
            lh_console.setLevel(self.config.logLevel_console)
            self.logger.addHandler(lh_console)
            
            # File Log Handler
            if self.config.logToFile:
                if not os.path.exists(self.config.logPath):
                    os.makedirs(self.config.logPath)
                
                self.logFilename = os.path.normpath(os.path.join(self.config.logPath, 'InstrControl_Manager.log'))
                #===============================================================
                # if self.config.logFilename == None:
                #     self.logFilename = os.path.normpath(os.path.join(self.config.logPath, 'InstrControl_Manager.log'))
                # else:
                #     self.logFilename = os.path.normpath(os.path.join(self.config.logPath, self.config.logFilename))
                #===============================================================
                try:
                    fh = logging.handlers.RotatingFileHandler(self.logFilename, backupCount=self.config.logBackups)
                    fh.setLevel(self.config.logLevel_file)
                    fh.setFormatter(formatter)
                    self.logger.addHandler(fh)  
                    fh.doRollover()
                except Exception as e:
                    self.logger.error("Unable to open log file for writing: %s", str(e))