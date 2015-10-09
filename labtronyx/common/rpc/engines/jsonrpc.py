"""
JSON RPC Python class for PTX-RPC

Conforms to the JSON RPC 2.0 Spec (http://www.jsonrpc.org/specification) with
a small addition to allow for both positional and keyword arguments

This class can either be instantiated with a JSON encoded string or used as 
a utility helper class
"""
import json

from .. import errors
from . import RpcRequest, RpcResponse

def get_content_type():
    return 'application/json'

#===============================================================================
# Error Type
#===============================================================================

def error_encode(obj):
    return {'jsonrpc': '2.0',
            'id': obj.id,
            'error': {'code': obj.code, 'message': obj.message}}
                 
class JsonRpc_Error(errors.RpcError):
    code = None
    message = None
    data = None

    def __init__(self, **rpc_dict):
        RuntimeError.__init__(self)
        
        self.id = rpc_dict.get('id', None)
        
        if 'error' in rpc_dict:
            error = rpc_dict.get('error', {})
            self.code = error.get('code', None)
            self.message = error.get('message', None)
        
    def __str__(self):
        return repr(str(self.message))
        
    def export(self):
        return error_encode(self)

class JsonRpc_ParseError(errors.RpcInvalidPacket, JsonRpc_Error):
    code = -32700
    message = 'Invalid JSON was received by the server.'

class JsonRpc_InvalidRequest(errors.RpcInvalidPacket, JsonRpc_Error):
    code = -32600
    message = 'The JSON sent is not a valid Request object.'

class JsonRpc_MethodNotFound(errors.RpcMethodNotFound, JsonRpc_Error):
    code = -32601
    message = 'The method does not exist / is not available.'

class JsonRpc_InvalidParams(errors.RpcServerException, JsonRpc_Error):
    code = -32602
    message = 'Invalid method parameter(s).'

class JsonRpc_InternalError(errors.RpcServerException, JsonRpc_Error):
    code = -32603
    message = 'Internal JSON-RPC error.'

class JsonRpc_ServerException(errors.RpcServerException, JsonRpc_Error):
    code = -32000
    message = 'An unhandled server exception occurred'

JsonRpcErrors = {  -32700: JsonRpc_ParseError,
                   -32600: JsonRpc_InvalidRequest,
                   -32601: JsonRpc_MethodNotFound,
                   -32602: JsonRpc_InvalidParams,
                   -32603: JsonRpc_InternalError,
                   -32000: JsonRpc_ServerException  } 
                 # -32000 to -32099 are reserved server-errors

JsonRpc_error_map = {
                    errors.RpcError: JsonRpc_InternalError,
                    errors.RpcInvalidPacket: JsonRpc_InvalidRequest,
                    errors.RpcMethodNotFound: JsonRpc_MethodNotFound,
                    errors.RpcServerException: JsonRpc_ServerException
                    }

#===============================================================================
# Request Type
#===============================================================================
               
class JsonRpc_Request(RpcRequest):
    def __init__(self, **rpc_dict):
        self.id = rpc_dict.get('id', None)
        self.method = rpc_dict.get('method', '')

        # decode arguments
        args = rpc_dict.get('params', [])
        kwargs = rpc_dict.get('kwargs', {})

        if type(args) == dict:
            self.kwargs = args
            self.args = []

        else:
            self.kwargs = kwargs
            self.args = args
        
    def export(self):
        # Slight modification of the JSON RPC 2.0 specification to allow 
        # both positional and named parameters
        # Adds kwargs variable to object only when both are present
        out = {'jsonrpc': '2.0',
               'id': self.id,
               'method': self.method }

        if len(self.args) > 0:
            out['params'] = self.args
            if len(self.kwargs) > 0:
                out['kwargs'] = self.kwargs
            
        elif len(self.args) == 0:
            out['params'] = self.kwargs
            
        return out
        
#===============================================================================
# Response Type
#===============================================================================

class JsonRpc_Response(RpcResponse):
    def __init__(self, **rpc_dict):

        self.id = rpc_dict.get('id', None)
        self.result = rpc_dict.get('result', None)
        
    def export(self):
        ret = {'jsonrpc': '2.0',
               'id': self.id,
               'result': self.result}
            
        return ret

