import threading
import socket
import errno
import select
import re
import uuid
import logging
from datetime import datetime

from jsonrpc import *
from server import *
from client import *
from errors import *

#__all__ = ['client', 'server', 'errors']
      
class RpcBase(object):
    """
    RpcBase provides helper functions to facilitate RPC operation. A server will 
    check if the target class inherits this base class to ensure that certain 
    functions will be available
    
    Each instantiation of an RpcBase object will generate a UUID to identify it
    to RPC Clients
    """
    
    def __init__(self):
        
        self.uuid = str(uuid.uuid1())
        
        self.rpc_thread = None
    
        self.rpc_running = threading.Event()
        self.rpc_lock = threading.Lock()
        self.rpc_startTime = datetime.now()

    def rpc_test(self, connection=None, port=None):
        """
        Tests if a port on the RpcServer host is being used.
        
        :param port: Port to test
        :type port: int
        :returns: bool - True if the port is being used, False if it is free
        """
        if port is not None:
            try:
                ts = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ts.connect(('localhost', port))
            
            
            except socket.error as e:
                if e.errno == errno.ECONNREFUSED: #10061 or e.errno == 111 or e.errno == 61: # Refused connection
                    return False
                
                elif e.errno == errno.ECONNRESET: #10054: # Connection reset
                    return False
                
                elif e.errno == errno.ETIMEDOUT: #10060: # Time out
                    return False
                
                else:
                    # Something else is wrong, assume port cannot be used
                    return True
            
            finally:
                ts.close()
                
            # If no exception was thrown, connection was successful and port is in use
            return True
        
        else:
            # No port was provided to check
            return False
    
    def rpc_start(self, connection=None, port=None):
        """
        Spawns an RpcServer thread to handle connections on the given port.
        
        :param port: Port to bind
        :type port: int
        :returns: bool - True if the RpcServer starts successfully, False otherwise
        """
        if not isinstance(self.rpc_thread, RpcServer):
            self.rpc_thread = RpcServer(target=self, port=port)
            
            if hasattr(self, 'logger'):
                self.rpc_thread.attachLogger(self.logger)
            
            self.rpc_thread.start()
            
            self.rpc_running.set()
            self.rpc_startTime = datetime.now()
        
            # Wait for thread to come alive
            self.rpc_thread.alive.wait(2.0)
            
        return self.rpc_thread.alive.is_set()
   
    
    def getPort(self):
        """
        Get the port that is bound by the RpcServer
        """
        return self.socket.getsockname()[1]
        