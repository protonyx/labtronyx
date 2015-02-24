import threading
import socket
import select
import logging
import inspect
import errno
from datetime import datetime

from jsonrpc import *
from errors import *

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
        protected and will not be invoked
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
        
        self.e_alive = threading.Event()
        self.rpc_lock = threading.Lock()
        self.rpc_startTime = datetime.now()
        
        # Attempt to bind a socket
        try:
            # TCP Socket
            srv_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv_socket_tcp.bind(('', self.port))
            srv_socket_tcp.listen(5)
            srv_socket_tcp.setblocking(0)
            
            # Update port if randomly assigned
            _, self.port = srv_socket_tcp.getsockname()
            
            # UDP Socket
            srv_socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            srv_socket_udp.bind(('', self.port))
            srv_socket_udp.setblocking(0)
            
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                # Server is already running
                raise RpcServerPortInUse
            
            else:
                raise
        
        self.e_alive.set()
            
        self.__rpc_thread = threading.Thread(name=self.name, target=self.__thread_run, args=(srv_socket_tcp, srv_socket_udp))
        self.__rpc_thread.start()
        
    def __thread_run(self, srv_socket_tcp, srv_socket_udp):
        _, self.port = srv_socket_tcp.getsockname()
        
        self.logger.debug('[%s] RPC Server started on port %i', self.name, self.port)
            
        self.rpc_startTime = datetime.now()

        while self.e_alive.isSet():
            # Service Socket
            try:
                ready_to_read,_,_ = select.select([srv_socket_tcp, srv_socket_udp], [], [], 1.0)
                
                for srv_socket in ready_to_read:
                    # Spawn a new thread to service the connection
                    connection, address = srv_socket.accept()
                    
                    # Spawn a new thread to service the connection
                    connThread = RpcConnection(server=self,
                                               socket=connection,
                                               logger=self.logger)
                        
                    connThread.start()

            except:
                self.logger.exception('RPC Server Socket Handler Exception')
                
            # Clean up old connections
            # TODO
                
        srv_socket.close()
        
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
    # Methods
    #===========================================================================
    
    def findMethod(self, method):
        """
        Return a bound method after searching through the server methods and the
        methods of all registered objects
        """
        # Disallow access to methods that start with an underscore
        if method == '' or method.startswith('_'):
            # Invalid - Protected Method
            self.logger.warning('RPC Request Denied (Protected Method): %s', method)
            raise AttributeError
                                
        elif method.startswith('rpc'):
            # Valid - RPC Server method
            return self._getMethod(self, method)
                
        else:
            # Check registered objects
            for reg_obj in self.rpc_objects:
                try:
                    return self._getMethod(reg_obj, method)
                except AttributeError:
                    pass
            
            # Unable to find method
            raise RpcMethodNotFound()
            
    def _getMethod(self, obj, method):
        test_method = getattr(obj, method)
        if inspect.ismethod(test_method):
            return test_method
        else:
            raise AttributeError
    
    #===========================================================================
    # RPC Functions
    #===========================================================================
    
    def rpc_getMethods(self, address=None):
        """
        Get a list of valid methods in the registered objects. Protected methods
        that begin with an underscore ('_') are not included.
        
        :returns: list of strings
        """
        # Catalog methods
        self.validMethods = []
        
        target_members = inspect.getmembers(self)
        
        for attr, val in target_members:
            if inspect.ismethod(val) and attr.startswith('rpc'):
                self.validMethods.append(attr)
                    
        for reg_obj in self.rpc_objects:
            target_members = inspect.getmembers(reg_obj)
            
            for attr, val in target_members:
                if inspect.ismethod(val) and not attr.startswith('_'):
                    self.validMethods.append(attr)
                
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
            delta = datetime.now() - self.rpc_startTime 
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
        return socket.gethostname()
        
    def rpc_getConnections(self, address=None):
        """
        Get the number of connections to the RPC server
        
        :returns: int
        """
        return len(self.rpc_connections)
    
