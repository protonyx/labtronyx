import struct
import time 

from . import errors

status_codes = {
    0x00: 'IDLE',
    0x01: 'RUNNING',
    0x02: 'STOP',
    0x80: 'INIT',
    0x81: 'RESET'
    }

data_format_codes = {
    0x00: 'string',
    0x01: 'int8',
    0x02: 'int16',
    0x03: 'int32',
    0x04: 'int64',
    0x10: 'float',
    0x11: 'double'
    }

data_format_struct = {
    'string': 's',
    'int8': 'b',
    'int16': 'h',
    'int32': 'i',
    'int64': 'q',
    'float': 'f',
    'double': 'd'}

#===============================================================================
# Packet Base Class
#===============================================================================

class ICP_Packet:
    """
    Base class for all ICP packets. Packs header information before transmission
    """
    header_format = 'IBBH'
    header_size = struct.calcsize(header_format)
    
    PACKET_ID = 0x0
    PACKET_TYPE = 0x0
    
    PAYLOAD = bytearray()
    
    def __init__(self, **kwargs):
        self.args = kwargs
        
        self.source = kwargs.get('source')
        self.destination = kwargs.get('destination')
        self.timestamp = time.time()
        
        data = kwargs.get('packet_data')
        if data is not None and len(data) >= self.header_size:
            # Unpack the data
            header = data[:self.header_size]
            header_up = struct.unpack(self.header_format, header)
            
            identifier, self.PACKET_TYPE, self.PACKET_ID, pkt_payload_size = header_up
            
            if identifier != 0x4C455055:
                raise errors.ICP_Invalid_Packet
            
            if len(data) > self.header_size:
                self.PAYLOAD = data[self.header_size:(self.header_size+8)]
                
            self._parse()
                
        else:
            self.PACKET_ID = kwargs.get('id', 1)
            
            self._format()
        
    def _format(self):
        """
        Called when the object was created empty
        """
        pass
        
    def _parse(self):
        """
        Called when the object was created with packet data from the network
        """
        pass
    
    def setPacketID(self, id):
        self.PACKET_ID = id
        
    def getPacketID(self):
        return self.PACKET_ID
    
    def getPacketType(self):
        return self.PACKET_TYPE
                
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
    
    def setPayload(self, data):
        self.PAYLOAD = data
    
    def getTimestamp(self):
        return self.timestamp
    
    def pack(self):
        """
        Pack the header and payload
        """
        # Enforce PAYLOAD type as bytearray
        if type(self.PAYLOAD) is not bytearray:
            self.PAYLOAD = bytearray(self.PAYLOAD)
            
        payloadSize = len(self.PAYLOAD)
        headerFormat = self.header_format + str('%is' % (payloadSize))
            
        header = struct.pack(self.header_format, 0x4C455055, self.PACKET_TYPE, self.PACKET_ID, payloadSize) 
        return header + str(self.PAYLOAD)
    
#===============================================================================
# Core Protocol Packet Types
#===============================================================================

class DiscoveryPacket(ICP_Packet):
    PACKET_TYPE = 0x00
    
class EnumerationPacket(ICP_Packet):
    PACKET_TYPE = 0x01
    
    def _parse(self):
        # TODO: Should this try to parse as JSON data?
        self.data = self.getPayload()
        
        self.vendor = str(self.data[0:31]).strip()
        self.model = str(self.data[32:63]).strip()
        
        packet_types = self.data[64:]
        if len(packet_types) == 64:
            packet_types = struct.unpack('h'*32, packet_types)
            self.packet_types = list(set(packet_types)) # Get unique values
    
    def getSuuportedPacketTypes(self):
        return self.packet_types
    
class HeartbeatPacket(ICP_Packet):
    PACKET_TYPE = 0x02
        
class StateChangePacket(ICP_Packet):
    PACKET_TYPE = 0x03
    
    payload_format = 'xxxB'
    
    def _format(self):
        self.state = self.args.get('state')
        data = struct.pack(self.payload_format, self.state)
        self.setPayload(data)
    
    def _parse(self):
        self.state = struct.unpack(self.payload_format, self.getPayload())
        
    def getState(self):
        return self.state

class ErrorPacket(ICP_Packet):
    PACKET_TYPE = 0x0F
    
    payload_format = 'Is'
    
    def _format(self):
        self.error = int(self.args.get('error'))
        self.msg = self.args.get('message')
        data = struct.pack(self.payload_format, self.error, self.msg)
        self.setPayload(data)
    
    def _parse(self):
        self.error, self.msg = struct.unpack(self.payload_format, self.getPayload())
        
    def getError(self):
        return self.error
    
    def getMessage(self):
        return self.msg

#===============================================================================
# Device Packets
#===============================================================================

class ResponsePacket(ICP_Packet):
    PACKET_TYPE = 0x80
    
    payload_format = 'xBxBs'
    
    def _parse(self):
        self.format, elems, data = struct.unpack(self.payload_format, self.getPayload())
        data_code = data_format_codes.get(self.format, 'string')
        data_unpack_code = data_format_struct.get(data_code, 's')
        
        self.data = struct.unpack(data_unpack_code * elems, data)
    
    def getData(self):
        return self.data

class CommandPacket(ICP_Packet):
    PACKET_TYPE = 0x81
    
    def _format(self):
        self.setPayload(self.args.get('data'))

class RegisterReadPacket(ICP_Packet):
    PACKET_TYPE = 0x82
    
    payload_format = 'H'
    
    def _format(self):
        data = struct.pack(self.payload_format, self.args.get('address'))
        self.setPayload(data)

class RegisterWritePacket(ICP_Packet):
    PACKET_TYPE = 0x83
    
    payload_format = 'HxxI'
    
    def _format(self):
        data = struct.pack(self.payload_format, 
                           self.args.get('address'),
                           self.args.get('data'))
        self.setPayload(data)

class SerialDescriptorPacket(ICP_Packet):
    PACKET_TYPE = 0x88
    
    def _format(self):
        self.setPayload(self.args.get('data'))
        
    def getData(self):
        return self.getPayload()
    
class CANDescriptorPacket(ICP_Packet):
    PACKET_TYPE = 0x89
    
    payload_format = 'IQ'
    
    def _format(self):
        self.message_id = self.args.get('message_id')
        self.data = self.args.get('data')
        data = struct.pack(self.payload_format,
                           self.message_id,
                           self.data)
        self.setPayload(data)
        
    def _parse(self):
        self.message_id, self.data = struct.unpack(self.payload_format, self.getPayload())
        
    def getMessageID(self):
        return self.message_id
    
    def getData(self):
        return self.data

