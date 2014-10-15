#===============================================================================
# Exceptions
#===============================================================================

class ICP_Error(RuntimeError):
    pass

class ICP_Invalid_Packet(ICP_Error):
    pass

class ICP_Timeout(ICP_Error):
    pass

class ICP_DeviceError(ICP_Error):
    def __init__(self, error_packet=None):
        self.error_packet = error_packet
        
    def get_errorPacket(self):
        return self.error_packet