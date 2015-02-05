import socket

from jsonrpc import *

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
    
    :param address: IP Address of remote RpcServer (Defaults to 'localhost')
    :type address: str - IPv4
    :param port: Port of remote RpcServer
    :type port: int
    """
    
    RPC_TIMEOUT = 10.0
    RPC_MAX_PACKET_SIZE = 1048576 # 1MB
    
    def __init__(self, **kwargs):
        
        if 'port' in kwargs:
            self.port = int(kwargs['port'])
            if 'address' in kwargs:
                try:
                    socket.inet_aton(kwargs['address'])
                    self.address = kwargs['address']
                    self.hostname = socket.gethostbyaddr(self.address)[0]
                except socket.error:
                    # Assume a hostname was given
                    self.hostname = kwargs['address']
                    self.address = socket.gethostbyname(self.hostname)
            else:
                # Loopback mode
                self.address = '127.0.0.1' 
                self.hostname = socket.gethostname()
                 
        else:
            raise RuntimeError('RpcClient must be provided a port')
        
        # Protocol aliases
        self.__rpcDecode__ = Rpc_decode
        self.__rpcEncode__ = Rpc_encode
        
        self.nextID = self.__rpcNextID()
        
        # Try to open a socket
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._setTimeout(1.0) # Short timeout on first connection
            self.socket.connect((self.address, self.port))
            self.socket.setblocking(0)
            
            self.ready = True
            
        except socket.error as e:
            self.socket.close()
            
            self.ready = False
            
        # Request a list of methods, an error here is acceptable if the remote
        # host does not inherit RpcBase
        if self.ready is True:
            try:
                self._setTimeout(2.0)
                self.methods = self._rpcCall('rpc_getMethods')
                
                for proc in self.methods:
                    self._methodAlias(proc)
                    
                # Update the hostname
                self.hostname = self._rpcCall('rpc_getHostname')
                    
            except Exception as e:
                pass
            
        self._setTimeout() # Default
            
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
        self.socket.settimeout(self.timeout)
            
    def _getHostname(self):
        return self.hostname
    
    def _getAddress(self):
        return self.address
    
    def _ready(self):
        return self.ready
    
    def _close(self):
        self.socket.close()
    
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
        nextID = self.nextID.next()
        request = [Rpc_Request(method=remote_method, params=args, kwargs=kwargs, id=nextID)]
        
        out_str = self.__rpcEncode__(request)
        self.socket.send(out_str)
        
        # Wait for return data or timeout
        ready = select.select([self.socket], [], [], self.timeout)
        if ready[0]:
            data = self.socket.recv(self.RPC_MAX_PACKET_SIZE)
            
            _, response = self.__rpcDecode__(data)
            if len(response) == 1 and isinstance(response[0], Rpc_Response):
                response = response[0]
                if response.isError():
                    error = response.getError()
                    raise error
            
                else:
                    return response.result
                
        else:
            raise Rpc_Timeout()
        
    def __rpcNextID(self):
        nextID = 1
        while True:
            yield int(nextID)
            nextID += 1

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
    
    def __del__(self):
        try:
            self.socket.close()
        except:
            pass