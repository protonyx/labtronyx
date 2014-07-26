import json

class JSON_RPC(object):
    """
    JSON RPC Python class
    
    Follows the JSON RPC 2.0 Spec (http://www.jsonrpc.org/specification)
    
    This class can either be instantiated with a JSON encoded string or used as a utility helper class
    """
        
    def __init__(self, str_req=None):
        # Internal RPC Object lists
        self.requests = []
        self.responses = []
        self.out = []
    
        self.error = None
        self.__str_req = str(str_req)

    def __parse(self, rpc_dict):
        """
        Takes a dictionary and determines if it is an RPC request or response
        """
        if type(rpc_dict) == dict:
            try:
                if rpc_dict.get('jsonrpc') == '2.0':
                    if 'method' in rpc_dict.keys() and 'params' in rpc_dict.keys():
                        # Request object
                        return Rpc_ValidRequest(rpc_dict)
                    
                    elif 'id' in rpc_dict.keys() and 'result' in rpc_dict.keys():
                        # Result response object
                        return Rpc_ResultResponse(dict=rpc_dict)
                        
                    elif 'id' in rpc_dict.keys() and 'error' in rpc_dict.keys():
                        # Error response object
                        return Rpc_ErrorResponse(dict=rpc_dict)
                            
                    elif 'id' in rpc_dict.keys():
                        return Rpc_InvalidRequest(id=rpc_dict['id'], error=InvalidRequest())
                        
                    else:
                        return Rpc_InvalidRequest(error=InvalidRequest())
                        
                else:
                    return Rpc_InvalidRequest(error=InvalidRequest())
                
            except:
                return Rpc_InvalidRequest(error=InternalError())
            
        else:
            raise TypeError
        
    def decode(self, str_req=''):
        """
        Takes a JSON encoded string and outputs a 2-tuple of the requests and responses contained therein
        
        If str_req is empty, it will assume the object was instantiated with the string json rpc requeset
        """

        requests = []
        responses = []
        
        try:
            if type(str_req) == str and str_req != '':
                req = json.loads(str_req)
            else:
                req = json.loads(self.__str_req)
            
            if type(req) == list:
                if len(req) >= 1:
                    # Iterate through each item in the list and determine if it is a request or a response
                    for sub_req in req:
                        item = self.__parse(sub_req)
                        
                        if isinstance(item, Rpc_Request):
                            requests.append(item)
                        elif isinstance(item, Rpc_Response):
                            responses.append(item)

                else:
                    self.error = InvalidRequest()    
                
            elif type(req) == dict:
                # Single request
                item = self.__parse(req)
                
                if isinstance(item, Rpc_Request):
                    requests.append(item)
                elif isinstance(item, Rpc_Response):
                    responses.append(item)
            
            else:
                self.error = ParseError()
            
        except ValueError:
            # No JSON object could be decoded
            self.error = ParseError()
            
        if str_req == '':
            self.requests = requests
            self.responses = responses
            
        return (requests, responses)
        
    def encode(self, e_list=None):
        # Convert the results list from Response objects into json serializable dictionaries
        if e_list == None:
            encode = self.out
        else:
            encode = e_list
            
        ret = None
        
        if self.error == None:
            if type(encode) == list:
                if len(encode) > 1:
                    # Encode a list of responses
                    ret = []
                    for index, item in enumerate(encode):
                        temp.append(item.export())
                
                elif len(encode) == 1:
                    # Encode a single response
                    ret = encode[0].export()
                
                else:
                    # Something happened and there are no valid responses
                    ret = Rpc_ErrorResponse(error=InvalidRequest())
                
            else:
                # Results must be a list
                ret = Rpc_ErrorResponse(error=InternalError())
            
        else:
            # An error likely occurred during parsing
            ret = Rpc_ErrorResponse(error=self.error)
            
        if isinstance(ret, Rpc_ErrorResponse):
            ret = ret.export()
            
        return str(json.dumps(ret)) 
            
    def __str__(self):
        return self.__str_req
        
class Rpc_Request(object):
    def __init__(self, req_id=None):

        self.error = None
        self.result = None
        
        self.id = req_id
        
    def invalid(self):
        """
        Declare a request invalid. Used by external logic if a request is declared invalid even if
        the method exists.
        
        Can be used to nullify requests unless certain conditions are met
        
        Will override any other errors that may have been set already (e.g. MethodNotFound)
        """
        self.error = InvalidRequest()
        
    def error(self, code=-32000, message=None):
        self.error = ServerError(code, message)
    
