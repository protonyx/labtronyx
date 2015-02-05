import threading
import socket
import select
import logging
import inspect
from datetime import datetime

from jsonrpc import *

class RpcServer(threading.Thread):
    """
    Flexible RPC server that runs in a Python thread. Wraps any Python object
    and allows remote machines to call functions and receive returned data.
    
    :param logger: Logger instance if you wish to override the internal instance
    :type logger: Logging.logger
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
        self.rpc_lock = threading.Lock()
        
        if 'logger' in kwargs:
            self.logger = kwargs.get('logger')
        else:
            self.logger = logging
        
        if 'target' in kwargs:
            self.target = kwargs['target']
            self.name = 'RPC-Server-' + self.target.__class__.__name__
        else:
            raise RuntimeError('RPC Server must be provided a target object')

        self.port = kwargs.get('port', 0)
            
        # RPC State Variables
        self.rpc_connections = []
        self.rpc_exclusive = None
        self.rpc_exclusiveTime = None
        
        self._identity = 'JSON-RPC/2.0'
        
    def run(self):
        # Catalog methods
        self.validMethods = []
        target_members = inspect.getmembers(self)
        
        for member in target_members:
            if inspect.ismethod(member[1]) and member[0][0] != '_':
                self.validMethods.append(member[0])
                
        self.logger.info('Starting RPC Server...')
                
        # Start socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO: Bind on each interface
        self.socket.bind(('',self.port))
        self.socket.listen(5)
        self.socket.setblocking(0)
        
        self.port = self.socket.getsockname()[1]
        
        self.logger.debug('[%s] listening on port %i', self.name, self.port)
        self.logger.debug("[%s] Hostname: %s", self.name, socket.gethostname())
            
        self.rpc_startTime = datetime.now()
        self.alive.set()

        while self.alive.isSet():
            # Service Socket
            try:
                ready_to_read,_,_ = select.select([self.socket], [], [], 1.0)
                
                if self.socket in ready_to_read:
                    # Spawn a new thread to service the connection
                    connection, address = self.socket.accept()
                    
                    # Spawn a new thread to service the connection
                    connThread = RpcConnection(server=self,
                                               target=self.target,
                                               socket=connection,
                                               logger=self.logger)
                        
                    connThread.start()
                    
                    self.rpc_connections.append(connThread)

            except:
                self.logger.exception('RPC Server Socket Handler Exception')
                
            # Clean up old connections
            # TODO
                
        self.socket.close()
        
        if hasattr(self, 'logger'):
            self.logger.debug('[%s] RPC Server thread stopped', self.name)
            
    def rpc_isRunning(self, address=None):
        """
        Check if there is an RpcServer thread running
        
        :returns: bool - True if running, False if not running
        """
        if isinstance(self.rpc_thread, RpcServer):
            return self.rpc_thread.alive.is_set()
        
        else:
            return False
            
    def rpc_stop(self, connection=None):
        """
        Close the server socket and stop the RpcServer thread
        
        .. note::
        
            This operation may take a small amount of time for the socket to
            register the stop request.
        """
        self.alive.clear()
        
        for conn in self.rpc_connections:
            conn.stop()

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
    
    def rpc_getMethods(self, address=None):
        """
        Get a list of valid methods in the target object. Protected methods
        that begin with an underscore ('_') are not included.
        
        :returns: list of strings
        """
        return self.validMethods
    
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
    
    def __init__(self, **kwargs):
        threading.Thread.__init__(self)
        
        self.server = kwargs.get('server')
        self.target = kwargs.get('target')
        self.socket = kwargs.get('socket')
        
        if 'logger' in kwargs:
            self.logger = kwargs.get('logger')
        else:
            self.logger = logging
        
        self.address, _ = self.socket.getnameinfo()
        
        
        
        self.lock = self.server.rpc_lock
        #self.name = self.parent.name
        
        # Give the thread a meaningful name
        self.name = 'RPC-%s-%s' % (self.target.__class__.__name__, self.address)
        
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
                            self.logger.debug('[%s, %s, %i] RPC Request: %s', self.name, self.address, req.id, req.method)
                            
                             # Disallow access to methods that start with an underscore
                            if req.method == '' or req.method[0] == '_':
                                # Invalid - Protected Method
                                result.append(Rpc_Response(id=req.id, error=Rpc_InvalidRequest()))
                                
                                self.logger.debug('[%s, %s, %i] RPC Request Denied (Protected Method)', self.name, self.address, req.id)
                                
                            elif req.method.startswith('rpc'):
                                # Valid - RPC Server method
                                try:
                                    result.append(req.call(self.server, self.address))
                             
                                except Exception as e:
                                    self.logger.exception('[%s, %s, %i] RPC Server Exception: %s', self.name, self.address, req.id, req.method)
                                        
                                    result.append(Rpc_Response(id=req.id, error=Rpc_InternalError(message=str(e))))
                                    
                            elif self.server.rpc_hasAccess(self.address):
                                # Valid - Has Access
                                with self.lock:      
                                    try:
                                        result.append(req.call(self.target))
                                    #except TypeError as e:
                                        # Parameter issue
                                        #result.append(Rpc_Response(id=req.id, error=Rpc_InvalidParams(message=str(e))))
                                        
                                    except Exception as e:
                                        self.logger.exception('[%s, %s, %i] RPC Target Exception: %s', self.name, self.address, req.id, req.method)
                                        
                                        result.append(Rpc_Response(id=req.id, error=Rpc_InternalError(message=str(e))))
                                
                            else:
                                # Invalid - Access Error
                                self.logger.debug('[%s, %s, %i] RPC Request Denied (Access Violation)', self.name, self.address, req.id)
                                
                                result.append(Rpc_Response(id=req.id, error={'code': -32001, 'message': 'Another connection has exclusive access.'}))

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
            self.logger.error('[%s, %s] Socket closed with error: %s', self.name, self.address, e.errno)

        except:
            # Log an exception, close the connection
            self.logger.exception('[%s, %s] Unhandled Exception', self.name, self.address)
        
        self.socket.close()
        
    def stop(self):
        self.socket.close()
        
        self.logger.debug('[%s, %s] Connection was forcibly closed', self.name, self.address)
        