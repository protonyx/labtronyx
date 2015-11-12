

class LabtronyxException(RuntimeError):
    """
    Base class for Labtronyx errors
    """
    pass


class InvalidResponse(LabtronyxException):
    pass


class DeviceError(LabtronyxException):
    pass


class InterfaceUnavailable(LabtronyxException):
    """
    The interface could not be opened because it is unavailable. Possible causes:

       * A library is missing or not installed
       * An error occurred while accessing the interface
    """
    pass


class InterfaceError(LabtronyxException):
    """
    Generic error for an exception that occurred during a low-level interface operation.
    """
    pass


class InterfaceTimeout(LabtronyxException):
    """
    A timeout condition occurred during data transmission, data was not received within the timeout window.
    """
    pass


class ResourceUnavailable(LabtronyxException):
    """
    The Resource could not be opened because it is unavailable. Possible causes:

       * Resource is in use by another program
       * Resource is locked by the system
       * Resource does not actually exist or is no longer connected to the system
    """
    pass


class ResourceNotOpen(LabtronyxException):
    """
    Operation could not be processed because the resource is not open. Try calling `open` before attempting this
    operation again
    """
    pass


class RpcError(LabtronyxException):
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