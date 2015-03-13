# Resource Status Codes
INITIALIZE = 'INIT'
READY = 'READY'
ERROR = 'ERROR'
DELETE = 'DEL'

ERROR_BUSY = (100, 'Device is in use')
ERROR_UNRESPONSIVE = (101, 'Device Unresponsive')
ERROR_NOTFOUND = (102, 'Interface could not find resource')
ERROR_BAD_DATA = (102, 'Device returned bad data')
ERROR_DEVICE_ERROR = (200, 'Device reported an internal error')

ERROR_UNKNOWN = (999, 'Unknown Error')

class ResourceNotReady(RuntimeError):
    pass