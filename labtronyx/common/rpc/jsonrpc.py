
import json

"""
JSON RPC Python class

Follows the JSON RPC 2.0 Spec (http://www.jsonrpc.org/specification)

This class can either be instantiated with a JSON encoded string or used as 
a utility helper class
"""

#===============================================================================
# Error Type
#===============================================================================
                 
class JsonRpc_Error(RuntimeError):
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
        return {'id': self.id,
                'error': {'code': self.code, 'message': self.message}}

class JsonRpc_ParseError(JsonRpc_Error):
    code = -32700
    message = 'Invalid JSON was received by the server.'

class JsonRpc_InvalidRequest(JsonRpc_Error):
    code = -32600
    message = 'The JSON sent is not a valid Request object.'

class JsonRpc_MethodNotFound(JsonRpc_Error):
    code = -32601
    message = 'The method does not exist / is not available.'

class JsonRpc_InvalidParams(JsonRpc_Error):
    code = -32602
    message = 'Invalid method parameter(s).'

class JsonRpc_InternalError(JsonRpc_Error):
    code = -32603
    message = 'Internal JSON-RPC error.'

class JsonRpc_ServerException(JsonRpc_Error):
    code = -32000
    message = 'An unhandled server exception occurred'

JsonRpcErrors = {  -32700: JsonRpc_ParseError,
                   -32600: JsonRpc_InvalidRequest,
                   -32601: JsonRpc_MethodNotFound,
                   -32602: JsonRpc_InvalidParams,
                   -32603: JsonRpc_InternalError,
                   -32000: JsonRpc_ServerException  } 
                 # -32000 to -32099 are reserved server-errors
                 
#===============================================================================
# Request Type
#===============================================================================
               
class JsonRpc_Request(object):
    def __init__(self, **rpc_dict):
        self.id = rpc_dict.get('id', None)
        self.method = rpc_dict.get('method', '')
        self.params = rpc_dict.get('params', [])
        self.kwargs = rpc_dict.get('kwargs', {})
        
    def getID(self):
        return self.id
    
    def getMethod(self):
        return self.method
        
    def export(self):
        # Slight modification of the JSON RPC 2.0 specification to allow 
        # both positional and named parameters
        # Adds kwargs variable to object only when both are present
        out = {'id': self.id, 'method': self.method }
        if len(self.params) > 0:
            out['params'] = self.params
            if len(self.kwargs) > 0:
                out['kwargs'] = self.kwargs
            
        elif len(self.params) == 0:
            out['params'] = self.kwargs
            
        return out
        
    def call(self, target):
        # Invoke target method with stored arguments
        # Don't attempt to catch exceptions here, let them bubble up
        if type(self.params) == dict and len(self.kwargs) == 0:
            # Only keyword parameters
            return target(**self.params)
        else:
            return target(*self.params, **self.kwargs)
        
#===============================================================================
# Response Type
#===============================================================================

class JsonRpc_Response(object):
    def __init__(self, **rpc_dict):

        self.id = rpc_dict.get('id', None)
        self.result = rpc_dict.get('result', None)
        
    def getID(self):
        return self.id
        
    def getResult(self):
        return self.result
        
    def export(self):
        ret = {'id': self.id,
               'result': self.result}
            
        return ret
     
#===============================================================================
# JSON RPC Handlers
#===============================================================================

class JsonRpcPacket(object):
    
    def __init__(self, str_req=None):
        self.requests = []
        self.responses = []
        self.errors = []
        
        if str_req is not None:
            try:
                req = json.loads(str_req)
                
                if type(req) == list:
                    # Batch request
                    for sub_req in req:
                        try:
                            self._parseJsonObject(sub_req)
                        except:
                            self.errors.append(JsonRpc_InvalidRequest())
                            
                    if len(req) == 0:
                        self.errors.append(JsonRpc_InvalidRequest())
                    
                elif type(req) == dict:
                    # Single request
                    self._parseJsonObject(req)
                
                else:
                    self.errors.append(JsonRpc_ParseError())
                
            except:
                # No JSON object could be decoded
                self.errors.append(JsonRpc_ParseError())
        
    def _parseJsonObject(self, rpc_dict):
        """
        Takes a dictionary and determines if it is an RPC request or response
        """
        if rpc_dict.get('jsonrpc') == '2.0':
            if 'method' in rpc_dict.keys() and type(rpc_dict.get('method')) is unicode:
                # Request object
                self.requests.append(JsonRpc_Request(**rpc_dict))
            
            elif 'id' in rpc_dict.keys() and 'result' in rpc_dict.keys():
                # Result response object
                self.responses.append(JsonRpc_Response(**rpc_dict))
                
            elif 'id' in rpc_dict.keys() and 'error' in rpc_dict.keys():
                # Error response object
                error_code = rpc_dict['error'].get('code', -32700)
                err_obj = JsonRpcErrors.get(error_code, JsonRpc_ParseError)
                
                self.errors.append(err_obj(**rpc_dict))
                
            else:
                self.errors.append(JsonRpc_InvalidRequest(**rpc_dict))
                
        else:
            self.errors.append(JsonRpc_InvalidRequest())
    
    def addRequest(self, id, method, *args, **kwargs):
        self.requests.append(JsonRpc_Request(id=id,
                                             method=method,
                                             params=args,
                                             kwargs=kwargs))
        
    def clearRequests(self):
        self.requests = []
    
    def getRequests(self):
        return self.requests
    
    def addResponse(self, id, result):            
        self.responses.append(JsonRpc_Response(id=id,
                                               result=result))
        
    def clearResponses(self):
        self.responses = []
    
    def getResponses(self):
        return self.responses
    
    def addError_InvalidParams(self, id):
        if id is not None:
            self.errors.append(JsonRpc_InvalidParams(id=id))
    
    def addError_ServerException(self, id, msg=None):
        if id is not None:
            self.errors.append(JsonRpc_ServerException(id=id,
                                                       message=msg))
    
    def addError_MethodNotFound(self, id):
        if id is not None:
            self.errors.append(JsonRpc_MethodNotFound(id=id))
    
    def getErrors(self):
        return self.errors
    
    def export(self):
        ret = []
        
        for rpc_obj in self.requests + self.responses + self.errors:
            rpc_dict = rpc_obj.export()
            rpc_dict['jsonrpc'] = '2.0'
            
            ret.append(rpc_dict)
        
        if len(ret) == 1:
            return str(json.dumps(ret[0]))
        elif len(ret) > 1:
            return str(json.dumps(ret))
        else:
            return ''
