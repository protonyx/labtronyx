import threading
import json
import logging
import requests

# Local imports
from . import errors
from . import engines
from . import jsonrpc

__all__ = ['RpcClient']


class RpcClient(object):
    """
    Establishes a TCP connection to the server through which all requests are
    send and responses are received. This is a blocking operation, so only one
    request can be sent at a time.
    
    :param uri: HTTP URI
    :type uri: str
    """
    # TODO: Add batch processing
    
    RPC_TIMEOUT = 10.0
    RPC_MAX_PACKET_SIZE = 1048576 # 1MB
    
    def __init__(self, uri, **kwargs):

        self.uri = uri
        self.timeout = kwargs.get('timeout', self.RPC_TIMEOUT)
        self.logger = kwargs.get('logger', logging)

        # Decode URI
        import urllib
        self.uri_type, uri = urllib.splittype(uri)
        host, self.path = urllib.splithost(uri)

        if ':' in host:
            self.host, self.port = host.split(':')
        else:
            self.host = host

        # Encode/Decode Engine, jsonrpc is the default
        self.engine = jsonrpc

        self.rpc_lock = threading.Lock()
        
        self.methods = []
    
    def _handleException(self, exception_object):
        raise NotImplementedError()

    def _getMethods(self):
        resp_data = requests.get(self.uri)

        return json.loads(resp_data.text).get('methods')
    
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
        req = engines.RpcRequest(method=remote_method, args=args, kwargs=kwargs)

        # Encode the RPC Request
        data = self.engine.encode([req], [])
        
        # Send the encoded request
        with self.rpc_lock:
            resp_data = requests.post(self.uri, data)

        # Check status code
        if resp_data.status_code is not 200:
            raise errors.RpcError("Server returned error code: %d" % resp_data.status_code)

        # Decode the returned data
        rpc_requests, rpc_responses, rpc_errors = self.engine.decode(resp_data.text)

        if len(rpc_errors) > 0:
            # There is a problem if there are more than one errors,
            # so just check the first one
            recv_error = rpc_errors[0]
            if isinstance(recv_error, errors.RpcMethodNotFound):
                raise AttributeError()
            else:
                raise recv_error

        elif len(rpc_responses) == 1:
            resp = rpc_responses[0]
            return resp.result

        else:
            raise errors.RpcInvalidPacket("An incorrectly formatted packet was received")
    
    def __str__(self):
        return '<RPC @ %s>' % (self.uri)

    class _RpcMethod(object):
        """
        RPC Method generator to bind a method call to an RPC server. Supports nested calls

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