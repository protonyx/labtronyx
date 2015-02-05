import threading
import socket
import select
import logging
import inspect
from datetime import datetime

from jsonrpc import *

class RpcServer(object):
    """
    Flexible RPC server that runs in a Python thread. Wraps any Python object
    and allows remote machines to call functions and receive returned data.
    
    :param logger: Logger instance if you wish to override the internal instance
    :type logger: Logging.logger
    :param port: Port to attach socket to
    :type port: int 
    :param name: Internal name for the RPC server thread
    :type name: str
    
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
    
    _identity = 'JSON-RPC/2.0'
    
    def __init__(self, **kwargs):
        self.logger = kwargs.get('logger', logging)
        self.port = kwargs.get('port', 0)
        self.name = kwargs.get('name', 'RPCServer')
            
        # RPC State Variables
        self.rpc_objects = []
        self.rpc_connections = []
        self.rpc_exclusive = None
        self.rpc_exclusiveTime = None
        
        self.e_alive = threading.Event()
        self.rpc_lock = threading.Lock()
        
        self.e_alive.set()
            
        self.__rpc_thread = threading.Thread(name=self.name, target=self.__thread_run)
        self.__rpc_thread.start()
        
    def __thread_run(self):
        # Start socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO: Bind on each interface
        self.socket.bind(('',self.port))
        self.socket.listen(5)
        self.socket.setblocking(0)
        
        self.port = self.socket.getsockname()[1]
        
        self.logger.debug('[%s] RPC Server started on port %i', self.name, self.port)
        self.logger.debug("[%s] Hostname: %s", self.name, socket.gethostname())
            
        self.rpc_startTime = datetime.now()

        while self.e_alive.isSet():
            # Service Socket
            try:
                ready_to_read,_,_ = select.select([self.socket], [], [], 1.0)
                
                if self.socket in ready_to_read:
                    # Spawn a new thread to service the connection
                    connection, address = self.socket.accept()
                    
                    # Spawn a new thread to service the connection
                    connThread = RpcConnection(server=self,
                                               target=self.rpc_objects,
                                               socket=connection,
                                               logger=self.logger)
                        
                    connThread.start()
                    
                    self.rpc_connections.append(connThread)

            except:
                self.logger.exception('RPC Server Socket Handler Exception')
                
            # Clean up old connections
            # TODO
                
        self.socket.close()
        
        self.logger.debug('[%s] RPC Server stopped', self.name)
            
    #===========================================================================
    # Server Management
    #===========================================================================
            
    def getName(self):
        return self.name
    
    def registerObject(self, reg_obj):
        self.rpc_objects.append(reg_obj)
    
    def unregisterObject(self, reg_obj):
        self.rpc_objects.remove(reg_obj)
    
    #===========================================================================
    # RPC Functions
    #===========================================================================
    
    def rpc_getMethods(self, address=None):
        """
        Get a list of valid methods in the target object. Protected methods
        that begin with an underscore ('_') are not included.
        
        :returns: list of strings
        """
        # Catalog methods
        self.validMethods = []
        for reg_obj in self.rpc_objects:
            target_members = inspect.getmembers(reg_obj)
            
            for member in target_members:
                if inspect.ismethod(member[1]) and member[0][0] != '_':
                    self.validMethods.append(member[0])
                
        return self.validMethods
            
    def rpc_isRunning(self, address=None):
        """
        Check if there is an RpcServer thread running
        
        :returns: bool - True if running, False if not running
        """
        return self.e_alive.is_set()
            
    def rpc_stop(self, connection=None):
        """
        Close the server socket and stop the RpcServer thread
        
        .. note::
        
            This operation may take a small amount of time for the socket to
            register the stop request.
        """
        self.e_alive.clear()
        self.__rpc_thread.join()

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
        
    def rpc_getPort(self, address=None):
        """
        Get the bound port of a running RpcServer thread.
        
        :returns: int - Port
        """
        return self.port
        
    def rpc_getHostname(self, address=None):
        """
        Get the hostname of the RpcServer host.
        
        :returns: str - hostname
        """
        hostname = socket.gethostname()
        return hostname
      
    def rpc_getTargetObjectName(self, address=None):
        """
        Get the class name of the target object.
        
        :returns: str - Object name
        """
        return self.__class__.__name__
        
    def rpc_getConnections(self, address=None):
        """
        Get the number of connections to the RPC server
        
        :returns: int
        """
        return len(self.rpc_connections)
    
    #===========================================================================
    # RPC Connection Locking
    #===========================================================================
    
    def rpc_hasAccess(self, address):
        """
        Check if an address has access to execute RPC.
        
        :returns: bool
        """
        return self.rpc_exclusive is None or (timedelta(seconds=self.EXCLUSIVE_TIMEOUT) < (datetime.now() - self.rpc_exclusiveTime))
    
    def rpc_requestExclusiveAccess(self, address):
        """
        Request exclusive access to the target object from the RPC interface. 
        This acts as a lock on the target object, and no other connections can
        call functions. 
        
        .. note::
        
            Exclusive Access locks expire after 60 seconds, and must be renewed
            by another call to :func:`RpcBase.rpc_requestExclusiveAccess`
            
        :returns: bool - True if exclusive lock granted, False if denied
        """
        if self.rpc_hasAccess(address):
            # No other connection has exclusive access, or previous owner did not renew exclusive lock
            self.rpc_exclusive = address
            self.rpc_exclusiveTime = datetime.now()
            
            self.logger.debug('[%s, %s] Requested exclusive access', self.name, address)
            
            return True

        else:
            return False
            
    def rpc_releaseExclusiveAccess(self, address):
        """
        Release exclusive access. If a connection does not have exclusive access,
        this function does nothing.
        
        .. note::
        
            This function does not have to be called explicitly, the lock
            will expire automatically after 60 seconds.
            
        :returns: bool - True if lock released, False otherwise
        """
        if self.rpc_exclusive is address:
            self.rpc_exclusive = None
              
            self.logger.debug('[%s, %s] Released exclusive access', self.name, connection.address)
              
            return True
          
        else:
            return False
    
class RpcConnection(threading.Thread):
    """
    Receives and processes RPC requests from remote connections (or local ones)
    
    Before any requests can be processed, the thread must acquire a lock to synchronize access
    to the shared resource (model object)
    
    Remote users can request exclusive access, but must renew the lock every 60 seconds or other users will be
    allowed to request access
    
    Any method that begins with an underscore is considered protected and will be invalidated by the RPC server

    :param server: RPC Server object
    :type server: RpcServer
    :param target: Target object
    :type target: object
    :param socket: RPC Request Socket
    :type socket: socket.socket 
    :param logger: Logger instance if you wish to override the internal instance
    :type logger: Logging.logger
    
    """
    RPC_MAX_PACKET_SIZE = 1048576 # 1MB
    
    def __init__(self, server, target, socket, **kwargs):
        threading.Thread.__init__(self)
        
        self.server = server
        self.target = target
        self.socket = socket
        self.logger = kwargs.get('logger', logging)
        
        self.address, _ = self.socket.getnameinfo()
        
        self.lock = self.server.rpc_lock
        #self.name = self.parent.name
        
        # Give the thread a meaningful name
        self.name = '%s-%s' % (self.server.getName(), self.address)
        
        # Hardcode JSON RPC for now
        self.rpc_decode = Rpc_decode
        self.rpc_encode = Rpc_encode
    
    def run(self):
        
        self.logger.debug('[%s, %s] Connection established', self.name, self.address)

        try:
            ready_to_read,_,_ = select.select([self.socket],[],[], 1.0)
            # TODO: Read until all data is in the buffer
            
            if self.socket in ready_to_read:
                
                data = self.socket.recv(self.RPC_MAX_PACKET_SIZE)
                
                if type(data) is str and data[0:4] == 'HELO':
                    self.socket.send(self.server._identity)
                    
                elif data:
                    # Process the incoming data as a JSON RPC packet
                    try:
                        request, _ = self.rpc_decode(data)
                    except Rpc_Error as e:
                        request = e
                        
                    result = []
                    target = self.target
                    
                    if type(request) == list and len(request) > 0:
                        # Iterate through each request, verify access criteria
                        
                        for req in request:
                            result.append(self.processRequest(req))
                                
                    elif request == None or isinstance(request, Rpc_Error):
                        # An invalid request was parsed, error will be passed through to encode()
                        result = request
                    
                    else:
                        # Something really terrible must have happened
                        self.logger.error("RPC Library Error")
                    
                    # Encode the outputs of the RPC requests
                    self.socket.send(self.rpc_encode(result))
                    
            
        except socket.error as e:
            # Socket closed poorly from client
            self.logger.error('[%s] Socket closed with error: %s', self.name, e.errno)

        except:
            # Log an exception, close the connection
            self.logger.exception('[%s] Unhandled Exception', self.name)
        
        self.socket.close()
        
    def stop(self):
        self.socket.close()
        
        self.logger.debug('[%s] Connection was forcibly closed', self.name)
        
    def processRequest(self, req):
        self.logger.debug('[%s, %i] RPC Request: %s', self.name, req.id, req.method)
                            
        try:
            if self.server.rpc_hasAccess(self.address):
                method = self.findMethod(req.method)
                
                with self.lock:
                    return req.call(self.target)
                    
            else:
                self.logger.debug('[%s, %s, %i] RPC Request Denied (Access Violation)', self.name, self.address, req.id)
                return Rpc_Response(id=req.id, error={'code': -32001, 'message': 'Another connection has exclusive access.'})

            
        except AttributeError:
            self.logger.warning('RPC Method Not Found')
            return Rpc_Response(id=req.id, error=Rpc_InvalidRequest())
            
        except Exception as e:
            self.logger.exception('[%s, %s, %i] RPC Target Exception: %s', self.name, self.address, req.id, req.method)
            return Rpc_Response(id=req.id, error=Rpc_InternalError(message=str(e)))
        
    def findMethod(self, method):
        """
        Return a bound method after searching through the server methods and the
        methods of all registered objects
        """
        # Disallow access to methods that start with an underscore
        if req.method == '' or req.method[0] == '_':
            # Invalid - Protected Method
            result.append(Rpc_Response(id=req.id, error=Rpc_InvalidRequest()))
                                
            self.logger.warning('RPC Request Denied (Protected Method): %s', method)
                                
        elif req.method.startswith('rpc'):
            # Valid - RPC Server method
            return self.getMethod(self.server, method)
                
        else:
            # Check registered objects
            for reg_obj in self.target:
                try:
                    return getMethod(reg_obj, method)
                except AttributeError:
                    pass
            
            # Unable to find method
            raise AttributeError
            
    def getMethod(self, obj, method):
        test_method = getattr(obj, method)
        if inspect.ismethod(test_method):
            return test_method
        else:
            raise AttributeError