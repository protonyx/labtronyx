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
    
    PACKET_ID = 0x0
    PACKET_TYPE = 0x0
    
    PAYLOAD = bytearray()
    
    def __init__(self, pkt_data=None):
        if pkt_data is not None and len(pkt_data) >= 8:
            # Unpack the data
            header = pkt_data[:8]
            header_format = 'IBBBB'
            identifier, pkt_spec_type, pkt_control, pkt_id, pkt_payload_size = struct.unpack(header_format, header)
            
            if identifier != 0x4C455055:
                raise ICP_Invalid_Packet
            
            self.CONTROL = pkt_control
            self.PACKET_ID = pkt_id
            self.PACKET_TYPE = pkt_spec_type & 0xF
            self.SPEC_NUMBER = (pkt_spec_type >> 4) & 0xF
            
            if len(pkt_data) > 8:
                self.PAYLOAD = pkt_data[8:(pkt_payload_size+8)]
                
    def getPayload(self):
        return self.PAYLOAD
    
    def pack(self):
        """
        Pack the header and PAYLOAD
        """
        packetIdentifier = ((self.SPEC_NUMBER<<4) | (self.PACKET_TYPE & 0xF)) & 0xFF
        
        # Enforce PAYLOAD type as bytearray
        if type(self.PAYLOAD) is not bytearray:
            self.PAYLOAD = bytearray(self.PAYLOAD)
            
        payloadSize = len(self.PAYLOAD)
        headerFormat = '4sBBBB%is' % (payloadSize)
            
        return struct.pack(headerFormat, 'UPEL', packetIdentifier, self.CONTROL, self.PACKET_ID, payloadSize, str(self.PAYLOAD))
    
class UPEL_ICP_Device(object):
    pass
    
class StateChangePacket(UPEL_ICP_Packet):
    def __init__(self, state):
        self.PACKET_TYPE = 0x0
        self.PAYLOAD = struct.pack('B', state)

class ErrorPacket(UPEL_ICP_Packet):
    def __init__(self):
        self.PACKET_TYPE = 0x1

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
        self.PACKET_TYPE = 0xF
        self.PACKET_ID = 0x00

#===============================================================================
# Exceptions
#===============================================================================
class ICP_Invalid_Packet(RuntimeError):
    pass


