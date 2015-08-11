
class InvalidResponse(RuntimeError):
    pass

class DeviceError(RuntimeError):
    pass

class InterfaceError(RuntimeError):
    pass

class InterfaceTimeout(RuntimeError):
    pass

class ResourceNotReady(RuntimeError):
    pass

class ResourceNotOpen(RuntimeError):
    pass