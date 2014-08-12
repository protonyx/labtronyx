
import json

"""
JSON RPC Python class

Follows the JSON RPC 2.0 Spec (http://www.jsonrpc.org/specification)

This class can either be instantiated with a JSON encoded string or used as a utility helper class
"""

# Error Exceptions
class Rpc_Error(RuntimeError):
    code = None
    message = None
    data = None

    def __init__(self, id = None, message = None, data = None):
        RuntimeError.__init__(self)
        self.id = id
        self.message = message or self.message
        self.data = data
        
    def __str__(self):
        return repr(str(self.message))
        
    def export(self):
        return {'code': self.code, 'message': self.message}

class Rpc_ParseError(Rpc_Error):
    code = -32700
    message = 'Invalid JSON was received by the server.'

class Rpc_InvalidRequest(Rpc_Error):
    code = -32600
    message = 'The JSON sent is not a valid Request object.'

class Rpc_MethodNotFound(Rpc_Error):
    code = -32601
    message = 'The method does not exist / is not available.'

class Rpc_InvalidParams(Rpc_Error):
    code = -32602
    message = 'Invalid method parameter(s).'

class Rpc_InternalError(Rpc_Error):
    code = -32603
    message = 'Internal JSON-RPC error.'

class Rpc_Timeout(Rpc_Error):
    pass

class Rpc_ServerException(Rpc_Error):
    code = -32000
    message = 'An unhandled server exception occurred'
    
JsonRpcErrors = {  -32700: Rpc_ParseError,
                   -32600: Rpc_InvalidRequest,
                   -32601: Rpc_MethodNotFound,
                   -32602: Rpc_InvalidParams,
                   -32603: Rpc_InternalError,
                   -32000: Rpc_ServerException  } 
                 # -32000 to -32099 are reserved server-errors
    
def parseJsonRpc(rpc_dict):
    """
    Takes a dictionary and determines if it is an RPC request or response
    """
    
    if type(rpc_dict) == dict:
        try:
            if rpc_dict.get('jsonrpc') == '2.0':
                if 'method' in rpc_dict.keys():
                    # Request object
                    return Rpc_Request(id=rpc_dict.get('id', None), method=rpc_dict['method'], params=rpc_dict.get('params', []), kwargs=rpc_dict.get('kwargs', {}) )
                
                elif 'id' in rpc_dict.keys() and 'result' in rpc_dict.keys():
                    # Result response object
                    return Rpc_Response(id=rpc_dict['id'], result=rpc_dict['result'])
                    
                elif 'id' in rpc_dict.keys() and 'error' in rpc_dict.keys():
                    # Error response object
                    error_code = rpc_dict['error']['code']
                    
                    if error_code in JsonRpcErrors.keys():
                        return Rpc_Response(id=rpc_dict['id'], error=JsonRpcErrors[error_code](message=rpc_dict['error'].get('message')))
                    else:
                        return Rpc_Response(id=rpc_dict['id'], error=Rpc_InternalError())
                    
                elif 'id' in rpc_dict.keys():
                    return Rpc_InvalidRequest(id=rpc_dict.get('id', None))
                    
                else:
                    return Rpc_InvalidRequest()
                    
            else:
                return Rpc_InvalidRequest()
            
        except Exception as E:
            return Rpc_InvalidRequest()
        
    else:
        raise TypeError()
    
def Rpc_decode(str_req):
    """
    Takes a string and returns:
    
    tuple of lists of Rpc_Request and Rpc_Response objects
    """

    requests = []
    responses = []
    
    try:
        if type(str_req) == str and str_req != '':
            req = json.loads(str_req)
        else:
            req = None
        
        if type(req) == list:
            if len(req) >= 1:
                # Iterate through each item in the list and determine if it is a request or a response
                for sub_req in req:
                    item = parseJsonRpc(sub_req)
                    
                    if isinstance(item, Rpc_Request):
                        requests.append(item)
                    elif isinstance(item, Rpc_Response):
                        responses.append(item)

            else:
                raise Rpc_InvalidRequest()
            
        elif type(req) == dict:
            # Single request
            item = parseJsonRpc(req)
            
            if isinstance(item, Rpc_Request):
                requests.append(item)
            elif isinstance(item, Rpc_Response):
                responses.append(item)
        
        else:
            raise Rpc_ParseError()
        
    except ValueError:
        # No JSON object could be decoded
        raise Rpc_ParseError()
        
    return (requests, responses)
    
