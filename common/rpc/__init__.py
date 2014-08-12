import threading
import socket
import select
import re
import uuid
import logging
from datetime import datetime

import jsonrpc

class RpcServer(threading.Thread):
    """
    Flexible RPC server that runs in a Python thread. Wraps any Python object
    and allows remote machines to call functions and receive returned data.
    
    :param Logger: Logger instance if you wish to override the internal instance
    :type Logger: Logging.logger
    :param target: Target object
    :type target: object
    :param port: Port to attach socket to
    :type port: int 
    
    .. note::

        Method calls to functions that begin with an underscore are considered 
        protected and will no be invoked
    
    .. note::
    
        If an RPC call begins with rpc, the function will only be called if the
        target object extends RpcBase. These functions are considered reserved.
        If a target object does not extend RpcBase, the RpcServer will not 
        allow use of these reserved functions, even if they are defined in the
        target class.
    """
    
    # Exclusive access times out after 60 seconds
    EXCLUSIVE_TIMEOUT = 60.0
    
    def __init__(self, **kwargs):
        threading.Thread.__init__(self)
        
        self.alive = threading.Event()
        
        if 'target' in kwargs:
            self.target = kwargs['target']
            self.name = 'RPC-Server-' + self.target.__class__.__name__
        else:
            raise RuntimeError('RPC Server must be provided a target object')
        
        if 'port' in kwargs and kwargs['port'] != None:
            self.port = int(kwargs['port'])
        else:
            # Auto-assign the port to a free port
            self.port = 0

        # RPC Client Synchronization lock
        self.lock = threading.Lock()

        # Socket management
        self.connections = []
        self.exclusive = None
        self.exclusiveTime = None
        
    def start(self):
        """
        Start the RPC Server Thread. 
        """
        threading.Thread.start(self)
        
    def run(self):
        # Start socket
        # TODO: Should this be off-loaded to the RPC Protocol API?
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('',self.port))
        self.socket.listen(5)
        
        self.port = self.socket.getsockname()[1]
        
        if hasattr(self, 'logger'):
            self.logger.debug('[%s] listening on port %i', self.name, self.port)
            self.logger.debug("[%s] Hostname: %s", self.name, socket.gethostname())
            
        self.alive.set()

        while self.alive.isSet():
            try:
                # Spawn a new thread to service the connection
                connection, address = self.socket.accept()
                # Spawn a new thread to service the connection
                connThread = RpcConnection(parent=self, address=address, socket=connection)
                # Give the name a meaningful name
                connThread.name = 'RPC-Conn-' + self.target.__class__.__name__ + connThread.name
                
                if hasattr(self, 'logger'):
                    connThread.attachLogger(self.logger)
                connThread.start()
                self.connections.append(connThread)
                
            except socket.error:
                # The socket probably closed, if so alive will be cleared
                continue
            
            except:
                if hasattr(self, 'logger'):
                    self.logger.exception('There was an exception raised while handling a connection request')
                    break
                else:
                    raise
                
        self.socket.close()
        
        if hasattr(self, 'logger'):
            self.logger.debug('[%s] RPC Server thread stopped', self.name)
            
    def getPort(self):
        """
        Get the port that is bound by the RpcServer
        """
        return self.socket.getsockname()[1]
        
    def stop(self):
        """
        Close all connections and stop the RpcServer thread
        """
        # Close all connections
        for socket in self.connections:
            socket.join()
            
        self.socket.close()
        self.alive.clear()
        
    def attachLogger(self, loggerObj):
        """
        Attach a logging.Logger instance for the RpcServer to use.
        
        :param loggerObj: Logger instance if you wish to override the internal instance
        :type loggerObj: Logging.logger
        """
        if isinstance(loggerObj, logging.Logger):
            self.logger = loggerObj
      
