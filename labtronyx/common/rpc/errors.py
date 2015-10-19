__all__ = ['RpcError', 'RpcServerPortInUse', 'RpcServerNotFound', 'RpcServerUnresponsive',
           'RpcTimeout', 'RpcServerException', 'RpcInvalidPacket', 'RpcMethodNotFound']

#===============================================================================
# Error Base Classes
#===============================================================================

class RpcError(RuntimeError):
    def __init__(self, *args, **kwargs):
        RuntimeError.__init__(self)
        self.id = kwargs.get('id', None)

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