import threading
import socket
import select
import logging
import errno

from jsonrpc import *
from errors import *

class RpcClient(object):
    """
    Flexible RPC client that connects to an RpcServer instance either on a local
    host or remote host. Abstracts a remote object using the magic of Python.
    By utilizing functions from the remote RpcServer and object that extends
    RpcBase, RpcClient can dynamically create method aliases. In this way, a
    RpcClient object can "become" an instance of an object on a remote host.
    
    .. note::
        If the remote RPC server does not extend RpcBase, then it will be 
        impossible to create aliases for remote functions. An alias method can 
        be created manually using RpcClient._methodAlias()
    
    To manually call a remote method, use the function RpcClient._rpcCall
    
    TODO: Add batch processing
    
    :param address: IP Address of remote RpcServer (Defaults to 'localhost')
    :type address: str - IPv4
    :param port: Port of remote RpcServer
    :type port: int
    """
    
    RPC_TIMEOUT = 10.0
    RPC_MAX_PACKET_SIZE = 1048576 # 1MB
    
    def __init__(self, address, port, **kwargs):
        
        self.address = self._resolveAddress(address)
        self.port = port
        self.logger = kwargs.get('logger', logging)
        self.timeout = self.RPC_TIMEOUT
        self.nextID = 1
            
        # Update the hostname
        self.hostname = self._rpcCall('rpc_getHostname')
            
        self._refresh()
            
        self._setTimeout() # Default
        
    def _resolveAddress(self, address):
        try:
            socket.inet_aton(address)
            return address
            #self.hostname, _ = socket.gethostbyaddr(address)
        except socket.error:
            # Assume a hostname was given
            #self.hostname = address
            return socket.gethostbyname(address)
        
    def _refresh(self):
        """
        Get a list of methods from the RPC server and dynamically fill the
        object
        """
        # Request a list of methods
        self._setTimeout(2.0)
        self.methods = self._rpcCall('rpc_getMethods')
        
        for proc in self.methods:
            self._methodAlias(proc)
            
    def _setTimeout(self, new_to=None):
        """
        Set the Timeout limit for an RPC Method call
        
        :param new_to: New Timeout time in seconds
        :type new_to: float
        """
        if new_to is not None:
            self.timeout = float(new_to)
        else:
            self.timeout = self.RPC_TIMEOUT
        
            
    def _getHostname(self):
        return self.hostname
    
    def _getAddress(self):
        return self.address
    
    def _ready(self):
        return self.ready
    
    def _close(self):
        pass
    
    def _rpcCall(self, remote_method, *args, **kwargs):
        """
        Calls a function on the remote host with both positional and keyword
        arguments
        
        Returns:
            - Whatever the remote function returns
            
        Exceptions:
            - AttributeError when method not found (same as if a local call)
            - RuntimeError when the remote host sent back a server error
            - Rpc_Timeout when the request times out
        """
        try:
            # Open a socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.address, self.port))
            self.socket.setblocking(0)
            self.socket.settimeout(self.timeout)
            
            # Encode the RPC Request
            nextID = int(self.nextID + 1)
            packet = JsonRpcPacket()
            packet.addRequest(nextID, remote_method, *args, **kwargs)
            
            # Send the encoded request
            out_str = packet.export()
            self.socket.send(out_str)
            
            # Wait for return data or timeout
            ready_to_read, _, _ = select.select([self.socket], [], [], self.timeout)
            if self.socket in ready_to_read:
                data = self.socket.recv(self.RPC_MAX_PACKET_SIZE)
                
                if data:
                    packet = JsonRpcPacket(data)
                    errors = packet.getErrors()
                    responses = packet.getResponses()
                    
                    if len(errors) > 0:
                        # There is a problem if there are more than one errors,
                        # so just check the first one
                        err_obj = JsonRpc_to_RpcErrors.get(type(errors[0]), RpcError)
                        raise err_obj()
                    
                    elif len(responses) == 1:
                        resp = responses[0]
                        return resp.getResult()
                
                    else:
                        raise RpcInvalidPacket()
                    
            else:
                raise RpcTimeout()
            
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                raise RpcServerNotFound()
            
            elif e.errno == errno.ECONNRESET: #10054: # Connection reset
                raise RpcServerNotFound()
                
            elif e.errno == errno.ETIMEDOUT: #10060: # Time out
                raise RpcServerNotFound()
            
            else:
                raise
        
        finally:
            self.socket.close()

    def _methodAlias(self, methodName):
        """
        Dynamically create a method internal to the RpcClient object that will
        invoke an RPC method call when called.
        
        :param methodName: Name of method
        :type methodName: str
        """
        dynFunc = lambda *args, **kwargs: self._rpcCall(methodName, *args, **kwargs)
        setattr(self, methodName, dynFunc)
    
    def __str__(self):
        return '<RPC Instance of %s:%s>' % (self.address, self.port)