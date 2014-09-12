import struct
"""
Conforms to Rev 1.0 of the UPEL Instrument Control Protocol

Author: Kevin Kennedy
"""
class UPEL_ICP_Packet:
    """
    Base class for all ICP packets. Packs header information before transmission
    """
    SPEC_NUMBER = 0x1
    CONTROL = 0x0
    
    packetID = 0x0
    packetType = 0x0
    
    
    payload = bytearray()
    
    def pack(self):
        """
        Pack the header and payload
        """
        packetIdentifier = ((self.SPEC_NUMBER<<4) | (self.packetType & 0xF)) & 0xFF
        
        # Enforce payload type as bytearray
        if type(self.payload) is not bytearray:
            self.payload = bytearray(self.payload)
            
        payloadSize = len(self.payload)
        headerFormat = '4sBBHH%is' % (payloadSize)
            
        return struct.pack(headerFormat, 'UPEL', packetIdentifier, self.CONTROL, self.packetID, payloadSize, str(self.payload))
    
class StateChangePacket(UPEL_ICP_Packet):
    def __init__(self, state):
        self.packetType = 0x0
        self.payload = struct.pack('B', state)

class ErrorPacket(UPEL_ICP_Packet):
    def __init__(self):
        self.packetType = 0x1

class HeartbeatPacket(UPEL_ICP_Packet):
    pass

class FirmwareDownloadPacket(UPEL_ICP_Packet):
    pass

class RegisterReadPacket(UPEL_ICP_Packet):
    pass

class RegisterWritePacket(UPEL_ICP_Packet):
    pass

class ProcessDataReadPacket(UPEL_ICP_Packet):
    pass

class DiscoveryPacket(UPEL_ICP_Packet):
    def __init__(self):
        self.packetType = 0xF
        self.packetID = 0x00




