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
        