
#===============================================================================
# Errors
#===============================================================================
class RpcServerPortInUse(Exception):
    pass

class RpcServerNotFound(Exception):
    pass

class RpcServerUnresponsive(Exception):
    pass