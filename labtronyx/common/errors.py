class GeneralError(RuntimeError):
    """
    Base class for Labtronyx errors
    """
    pass

class InvalidResponse(GeneralError):
    pass

class DeviceError(GeneralError):
    pass

class InterfaceUnavailable(GeneralError):
    """
    The interface could not be opened because it is unavailable. Possible causes:

       * A library is missing or not installed
       * An error occurred while accessing the interface
    """
    pass

class InterfaceError(GeneralError):
    """
    Generic error for an exception that occurred during a low-level interface operation.
    """
    pass

class InterfaceTimeout(GeneralError):
    """
    A timeout condition occurred during data transmission, data was not received within the timeout window.
    """
    pass

class ResourceUnavailable(GeneralError):
    """
    The Resource could not be opened because it is unavailable. Possible causes:

       * Resource is in use by another program
       * Resource is locked by the system
       * Resource does not actually exist or is no longer connected to the system
    """
    pass

class ResourceNotOpen(GeneralError):
    """
    Operation could not be processed because the resource is not open. Try calling `open` before attempting this
    operation again
    """
    pass