class Rpc_ValidRequest(Rpc_Request):
    def __init__(self, rpc_dict):
        super(Rpc_ValidRequest, self).__init__(rpc_dict.get('id'))
        
        self.method = str(rpc_dict.get("method", "")) # Required
        self.params = rpc_dict.get("params", [])
        
    def force_result(self, result_obj):
        # Bypass the call and force the request to return a certain result
        self.result = Rpc_ResultResponse(id=self.id, result=result_obj)
        
    def isCallable(self):
        if self.error == None and self.result == None:
            return True
        else:
            return False
        
    def getResponse(self):
        if self.error != None:
            return Rpc_ErrorResponse(error=self.error)
        
        elif self.result != None:
            return self.result
        
        else:
            return False
        
    def call(self, target):
        # Parse method        
        if not self.isCallable():
            return self.getResponse()
            
        else:
            try:
                self.method = getattr(target, self.method)
            except AttributeError:
                self.error = MethodNotFound()
                
            # Parse params
            self.params_pos = []
            self.params_named = {}
            if type(self.params) == list:
                self.params_pos = self.params
                
            elif type(self.params) == dict:
                self.params_named = self.params.get("__args", [])
                if self.params_pos:
                    del self.params["__args"]
                    self.params_named = self.params
                
            else:
                self.error = InvalidParams()
                
            # Invoke method
            if self.error == None:
                try:
                    ret = self.method(*self.params_pos, **self.params_named)
                    # Build the response with the results
                    if self.id != None:
                        # Only send a result of a notification if an error occurred
                        return Rpc_ResultResponse(id=self.id, result=ret)
                    else:
                        return None
                except:
                    return Rpc_ErrorResponse(id=self.id, error=InternalError())
            
            else:
                return self.getResponse()
    

class Rpc_InvalidRequest(Rpc_Request):
    def __init__(self, req_id, error_obj):
        super(Rpc_InvalidRequest, self).__init__(req_id)
        self.error = error_obj
    
    def call(self, target):
        return Rpc_ErrorResponse(error=self.error)
        
class Rpc_Response(object):
    def __init__(self, id=None):

        self.response = {'jsonrpc': '2.0'}
        self.response['id'] = id
    
    def __str__(self):
        # serialize the object into a json response (error or return)
        return str(json.dumps(self.response))
        
    def export(self):
        return self.response
    
class Rpc_ResultResponse(Rpc_Response):
    def __init__(self, **kwargs):
        if 'dict' in kwargs:
            super(Rpc_ResultResponse, self).__init__(kwargs['dict'].get('id'))
            self.response['result'] = kwargs['dict'].get('result')
        elif 'result' in kwargs and 'id' in kwargs:
            super(Rpc_ResultResponse, self).__init__(kwargs['id'])
            self.response['result'] = kwargs['result']
        else:
            # This shouldn't happen
            pass

class Rpc_ErrorResponse(Rpc_Response):
    def __init__(self, **kwargs):
        if 'dict' in kwargs:
            super(Rpc_ErrorResponse, self).__init__(kwargs['dict'].get('id'))
            self.response['error'] = kwargs['dict'].get('error')
        elif 'id' in kwargs:
            super(Rpc_ErrorResponse, self).__init__(kwargs['id'])
        else:
            super(Rpc_ErrorResponse, self).__init__(None)
        
        if 'error' in kwargs:
            error_obj = kwargs['error']
            self.response['error'] = {'code': error_obj.code, 'message': error_obj.message}
        
# Error Exceptions
class JSONRPCError(RuntimeError):
    code = None
    message = None
    data = None

    def __init__(self, message = None, data = None):
        RuntimeError.__init__(self)
        self.message = message or self.message
        self.data = data

class ParseError(JSONRPCError):
    code = -32700
    message = u"Invalid JSON was received by the server."

class InvalidRequest(JSONRPCError):
    code = -32600
    message = u"The JSON sent is not a valid Request object."

class MethodNotFound(JSONRPCError):
    code = -32601
    message = u"The method does not exist / is not available."

class InvalidParams(JSONRPCError):
    code = -32602
    message = u"Invalid method parameter(s)."

class InternalError(JSONRPCError):
    code = -32603
    message = u"Internal JSON-RPC error."
    
class ServerError(JSONRPCError):
    def __init__(self, code=-32000, str_msg=None):
        self.code = code
        if str_msg != None:
            self.message = str_msg
        else:
            self.message = "Undefined server error occurred"