def Rpc_encode(toEncode):
    """
    Convert a list of Rpc_Request and Rpc_Result objects into a JSON RPC string for transmission
    """
        
    ret = []
    
    if type(toEncode) == list:
        if len(toEncode) > 1:
            # Encode a list of responses
            for item in toEncode:
                if isinstance(item, Rpc_Request) or isinstance(item, Rpc_Response):
                    item_dict = item.export()
                    item_dict['jsonrpc'] = '2.0'
                    
                    if 'error' in item_dict.keys():
                        item_dict['error'] = errorToDict(item_dict['error'])
                    
                    ret.append(item_dict)
                    
                else:
                    ret = Rpc_ParseError()
        
        elif len(toEncode) == 1:
            # Encode a single response
            item_dict = toEncode[0].export()
            item_dict['jsonrpc'] = '2.0'
            
            ret = item_dict
        
        else:
            # Something happened and there are no valid responses
            ret = Rpc_InvalidRequest()
        
    elif isinstance(toEncode, Rpc_Error):
        ret = toEncode
        
    else:
        # Results must be a list
        ret = Rpc_ParseError()
        
    if isinstance(ret, Rpc_Error):
        ret = errorToDict(ret)
        
    return str(json.dumps(ret))

class Rpc_Request(object):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.method = kwargs.get('method', '')
        self.params = kwargs.get('params', [])
        self.kwargs = kwargs.get('kwargs', {})
        
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
        
    def call(self, target, *pos_args, **kw_args):
        # Parse method        

        if hasattr(target, self.method):
            self.method = getattr(target, self.method)
        else:
            return Rpc_Response(id=self.id, error=Rpc_MethodNotFound())
            
        # Parse params
        self.params_pos = list(pos_args)
        self.params_named = kw_args
        if type(self.params) == dict:
            # Only named parameters
            self.params_named.update(self.params)
            
        elif type(self.params) == list:
            # Only positional parameters
            self.params_pos = self.params_pos + self.params
            
            if len(self.kwargs) > 0:
                # Positional and named parameters
                self.params_named.update(self.kwargs)
                
            #self.params_named = self.params.get("__args", [])
            #if self.params_pos:
                #del self.params["__args"]
            
        else:
            return Rpc_Response(id=self.id, error=Rpc_InvalidParams())
            
        # Invoke method
        try:
            ret = self.method(*self.params_pos, **self.params_named)
            # Build the response with the results
            if self.id != None:
                # Only send a result of a notification if an error occurred
                return Rpc_Response(id=self.id, result=ret)
            else:
                return None
        
        except NotImplementedError:
            # Whoops, somebody didn't follow the API
            return Rpc_Response(id=self.id, error=Rpc_MethodNotFound())
            
        except:
            raise
        
class Rpc_Response(object):
    def __init__(self, **kwargs):

        self.id = kwargs.get('id', None)
        self.result = kwargs.get('result', None)
        self.error = kwargs.get('error', None)
        
    def export(self):
        ret = {'id': self.id}
        if self.error != None:
            try:
                ret['error'] = self.error.export()
            except:
                ret['error'] = self.error
        elif self.result != None:
            ret['result'] = self.result
        else:
            ret['result'] = None
            
        return ret
    
    def isError(self):
        if self.error != None:
            return True
        
        else:
            return False
        
    def getError(self):
        if self.isError():
            return self.error


