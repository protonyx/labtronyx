import threading
import Queue
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
    :param port: Port to attach srv_socket to
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
    type = "TCP"
    
    def __init__(self, **kwargs):
        self.logger = kwargs.get('logger', logging)
        self.port = kwargs.get('port', 0)
        self.name = kwargs.get('name', 'RPCServer')
            
        # RPC State Variables
        self.rpc_objects = []
        
        # Sockets
        self.connections = []
        # Registered Clients
        self.connections_reg = {}
        
        self.rpc_lock = threading.Lock()
        self.rpc_startTime = datetime.now()
        
        # Attempt to bind sockets
        try:
            if self.type == "TCP":
                # TCP Socket
                self.srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.srv_socket.bind(('', self.port))
                self.srv_socket.listen(5)
                self.srv_socket.setblocking(0)
            elif self.type == "UDP":
                # UDP Socket
                self.srv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.srv_socket.bind(('', self.port))
                self.srv_socket.setblocking(0)
            else:
                raise RuntimeError
            
            # Update port if randomly assigned
            _, self.port = self.srv_socket.getsockname()
            
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                # Server is already running
                raise RpcServerPortInUse
            
            else:
                raise
           
        self.__rpc_thread = RpcServerThread(name=self.name, 
                                            server=self,
                                            srv_socket=self.srv_socket,
                                            port=self.port,
                                            logger=self.logger)
        self.__rpc_thread.start()
            
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
    # Connection Management and Notifications
    #===========================================================================
    
    def notifyClients(self, event, *args, **kwargs):
        for address, port in self.connections_reg.items():
            pass
    
    def _registerConnection(self, connection):
        self.connections.append(connection)
        
    def _unregisterConnection(self, connection):
        self.connections.remove(connection)
        
    def rpc_register(self, address, port):
        self.connections_reg[address] = port
    
    def rpc_unregister(self, address):
        self.connections_reg.pop(address)
        
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
            raise RpcMethodNotFound()
                                
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
    
    def rpc_getMethods(self):
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
            
    def rpc_isRunning(self):
        """
        Check if there is an RpcServer thread running
        
        :returns: bool - True if running, False if not running
        """
        return self.__rpc_thread.is_alive()
            
    def rpc_stop(self):
        """
        Close the server srv_socket and stop the RpcServer thread
        
        .. note::
        
            This operation may take a small amount of time for the srv_socket to
            register the stop request.
        """
        self.__rpc_thread.join()

    def rpc_uptime(self):
        """
        Get the uptime of the RpcServer
        
        :returns: int - uptime in seconds
        """
        if hasattr(self, 'rpc_startTime'):
            delta = datetime.now() - self.rpc_startTime 
            return delta.total_seconds()
        else:
            return 0
        
    def rpc_getPort(self):
        """
        Get the bound port of a running RpcServer thread.
        
        :returns: int - Port
        """
        return self.port
        
    def rpc_getHostname(self):
        """
        Get the hostname of the RpcServer host.
        
        :returns: str - hostname
        """
        return socket.gethostname()
        
    def rpc_getConnections(self):
        """
        Get the number of connections to the RPC server
        
        :returns: int
        """
        return len(self.rpc_connections)
    
class RpcServerThread(threading.Thread):
    
    def __init__(self, name, server, srv_socket, **kwargs):
        threading.Thread.__init__(self)
        
        self.server = server
        self.srv_socket = srv_socket
        self.port = kwargs.get('port', 0)
        self.logger = kwargs.get('logger', logging)
        
        self.e_alive = threading.Event()
        
        # Give the thread a meaningful name
        self.name = name
        
    def run(self):
        self.e_alive.set()
        
        self.logger.debug('[%s] RPC Server started on port %i', self.name, self.port)
        
        while self.e_alive.isSet():
            # Service Socket
            try:
                ready_to_read,_,_ = select.select([self.srv_socket], [], [], 0.1)
                
                for srv_socket in ready_to_read:
                    # Spawn a new thread to service the connection
                    connection, address = srv_socket.accept()
                    
                    # Spawn a new thread to service the connection
                    connThread = RpcConnection(server=self.server,
                                               conn_socket=connection,
                                               logger=self.logger)
                        
                    connThread.start()

            except:
                self.logger.exception('RPC Server Socket Handler Exception')
                
        self.srv_socket.close()
        
        self.logger.debug('[%s] RPC Server stopped', self.name)
        
    def join(self, timeout=None):
        for conn in self.connections:
            if conn.is_active():
                conn.join()
            
        self.e_alive.clear()
        
        threading.Thread.join(self, timeout=timeout)
    
class RpcConnection(threading.Thread):
    """
    Receives and processes RPC requests from remote connections (or local ones)
    
    Before any requests can be processed, the thread must acquire a lock to 
    synchronize access to RPC Server resources
    
    Any method that begins with an underscore is considered protected and will 
    be invalidated by the RPC server

    :param server: RPC Server object
    :type server: RpcServer
    :param srv_socket: RPC Request Socket
    :type srv_socket: srv_socket.srv_socket 
    :param logger: Logger instance if you wish to override the internal instance
    :type logger: Logging.logger
    """
    RPC_MAX_PACKET_SIZE = 4096
    
    def __init__(self, server, conn_socket, **kwargs):
        threading.Thread.__init__(self)
        
        self.server = server
        self.conn_socket = conn_socket
        self.logger = kwargs.get('logger', logging)
        
        self.address, _ = self.conn_socket.getsockname()
        
        self.lock = self.server.rpc_lock
        
        self.e_alive = threading.Event()
        self.notification_queue = Queue.Queue()
        
        # Give the thread a meaningful name
        self.name = '%s-%s' % (self.server.getName(), self.address)
    
    def run(self):
        self.e_alive.set()
        self.server._registerConnection(self)

        self.logger.debug("New RPC Connection: %s", self.address)
        
        while(self.e_alive.isSet()):
            # Maintain the connection as long as it is open
            try:
                ready_to_read,_,_ = select.select([self.conn_socket],[],[], 0.1)
                # TODO: Read until all data is in the buffer
                
                if self.conn_socket in ready_to_read:
                    
                    data = self.conn_socket.recv(self.RPC_MAX_PACKET_SIZE)
                    seg = None
                    # Receive the full packet
                    try:
                        while seg != "":
                            seg = self.conn_socket.recv(self.RPC_MAX_PACKET_SIZE)
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
                        self.conn_socket.send(out_str)
                        
            except socket.error as e:
                # Socket closed poorly from client
                if e.errno == errno.ECONNABORTED:
                    self.logger.error('[%s] Client socket closed before data could be sent', self.name)
                    break
                else:
                    self.logger.error('[%s] Socket closed with error: %s', self.name, e.errno)
                    break
    
            except:
                # Log an exception, close the connection
                self.logger.exception('[%s] Unhandled Exception', self.name)
                break
            
            # Handle Notifications
            if self.notification_queue.not_empty():
                try:
                    packet = JsonRpcPacket()
                    
                    while (self.notification_queue.not_empty()):
                        item = self.notification_queue.get()
                        
                        packet.addRequest(None, 'handle_event', item)
                        
                    out_str = packet.export()
                    self.conn_socket.send(out_str)
                    
                except:
                    pass
            
        self.server._unregisterConnection(self)
            
    def join(self, timeout=None):
        self.e_alive.clear()
        
        threading.Thread.join(self, timeout=timeout)
        
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
        