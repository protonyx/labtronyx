import struct
import time
"""
Conforms to Rev 1.0 of the UPEL Instrument Control Protocol

Author: Kevin Kennedy
"""

    
class UPEL_ICP_Device(object):
    """
    Instrument class for ICP devices. Used by Models to communicate with ICP
    devices over the network. 
    """
    
    data_types_pack = {
        'int8': lambda data: struct.pack('b', int(data)),
        'int16': lambda data: struct.pack('h', int(data)),
        'int32': lambda data: struct.pack('i', int(data)),
        'int64': lambda data: struct.pack('q', int(data)),
        'float': lambda data: struct.pack('f', float(data)),
        'double': lambda data: struct.pack('d', float(data)) }
    
    data_types_unpack = {
        'int8': lambda data: struct.unpack('b', data)[0],
        'int16': lambda data: struct.unpack('h', data)[0],
        'int32': lambda data: struct.unpack('i', data)[0],
        'int64': lambda data: struct.unpack('q', data)[0],
        'float': lambda data: struct.unpack('f', data)[0],
        'double': lambda data: struct.unpack('d', data)[0] }
    
    def __init__(self, address, arbiter):
        """
        :param address: IPv4 Address
        :type address: str
        """
        self.address = address
        self.arbiter = arbiter
        
        self.incomingPackets = {}
        
    def _processTimeout(self, packetID):
        """
        Called by the controller thread when a sent packet is considered
        expired
        """
        self.incomingPackets[packetID]= ICP_Timeout
        
    def _processResponse(self, pkt):
        """
        Called by the controller thread when a response packet is
        received that originated from this instrument.
        """
        packetID = pkt.PACKET_ID
        
        self.incomingPackets[packetID] = pkt
        
    def _getResponse(self, packetID, data_type):
        """
        Get 
        :returns: UPEL_ICP_Packet object or None if no response
        """
        pkt = self.incomingPackets.get(packetID, None)
        
        if isinstance(pkt, ICP_Timeout):
            raise pkt
            
        elif pkt is not None:
            self.incomingPackets.pop(packetID)
            
            if isinstance(pkt, ErrorPacket):
                raise ICP_DeviceError(pkt)
            
            else:
                unpacker = self.data_types_unpack.get(data_type, None)
                if unpacker is not None:
                    return unpacker(pkt.getPayload())
                else:
                    return pkt.getPayload()
                
        else:
            return None
        
    #===========================================================================
    # def _getResponse(self, timeout):
    #     try:
    #         pkt = self.packetQueue.get(True, timeout)
    #         
    #         if isinstance(pkt, ErrorPacket):
    #             raise ICP_DeviceError(pkt);
    #         
    #         return str(pkt.getPayload())
    #         
    #     except Queue.Empty:
    #         raise ICP_Timeout
    #===========================================================================
        
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
    
    def queue_writeReg(self, address, subindex, data, data_type):
        """
        Queue a write operation to a register. Returns packet ID for the sent
        packet. If there are no packet IDs currently available, this call
        blocks until one is available. Otherwise, this call returns immediately.
        
        :returns: packetID
        """
        packer = self.data_types_pack.get(data_type, None)
        if packer is not None:
            data = packer(data)
            
        packet = RegisterWritePacket(address, subindex, data)
        packet.setDestination(self.address)
        
        packetID = self.arbiter.queueMessage(packet, 10.0)
        
        return packetID
    
    def writeReg(self, address, subindex, data, data_type):
        """
        Write a value to a register. Blocking operation.
        
        :warning::
        
            Binary data cannot be encoded for network transmission from a Model.
            Models should use the appropriate writeReg function for the desired
            data type to avoid raising exceptions or corrupting data.
        """
        packetID = self.queue_writeReg(address, subindex, data, data_type)
        
        if packetID is not None:
            while True:
                try:
                    data = self._getResponse(packetID, data_type)
                    
                    if data is not None:
                        return data
                
                except ICP_Timeout:
                    return None
            
    def queue_readReg(self, address, subindex, data_type):
        """
        Queue a read operation to a register. Returns packet ID for the sent
        packet. If there are no packet IDs currently available, this call
        blocks until one is available. Otherwise, this call returns immediately.
        
        :returns: packetID
        """
        packet = RegisterReadPacket(address, subindex)
        packet.setDestination(self.address)
        
        packetID = self.arbiter.queueMessage(packet, 10.0)
        
        return packetID
    
    def readReg(self, address, subindex, data_type):
        """
        Read a value from a register. Blocks until data returns.
        
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
        packetID = self.queue_readReg(address, subindex, data_type)
        
        if packetID is not None:
            while True:
                try:
                    data = self._getResponse(packetID, data_type)
                    
                    if data is not None:
                        return data
                
                except ICP_Timeout:
                    return None
    
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
                
            if self.PACKET_TYPE == 0x0:
                self.__class__ = StateChangePacket
            elif self.PACKET_TYPE == 0x1:
                self.__class__ = ErrorPacket
            elif self.PACKET_TYPE == 0x8:
                self.__class__ = RegisterReadPacket
            elif self.PACKET_TYPE == 0x9:
                self.__class__ = RegisterWritePacket
            elif self.PACKET_TYPE == 0xF:
                self.__class__ = DiscoveryPacket
                
        self.source = None
        self.destination = None
        self.timestamp = time.time()
                
    def setSource(self, source):
        self.source = source
        
    def getSource(self):
        return self.source
                
    def setDestination(self, destination):
        self.destination = destination
    
    def getDestination(self):
        return self.destination
                
    def getPayload(self):
        return self.PAYLOAD
    
    def getTimestamp(self):
        return self.timestamp
    
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