class RpcBase(object):
    """
    RpcBase provides helper functions to facilitate RPC operation. A server will 
    check if the target class inherits this base class to ensure that certain 
    functions will be available
    
    Each instantiation of an RpcBase object will generate a UUID to identify it
    to RPC Clients
    """
    rpc_thread = None
    exclusive = None
    exclusiveTime = None
    
    __identity = 'JSON-RPC/2.0'
        
    def __init__(self):
        self.exclusive = None
        self.exclusiveTime = None
        self.uuid = str(uuid.uuid1())
        
    def _setHELOResponse(self, response):
        self.__identity = response
        
    def _getHELOResponse(self):
        return self.__identity
        
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
                if e.errno == 10061: # Refused connection
                    return False
                elif e.errno == 10054: # Connection reset
                    return False
                elif e.errno == 10060: # Time out
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
            self.rpc_startTime = datetime.now()
        
            # Wait for thread to come alive
            self.rpc_thread.alive.wait(2.0)
            
        return self.rpc_thread.alive.is_set()
        
    def rpc_stop(self, connection=None):
        """
        Stops a running RpcServer thread.
        """
        if isinstance(self.rpc_thread, RpcServer):
            self.rpc_thread.join()
            self.rpc_thread = None
            
    def rpc_restart(self, connection=None):
        """
        Stops and restarts a running RpcServer thread
        """
        self.rpc_stop()
        self.rpc_start()
        
    def rpc_uptime(self, connection=None):
        """
        Get the uptime of the RpcServer
        
        :returns: int - uptime in seconds
        """
        if hasattr(self, 'rpc_startTime'):
            delta = self.rpc_startTime - datetime.now()
            return delta.total_seconds()
        else:
            return 0
        
    def rpc_getPort(self, connection=None):
        """
        Get the bound port of a running RpcServer thread.
        
        :returns: int - Port
        """
        if isinstance(self.rpc_thread, RpcServer) and self.rpc_thread.alive.is_set():
            return self.rpc_thread.getPort()
        
        else:
            return None
        
    def rpc_isRunning(self, connection=None):
        """
        Check if there is an RpcServer thread running
        
        :returns: bool - True if running, False if not running
        """
        if isinstance(self.rpc_thread, RpcServer):
            return self.rpc_thread.alive.is_set()
        
        else:
            return False
    
    def rpc_getConnections(self, connection=None):
        # TODO
        pass
    
    def rpc_getMethods(self, connection):
        """
        Get a list of methods in the target object. Used by RpcClient to populate
        remote objects.
        
        :returns: list of strings
        """
        import inspect
        
        validMethods = []
        
        # Create a list of methods that can be called
        target_members = inspect.getmembers(self)
        
        for member in target_members:
            if inspect.ismethod(member[1]) and member[0][0] != '_':
                validMethods.append(member[0])
                
        return validMethods
    
    def rpc_getUUID(self, connection=None):
        """
        Get the RpcServer UUID
        
        :returns: str - RpcServer UUID
        """
        return str(self.uuid)
    
    def rpc_requestExclusiveAccess(self, connection):
        """
        Request exclusive access to the target object from the RPC interface. 
        This acts as a lock on the target object, and no other connections can
        call functions. 
        
        .. note::
        
            Exclusive Access locks expire after 60 seconds, and must be renewed
            by another call to :func:`RpcBase.rpc_requestExclusiveAccess`
            
        :returns: bool - True if exclusive lock granted, False if denied
        """
        if self.rpc_hasAccess(connection):
            # No other connection has exclusive access, or previous owner did not renew exclusive lock
            self.exclusive = connection
            self.exclusiveTime = datetime.now()
            
            self.logger.debug('[%s, %s] Requested exclusive access', self.name, connection.address)
            
            return True

        else:
            return False
            
    def rpc_releaseExclusiveAccess(self, connection):
        """
        Release exclusive access. If a connection does not have exclusive access,
        this function does nothing.
        
        .. note::
        
            This function does not have to be called explicitly, the lock
            will expire automatically after 60 seconds.
            
        :returns: bool - True if lock released, False otherwise
        """
        if isinstance(self.exclusive, RpcConnection) and self.exclusive == connection:
            self.exclusive = None
              
            self.logger.debug('[%s, %s] Released exclusive access', self.name, connection.address)
              
            return True
          
        else:
            return False
              
    def rpc_hasExclusiveAccess(self, connection):
        """
        Check if the requesting connection has exclusive access.
        
        :returns: bool - True if requesting connection has exclusive access, False otherwise
        """
        if isinstance(self.exclusive, RpcConnection) and self.exclusive == connection and timedelta(seconds=self.EXCLUSIVE_TIMEOUT) < (datetime.now() - self.exclusiveTime):
            return True
        
        else:
            return False
        
    def rpc_whoHasExclusiveAccess(self, connection):
        # TODO
        pass
    
    def rpc_hasAccess(self, connection):
        if self.exclusive == None or (isinstance(self.exclusive, RpcConnection) and timedelta(seconds=self.EXCLUSIVE_TIMEOUT) < (datetime.now() - self.exclusiveTime)):
            return True
        
        else:
            return False
        
    def rpc_getHostname(self, connection):
        """
        Get the hostname of the RpcServer host.
        
        :returns: str - hostname
        """
        hostname = socket.gethostname()
        return hostname
      
    def rpc_getObjectName(self, connection):
        """
        Get the name of the object that may be extending RpcBase.
        
        :returns: str - Object name
        """
        return self.__class__.__name__
    