class RpcConnection(threading.Thread):
    """
    Receives and processes RPC requests from remote connections (or local ones)
    
    Before any requests can be processed, the thread must acquire a lock to 
    synchronize access to RPC Server resources
    
    Any method that begins with an underscore is considered protected and will 
    be invalidated by the RPC server

    :param server: RPC Server object
    :type server: RpcServer
    :param socket: RPC Request Socket
    :type socket: socket.socket 
    :param logger: Logger instance if you wish to override the internal instance
    :type logger: Logging.logger
    """
    RPC_MAX_PACKET_SIZE = 4096
    
    def __init__(self, server, socket, **kwargs):
        threading.Thread.__init__(self)
        
        self.server = server
        self.socket = socket
        self.logger = kwargs.get('logger', logging)
        
        self.address, _ = self.socket.getsockname()
        
        self.lock = self.server.rpc_lock
        #self.name = self.parent.name
        
        # Give the thread a meaningful name
        self.name = '%s-%s' % (self.server.getName(), self.address)
    
    def run(self):
        
        try:
            ready_to_read,_,_ = select.select([self.socket],[],[], 1.0)
            # TODO: Read until all data is in the buffer
            
            if self.socket in ready_to_read:
                
                data = self.socket.recv(self.RPC_MAX_PACKET_SIZE)
                seg = None
                # Receive the full packet
                try:
                    while seg != "":
                        seg = self.socket.recv(self.RPC_MAX_PACKET_SIZE)
                        data += seg
                except socket.error as e:
                    if e.errno == errno.EWOULDBLOCK:
                        # No more data to process
                        pass
                    else:
                        pass
                
                if data:
                    # Process the incoming data as a JSON RPC packet
                    in_packet = JsonRpcPacket(data)
                    errors = in_packet.getErrors()
                    requests = in_packet.getRequests()
                    
                    out_packet = JsonRpcPacket()
                    
                    if len(errors) == 0:
                        # Only process requests if no errors were found during parsing
                        for req in requests:
                            # Process Requests in order
                            id = req.getID()
                            try:
                                result = self.processRequest(req)
                                
                                # Check if the request was a notification
                                if id is not None:
                                    out_packet.addResponse(id, result)
                            
                            # Catch exceptions during method execution
                            # DO NOT ALLOW ANY EXCEPTIONS TO PASS THIS LEVEL   
                            except RpcMethodNotFound:
                                out_packet.addError_MethodNotFound(id)
                                
                            except TypeError:
                                # Raised when arguments mismatch, but also other cases
                                # Not a perfect solution, but whatever.
                                out_packet.addError_InvalidParams(id)
                                self.logger.exception("RPC Server Type Error")
                                
                            except Exception as e:
                                # Catch-all for everything else
                                out_packet.addError_ServerException(id, e.message)
                                self.logger.exception("RPC Server Exception")
                    
                    # Encode the outputs of the RPC requests
                    out_str = out_packet.export()
                    self.socket.send(out_str)
                    
        except socket.error as e:
            # Socket closed poorly from client
            if e.errno == errno.ECONNABORTED:
                self.logger.error('[%s] Client socket closed before data could be sent', self.name)
            else:
                self.logger.error('[%s] Socket closed with error: %s', self.name, e.errno)

        except:
            # Log an exception, close the connection
            self.logger.exception('[%s] Unhandled Exception', self.name)
        
    def processRequest(self, req):
        id = req.getID()
        method = req.getMethod()
        self.logger.debug('[%s, %i] RPC Request: %s', self.name, id, method)
                            
        try:
            test_method = self.server.findMethod(method)
            
            with self.lock:
                return req.call(test_method)
            
        # Bubble all exceptions up to the calling function
        except RpcMethodNotFound:
            self.logger.error('RPC Method Not Found')
            raise
        