def generate_id():
    next_id = 0

    while 1:
        next_id += 1
        yield next_id
     
#===============================================================================
# JSON RPC Handlers
#===============================================================================

def _parseJsonRpcObject(rpc_dict):
    """
    Takes a dictionary and determines if it is an RPC request or response
    """
    if rpc_dict.get('jsonrpc') == '2.0':
        if 'method' in rpc_dict.keys() and type(rpc_dict.get('method')) is unicode:
            # Request object
            req = RpcRequest(**rpc_dict)

            req.kwargs = rpc_dict.get('kwargs', {})
            req.args = rpc_dict.get('params', [])
            if type(req.args) == dict:
                req.kwargs = req.args
                req.args = []

            # if len(args) > 0 and len(kwargs) > 0:
            #     # Multiple parameter types
            #     req.args = args
            #     req.kwargs = kwargs
            # elif len(args) > 0 and len(kwargs) == 0:
            #     # Only positional parameters
            #     req.args = args
            #     req.kwargs = {}
            # elif len(args) == 0 and len(kwargs) > 0:
            #     # Only keyword parameters
            #     req.args = []
            #     req.kwargs = kwargs
            # else:
            #     # No parameters?
            #     req.args = args
            #     req.kwargs = kwargs

            return req

        elif 'id' in rpc_dict.keys() and 'result' in rpc_dict.keys():
            # Result response object
            return RpcResponse(**rpc_dict)

        elif 'id' in rpc_dict.keys() and 'error' in rpc_dict.keys():
            # Error response object
            error_code = rpc_dict['error'].get('code', -32700)
            err_obj = JsonRpcErrors.get(error_code, JsonRpc_ParseError)

            return err_obj(**rpc_dict)

        else:
            return JsonRpc_InvalidRequest(**rpc_dict)

    else:
        return JsonRpc_InvalidRequest()

def decode(data):
    """

    :param data:
    :return: (requests, responses, errors)
    """
    requests = []
    responses = []
    rpc_errors = []

    try:
        req = json.loads(data)

        if type(req) == list:
            # Batch request
            for sub_req in req:
                try:
                    res = _parseJsonRpcObject(sub_req)
                    if isinstance(res, RpcRequest):
                        requests.append(res)
                    elif isinstance(res, RpcResponse):
                        responses.append(res)
                    elif isinstance(res, errors.RpcError):
                        rpc_errors.append(res)

                except:
                    rpc_errors.append(JsonRpc_InvalidRequest())

            if len(req) == 0:
                rpc_errors.append(JsonRpc_InvalidRequest())

        elif type(req) == dict:
            # Single request
            res = _parseJsonRpcObject(req)
            if isinstance(res, RpcRequest):
                requests.append(res)
            elif isinstance(res, RpcResponse):
                responses.append(res)
            elif isinstance(res, errors.RpcError):
                rpc_errors.append(res)

        else:
            rpc_errors.append(JsonRpc_ParseError())

    except Exception as e:
        # No JSON object could be decoded
        rpc_errors.append(JsonRpc_ParseError())

    return (requests, responses, rpc_errors)

def encode(requests, responses):
    """

    :param requests:
    :param responses:
    :return: str
    """
    ret = []

    for rpc_obj in requests + responses:
        if type(rpc_obj) == RpcRequest:
            rpc_obj.__class__ = JsonRpc_Request
            # Generate new ID for requests
            rpc_obj.id = generate_id().next()

        if type(rpc_obj) == RpcResponse:
            rpc_obj.__class__ = JsonRpc_Response

        if isinstance(rpc_obj, errors.RpcError) and type(rpc_obj) not in JsonRpcErrors.values():
            rpc_obj.__class__ = JsonRpc_error_map.get(type(rpc_obj), JsonRpc_InternalError)

        rpc_dict = rpc_obj.export()

        ret.append(rpc_dict)

    if len(ret) == 1:
        return str(json.dumps(ret[0]))
    elif len(ret) > 1:
        return str(json.dumps(ret))
    else:
        return ''