class RpcConnection(threading.Thread):
    """
    Receives and processes RPC requests from remote connections (or local ones)
    
    Before any requests can be processed, the thread must acquire a lock to synchronize access
    to the shared resource (model object)
    
    Remote users can request exclusive access, but must renew the lock every 60 seconds or other users will be
    allowed to request access
    
    Any method that begins with an underscore is considered protected and will be invalidated by the RPC server

    
    """
    
    def __init__(self, **kwargs):
        threading.Thread.__init__(self)
        
        self.parent = kwargs['parent']
        
        self.address = kwargs['address'][0]
        self.port = kwargs['address'][1]
        
        self.socket = kwargs['socket']
        
        self.lock = self.parent.lock
        #self.name = self.parent.name
        
        # Hardcode JSON RPC for now
        self.rpc_decode = jsonrpc.decode
        self.rpc_encode = jsonrpc.encode
        
        # Socket management
        self.alive = threading.Event()
        self.alive.set()
    
    def run(self):
        
        if hasattr(self, 'logger'):
            self.logger.debug('[%s, %s] Connection established', self.name, self.address)
        
        while self.alive.isSet():
            # Check for incoming data
            try:
                data = self.socket.recv(4096)
                
                if type(data) is str and data[0:4] == 'HELO':
                    self.socket.send(self.parent.target._getHELOResponse())
                    
                elif data:
                    # Process the incoming data as a JSON RPC packet
                    try:
                        request, _ = self.rpc_decode(data)
                    except Rpc_Error as e:
                        request = e
                        
                    # self.logger.debug('RX: %s', data)
                        
                    result = []
                    target = self.parent.target
                    
                    if type(request) == list and len(request) > 0:
                        # Iterate through each request, verify access criteria
                        for req in request:
                            
                             # Disallow access to methods that start with an underscore
                            if req.method == '' or req.method[0] == '_':
                                result.append(Rpc_Response(id=req.id, error=Rpc_InvalidRequest()))
                                if hasattr(self, 'logger'):
                                    self.logger.debug('[%s, %s, %i] RPC request for protected method: %s', self.name, self.address, req.id, req.method)
                             
                            else:
                                allow = True
                                
                                if isinstance(target, RpcBase) and not target.rpc_hasAccess(self):
                                    # Send an error if somebody has exclusive access
                                    result.append(Rpc_Response(id=req.id, error={'code': -32001, 'message': 'Another connection has exclusive access.'}))
                                    if hasattr(self, 'logger'):
                                        self.logger.debug('[%s, %s, %i] RPC request denied - another user has exclusive access: %s', self.name, self.address, req.id, req.method)
                                    
                                    allow = False
                                    
                                if allow:
                                    if hasattr(self, 'logger'):
                                        self.logger.debug('[%s, %s, %i] RPC method call: %s', self.name, self.address, req.id, req.method)
                                        
                                    with self.lock:      
                                        try:
                                            if req.method[0:3] == 'rpc':
                                                result.append(req.call(target, self))
                                            else:
                                                result.append(req.call(target))
                                        except Exception as e:
                                            if hasattr(self, 'logger'):
                                                self.logger.exception('[%s, %s, %i] RPC Unhandled Exception: %s', self.name, self.address, req.id, req.method)
                                            result.append(Rpc_Response(id=req.id, error=Rpc_InternalError(message=str(e))))
                                
                    elif request == None or isinstance(request, Rpc_Error):
                        # An invalid request was parsed, error will be passed through to encode()
                        result = request
                    
                    else:
                        # Something really terrible must have happened
                        if hasattr(self, 'logger'):
                            self.logger.error("RPC Library Error")
                    
                    # Encode the outputs of the RPC requests
                    self.socket.send(self.rpc_encode(result))
                    
                else:
                    # Connection was closed by client
                    break
                
            except socket.error as e:
                # Socket closed poorly from client
                if hasattr(self, 'logger'):
                    self.logger.error('[%s, %s] Socket closed with error: %s', self.name, self.address, e.errno)
                break

            except:
                # Log an exception, close the connection
                if hasattr(self, 'logger'):
                    self.logger.exception('[%s, %s] Unhandled Exception', self.name, self.address)
                break
        
        self.socket.close()
        self.alive.clear()
        
        if hasattr(self, 'logger'):
            self.logger.debug('[%s, %s] Disconnected', self.name, self.address)
        
    def stop(self):
        self.socket.close()
        self.alive.clear()
        
        if hasattr(self, 'logger'):
            self.logger.debug('[%s, %s] Connection was asked to close internally', self.name, self.address)
        
    def attachLogger(self, loggerObj):
        if isinstance(loggerObj, logging.Logger):
            self.logger = loggerObj
    
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
    RPC_MAX_PACKET_SIZE = 4096 # 4K
    
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
        self.__rpcDecode__ = jsonrpc.decode
        self.__rpcEncode__ = jsonrpc.encode
        
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
                    
            except:
                pass
            
        self._setTimeout() # Default
            
    def _setTimeout(self, new_to=None):
        """
        Set the Timeout limit for an RPC Method call
        
        :param new_to: New Timeout time in seconds
        :type new_to: fload
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
                    raise response.getError()
            
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
                
    
