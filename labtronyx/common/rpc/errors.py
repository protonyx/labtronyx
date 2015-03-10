from jsonrpc import *

#===============================================================================
# Errors
#===============================================================================

class RpcError(RuntimeError):
    pass

class RpcServerPortInUse(RpcError):
    pass

class RpcServerNotFound(RpcError):
    pass

class RpcServerUnresponsive(RpcError):
    pass

class RpcTimeout(RpcError):
    pass

class RpcServerException(RpcError):
    pass

class RpcInvalidPacket(RpcError):
    pass

class RpcMethodNotFound(RpcError):
    pass

JsonRpc_to_RpcErrors = {JsonRpc_ParseError: RpcInvalidPacket,
                      JsonRpc_InvalidRequest: RpcInvalidPacket,
                      JsonRpc_MethodNotFound: RpcMethodNotFound,
                      JsonRpc_InvalidParams: RpcServerException,
                      JsonRpc_InternalError: RpcError,
                      JsonRpc_ServerException: RpcServerException}
    

