
import json

"""
JSON RPC Python class

Follows the JSON RPC 2.0 Spec (http://www.jsonrpc.org/specification)

This class can either be instantiated with a JSON encoded string or used as a utility helper class
"""

def parseJsonRpc(rpc_dict):
    """
    Takes a dictionary and determines if it is an RPC request or response
    """
    from common.rpc import Rpc_Request, Rpc_Response, Rpc_InvalidRequest
    
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
                    return Rpc_Response(id=rpc_dict['id'], error=rpc_dict['error'])
                        
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
    
def decode(str_req):
    """
    Takes a string and returns:
    
    tuple of lists of Rpc_Request and Rpc_Response objects
    """
    from common.rpc import Rpc_Request, Rpc_Response, Rpc_ParseError, Rpc_InvalidRequest

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
    
def encode(toEncode):
    """
    Convert a list of Rpc_Request and Rpc_Result objects into a JSON RPC string for transmission
    """
    from common.rpc import Rpc_Error, Rpc_ParseError, Rpc_InvalidRequest
        
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
            
            if 'error' in item_dict.keys():
                item_dict['error'] = errorToDict(item_dict['error'])
            
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

def errorToDict(Rpc_Error_obj):
    from common.rpc import Rpc_Error, Rpc_ParseError, Rpc_InvalidRequest, Rpc_MethodNotFound, Rpc_InvalidParams, Rpc_InternalError
    
    if isinstance(Rpc_Error_obj, Rpc_ParseError):
        return {'code': -32700, 'message': 'Invalid JSON was received by the server.'}
    
    elif isinstance(Rpc_Error_obj, Rpc_InvalidRequest):
        return {'code': -32600, 'message': 'The JSON sent is not a valid Request object.'}
    
    elif isinstance(Rpc_Error_obj, Rpc_MethodNotFound):
        return {'code': -32601, 'message': 'The method does not exist / is not available.'}
    
    elif isinstance(Rpc_Error_obj, Rpc_InvalidParams):
        return {'code': -32602, 'message': 'Invalid method parameter(s).'}
    
    elif isinstance(Rpc_Error_obj, Rpc_InternalError):
        if Rpc_Error_obj.message is not None:
            return {'code': -32001, 'message': Rpc_Error_obj.message }
        else:
            return {'code': -32603, 'message': 'Internal JSON-RPC error.'}
    
    elif type(Rpc_Error_obj) == dict and 'code' in Rpc_Error_obj.keys() and 'message' in  Rpc_Error_obj.keys():
        return Rpc_Error_obj
    
    else:
        return {'code': -32000, 'message': 'Unidentified Internal JSON-RPC error.'}