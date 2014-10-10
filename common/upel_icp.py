import struct
import Queue
"""
Conforms to Rev 1.0 of the UPEL Instrument Control Protocol

Author: Kevin Kennedy
"""

    
class UPEL_ICP_Device(object):
    """
    Instrument class for ICP devices. Used by Models to communicate with ICP
    devices over the network. 
    """
    
    def __init__(self, address, arbiter):
        """
        :param address: IPv4 Address
        :type address: str
        """
        self.address = address
        self.arbiter = arbiter
        
        self.packetQueue = Queue.Queue()
        
    def _getResponse(self, timeout):
        try:
            pkt = self.packetQueue.get(True, timeout)
            
            if isinstance(pkt, ErrorPacket):
                raise ICP_DeviceError(pkt);
            
            return str(pkt.getPayload())
            
        except Queue.Empty:
            raise ICP_Timeout
        
    #===========================================================================
    # Device State
    #===========================================================================
    
    def getState(self):
        packet = StateChangePacket(0)
        
        self.arbiter.queueMessage(self.address, 10.0, packet)
        
        try:
            return self._getResponse(10.0)
            
        except ICP_Timeout:
            return None
        
    def setState(self, new_state):
        packet = StateChangePacket(new_state)
        
        self.arbiter.queueMessage(self.address, 10.0, packet)
        
        try:
            return self._getResponse(10.0)
            
        except ICP_Timeout:
            return None
    
    #===========================================================================
    # Register Operations
    #===========================================================================
    
    def writeReg(self, address, subindex, data):
        """
        Write a value to a register.
        
        :warning::
        
            Binary data cannot be encoded for network transmission from a Model.
            Models should use the appropriate writeReg function for the desired
            data type to avoid raising exceptions or corrupting data.
        """
        packet = RegisterWritePacket(address, subindex, data)
        
        self.arbiter.queueMessage(self.address, 60.0, packet)
        
        try:
            return self._getResponse(60.0)
            
        except ICP_Timeout:
            return None
        
    def writeReg_int8(self, address, subindex, data):
        data_enc = struct.pack('b', int(data))
        return self.writeReg(address, subindex, data_enc)
    
    def writeReg_int16(self, address, subindex, data):
        data_enc = struct.pack('h', int(data))
        return self.writeReg(address, subindex, data_enc)
    
    def writeReg_int32(self, address, subindex, data):
        data_enc = struct.pack('i', int(data))
        return self.writeReg(address, subindex, data_enc)
    
    def writeReg_int64(self, address, subindex, data):
        data_enc = struct.pack('q', int(data))
        return self.writeReg(address, subindex, data_enc)
    
    def writeReg_float(self, address, subindex, data):
        data_enc = struct.pack('f', float(data))
        return self.writeReg(address, subindex, data_enc)
    
    def writeReg_double(self, address, subindex, data):
        data_enc = struct.pack('d', float(data))
        return self.writeReg(address, subindex, data_enc)
    
    def readReg(self, address, subindex):
        """
        Read a register. Interpret as string
        
        :warning::
        
            Binary data cannot be encoded for network transmission from a Model.
            Models should use the appropriate readReg function for the desired
            data type to avoid raising exceptions. 
        
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        :returns: str
        """
        packet = RegisterReadPacket(address, subindex)
        
        self.arbiter.queueMessage(self.address, 60.0, packet)
        
        try:
            return self._getResponse(60.0)
            
        except ICP_Timeout:
            return None
        
    def readReg_int8(self, index, subindex):
        reg = self.readReg(index, subindex)
        reg_up = struct.unpack('b', reg)[0]
        return reg_up
        
    def readReg_int16(self, index, subindex):
        reg = self.readReg(index, subindex)
        reg_up = struct.unpack('h', reg)[0]
        return reg_up
        
    def readReg_int32(self, index, subindex):
        reg = self.readReg(index, subindex)
        reg_up = struct.unpack('i', reg)[0]
        return reg_up
    
    def readReg_int64(self, index, subindex):
        reg = self.readReg(index, subindex)
        reg_up = struct.unpack('q', reg)[0]
        return reg_up
    
    def readReg_float(self, index, subindex):
        reg = self.readReg(index, subindex)
        reg_up = struct.unpack('f', reg)[0]
        return reg_up
    
    def readReg_double(self, index, subindex):
        reg = self.readReg(index, subindex)
        reg_up = struct.unpack('d', reg)[0]
        return reg_up
    
    #===========================================================================
    # Process Data Operations
    #===========================================================================
    
    def readProc(self, address):
        pass
    
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
    
    def isResponse(self):
        return bool(self.CONTROL & 0x80)
    
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
    def __init__(self, address, subindex):
        self.PACKET_TYPE = 0x8
        self.PAYLOAD = str(struct.pack('HxB', address, subindex))

class RegisterWritePacket(UPEL_ICP_Packet):
    def __init__(self, address, subindex, data):
        self.PACKET_TYPE = 0x9
        self.PAYLOAD = str(struct.pack('HxB', address, subindex)) + str(data)

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

class ICP_Timeout(RuntimeError):
    pass

class ICP_DeviceError(RuntimeError):
    def __init__(self, error_packet=None):
        self.error_packet = error_packet
        
    def get_errorPacket(self):
        return self.error_packet


