import socket
import logging

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

            
class IC_Common(object):
    """
    IC_Common provides a uniform base of functions for objects in the Instrument Control Model-View-Controller framework
    
    Dynamically import configuration files given a filename
    
    Configuration:
    - Accessing configuration information
    >>> self.config.<attribute>
    
    """

    # Dictionary of instantiated devices with serial number as the key
    devices = {}
    
    loggerName = "InstrumentControl"
    loggerOverride = None
    
    def __init__(self, **kwargs):
        if 'logger' in kwargs:
            self.logger = kwargs['logger']
        else:
            # Create a generic logger
            self.logger = logging
        
        try:
            import config
            self.config = config.Config()
            
        except:
            pass
