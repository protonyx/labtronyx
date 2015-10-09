import threading
import socket
import logging
import errno
import string
import httplib
import importlib

# Local imports
from .errors import *
from .engines import RpcRequest, RpcResponse

__all__ = ['PtxRpcClient']

class HttpTransport(object):
    """
    HTTP Transport class based on the Transport class of xmlrpclib.py
    """
    VERSION = '1.0'

    user_agent = 'ptx-rpc/%s' % VERSION
    content_type = 'application/json'

    def __init__(self):
        self._connection = (None, None)

    def request(self, host, handler, request_body):
        """

        """
        for attempt in (0, 1):
            try:
                return self.single_request(host, handler, request_body)
            except socket.error as e:
                if attempt or e.errno not in (errno.ECONNRESET, errno.ECONNABORTED, errno.EPIPE):
                    raise

    def single_request(self, host, handler, request_body):
        """

        """
        conn = self.make_connection(host)

        try:
            conn.putrequest("POST", handler)

            # Send host data
            extra_headers = self._extra_headers
            if extra_headers:
                if type(extra_headers) == dict:
                    extra_headers = extra_headers.items()
                for key, value in extra_headers:
                    conn.putheader(key, value)

            # Send user agent
            conn.putheader("User-Agent", self.user_agent)

            # Send content
            conn.putheader("Content-Type", self.content_type)
            conn.putheader("Content-Length", str(len(request_body)))

            conn.endheaders(request_body)

            # Get response
            resp = conn.getresponse(buffering=True)
            # TODO: How do we set the timeout for getresponse?

            if resp.status == 200:
                return resp.read()

        except socket.error as e:
            if e.errno in [errno.ECONNREFUSED]:
                raise RpcServerNotFound()

        except Exception:
            self.close()
            raise

        # TODO: Handle case where response status is not 200


    def get_host_info(self, host):
        """
        Get authorization info from host parameter. Host may be a string, or a (host, x509-dict) tuple; if a string,
        it is checked for a "user:pw@host" format, and a "Basic Authentication" header is added if appropriate.

        :param host: Host descriptor (URL or (URL, x509 info) tuple)
        :returns: A 3-tuple containing (actual host, extra headers, x509 info).  The header and x509 fields may be None.
        """
        x509 = {}
        if type(host) == tuple:
            host, x509 = host

        import urllib
        auth, host = urllib.splituser(host)

        if auth:
            import base64
            auth = base64.encodestring(urllib.unquote(auth))
            auth = string.join(string.split(auth), "") # get rid of whitespace
            extra_headers = [
                ("Authorization", "Basic " + auth)
                ]
        else:
            extra_headers = None

        return host, extra_headers, x509


    def make_connection(self, host):
        """
        Open a connection or use an already open connection

        :param host:
        """
        if self._connection and host == self._connection[0]:
            return self._connection[1]

        chost, self._extra_headers, x509 = self.get_host_info(host)
        #store the host argument along with the connection object
        self._connection = host, httplib.HTTPConnection(chost)
        return self._connection[1]


    def close(self):
        """
        Close any open connection
        """
        if self._connection[1]:
            self._connection[1].close()
            self._connection = (None, None)


class PtxRpcClient(object):
    """
    Flexible RPC client that connects to an RpcServer instance either on a local
    host or remote host. Abstracts a remote object using the magic of Python.
    By utilizing functions from the remote RpcServer and object that extends
    RpcBase, RpcClient can dynamically create method aliases. In this way, a
    RpcClient object can "become" an instance of an object on a remote host.
    
    Establishes a TCP connection to the server through which all requests are
    send and responses are received. This is a blocking operation, so only one
    request can be sent at a time (currently). 
    
    To manually call a remote method, use the function RpcClient._rpcCall
    
    TODO: Add batch processing
    
    :param address: IP Address of remote RpcServer (Defaults to 'localhost')
    :type address: str - IPv4
    :param port: Port of remote RpcServer
    :type port: int
    """
    DEBUG_RPC_CLIENT = False
    
    RPC_TIMEOUT = 10.0
    RPC_MAX_PACKET_SIZE = 1048576 # 1MB
    
    def __init__(self, uri, **kwargs):

        import urllib
        self.uri = uri
        self.uri_type, uri = urllib.splittype(uri)
        self.host, self.path = urllib.splithost(uri)

        # self.address = self._resolveAddress(address)
        # self.port = port
        self.logger = kwargs.get('logger', logging)

        # Timeout
        self.timeout = kwargs.get('timeout')
        # TODO: Implement timeout programming

        # Data Transport, http is the default
        self._transport = kwargs.get('transport', HttpTransport)()

        # Encode/Decode Engine, jsonrpc is the default
        engine_name = kwargs.get('engine', 'jsonrpc')
        self.engine = importlib.import_module('ptxrpc.engines.%s' % engine_name)

        self.rpc_lock = threading.Lock()
        
        self.methods = []
        
    def _resolveAddress(self, address):
        try:
            socket.inet_aton(address)
            return address
            #self.hostname, _ = socket.gethostbyaddr(address)
        except socket.error:
            # Assume a hostname was given
            #self.hostname = address
            return socket.gethostbyname(address)
            
    def _getHostname(self):
        return self.hostname
    
    def _getAddress(self):
        return self.address
    
    def _ready(self):
        return self.ready
    
    def _handleException(self, exception_object):
        raise NotImplementedError()
    
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
        req = self.engine.RpcRequest(method=remote_method,
                                     args=args,
                                     kwargs=kwargs)

        # Encode the RPC Request
        data = self.engine.encode([req], [])
        
        # Send the encoded request
        with self.rpc_lock:
            resp_data = self._transport.request(self.host, self.path, data)

        if resp_data is None:
            raise RpcError("Server returned empty data")

        # Decode the returned data
        requests, responses, errors = self.engine.decode(resp_data)

        if len(errors) > 0:
            # There is a problem if there are more than one errors,
            # so just check the first one
            recv_error = errors[0]
            if isinstance(recv_error, RpcMethodNotFound):
                raise AttributeError()
            else:
                raise recv_error

            # if isinstance(recv_error, RpcInvalidPacket):
            #     pass
            #
            # elif isinstance(recv_error, RpcServerException):
            #     raise RuntimeError("RPC Server Exception")
            #
            # elif isinstance(recv_error, RpcError):
            #     raise recv_error
            #
            # else:
            #     raise RpcError()


        elif len(responses) == 1:
            resp = responses[0]
            return resp.result

        else:
            raise RpcInvalidPacket("An incorrectly formatted packet was received")
                    
        raise RpcTimeout("The operation timed out")
    
    def __str__(self):
        return '<RPC Instance of %s>' % (self.uri)

    class _RpcMethod(object):
        """
        RPC Method generator to bind a method call to an RPC server.

        Based on xmlrpclib
        """

        def __init__(self, rpc_call, method_name):
            self.__rpc_call = rpc_call
            self.__method_name = method_name

        def __getattr__(self, name):
            # supports "nested" methods (e.g. examples.getStateName)
            return self._RpcMethod(self.__rpc_call, "%s.%s" % (self.__method_name, name))

        def __call__(self, *args, **kwargs):
            return self.__rpc_call(self.__method_name, *args, **kwargs)

    def __getattr__(self, name):
        return self._RpcMethod(self._rpcCall, name)

        #return lambda *args, **kwargs: self._rpcCall(name, *args, **kwargs)