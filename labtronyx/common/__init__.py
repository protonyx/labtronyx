import socket

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

import constants
import errors
import events

__all__ = ['constants', 'errors', 'events', 'plugin']