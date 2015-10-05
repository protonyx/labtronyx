"""
Instrument Control Protocol (ICP)
=================================

The Instrument Control Protocol was developed as a low-overhead, flexible protocol for use  with instruments over an
Ethernet network.

Detailed Operation
------------------

The ICP thread manages communication in and out of the network socket on port 
7968.

Message Queue
^^^^^^^^^^^^^

Packets to send out to remote devices are queued in the message queue and sent
one at a time. Queuing a message requires:

  * IP Address
  * TTL (Time to Live)
  * Response Queue
  * ICP Packet Object

The response packet object will be loaded into the response queue.

Routing Map
^^^^^^^^^^^

When a message is sent, it is assigned an ID within the packet header. If a
response is expected from an outgoing packet, an entry is made in the map
table to associate the packet ID of the response packet with the object that
sent the original packet.

The Arbiter will periodically scan the routing map for old entries. If an
entry has exceeded the TTL window, a signal is sent to the originating
object that a timeout condition has occurred. 

The Packet ID is an 8-bit value, so there are 256 possible ID codes. A 
Packet ID of 0x00 is reserved for "notification" packet where a response is 
not expected, and thus will never create an entry in the routing map, giving 
a maximum of 255 possible entries in the routing map.

The routing map has the format: { PacketID: Address }

Execution Strategy
^^^^^^^^^^^^^^^^^^

The arbiter will alternate between servicing the message queue, processing 
any data in the __socket buffer, and checking the status of entries in the 
routing map. If none of those tasks requires attention, the thread will 
sleep for a small time interval to limit loading the processor excessively.
"""

from labtronyx.bases.interface import Base_Interface
from labtronyx.bases.resource import Base_Resource
from labtronyx.common.errors import *

import time
import socket
import select
import threading
import Queue
from sets import Set
import errno
import struct
import time
import binascii

import numpy

info = {
    # Interface Author
    'author':               'KKENNEDY',
    # Interface Version
    'version':              '1.0',
    # Revision date
    'date':                 '2015-10-05'
}

#===========================================================================
# data_types_pack = {
#     'int8': lambda data: struct.pack('!b', int(data)),
#     'int16': lambda data: struct.pack('!h', int(data)),
#     'int32': lambda data: struct.pack('!i', int(data)),
#     'int64': lambda data: struct.pack('!q', int(data)),
#     'float': lambda data: struct.pack('!f', float(data)),
#     'double': lambda data: struct.pack('!d', float(data)) }
# 
# data_types_unpack = {
#     'int8': lambda data: struct.unpack('!b', data)[0],
#     'int16': lambda data: struct.unpack('!h', data)[0],
#     'int32': lambda data: struct.unpack('!i', data)[0],
#     'int64': lambda data: struct.unpack('!q', data)[0],
#     'float': lambda data: struct.unpack('!f', data)[0],
#     'double': lambda data: struct.unpack('!d', data)[0] }
#===========================================================================

class i_ICP(Base_Interface):
    """
    Instrument Control Protocol (ICP) Interface
    """

    info = {
        # Interface Name
        'interfaceName':    'ICP'
    }
    
    DEBUG_INTERFACE_ICP = True
    
    # Dict: ResID -> Resource Object
    _resources = {}
    
    # Config
    # TODO: Find a way to generate the broadcast IP
    broadcastIP = '192.168.1.255'
    DEFAULT_PORT = 7968
    
    e_conf = threading.Event()

    def open(self):
        # Init
        self.__messageQueue = Queue.Queue()
        self.__routingMap = {} # { PacketID: ResID }
        self.__expiration = {} # { PacketID: Expiration time }
        self.__nextID = 0
        self.__queue_lock = threading.Lock()
        
        # Configure Socket
        # IPv4 UDP
        try:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.__socket.bind(('', self.DEFAULT_PORT))
            self.__socket.setblocking(0)
            self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            _, port = self.__socket.getsockname()
            
            self.logger.info("ICP Socket Bound to port %i", port)
            
            self.refresh()
            
        except socket.error as e:
            if e.errno in [errno.EADDRINUSE]:
                self.logger.error("ICP Socket In Use")
                return False

        except:
            self.logger.exception("ICP Unhandled Exception")
            return False
            
        self.e_conf.set()
        
        return True
    
    def close(self):
        try:
            self.__socket.shutdown(1)
            self.__socket.close()
        except:
            pass
        
        self.e_conf.clear()
        
    def run(self):
        self.last_update = 0
        
        while (self.e_alive.isSet()):
            if not self.e_conf.isSet():
                continue
            
            # Auto-discover
            if time.time() - self.last_update > 30.0:
                self.last_update = time.time()
                self.refresh()
             
            try:
                #===================================================================
                # Service the socket
                #===================================================================
                self._serviceSocket()
                
                #===================================================================
                # Service the message queue
                #===================================================================
                self._serviceQueue()
                
            except socket.error as e:
                if e.errno == errno.EACCES:
                    # Permission denied
                    self.logger.error('Unable to send: permission denied. Check firewall policy')
                    self.e_alive.clear()
                
            except:
                self.logger.exception("ICP Thread Exception")
    
    def getResources(self):
        return self._resources
    
    def getAddress(self):
        return self.__socket.getsockname()
    
    #===========================================================================
    # Resource Management
    #===========================================================================
    
    def refresh(self):
        """
        Queues a broadcast discovery packet. The arbiter will automatically
        update the resource table as responses come in. 
        
        :returns: None
        """
        address = self.broadcastIP
        
        packet = DiscoveryPacket()
        packet.setDestination(address)
        
        self.queuePacket(packet, 10.0)
        
    def addResource(self, resID):
        """
        Treats an addResource request as a hint that a device exists. Attempts
        to send a discovery packet to the device to get more information.
        
        The ICP thread will automatically handle the creation of an
        instrument for the new resource.
        
        :param resID: Resource ID (IP Address)
        :type resID: str
        :returns: bool. True if successful, False otherwise
        """
        packet = DiscoveryPacket()
        packet.setDestination(resID)
        
        self.queuePacket(packet, 10.0)

    #===========================================================================
    # def _getInstrument(self, resID):
    #     return self.icp_manager.getDevice(resID)
    #     
    # def _getDevice(self, resID):
    #     return self.icp_manager.getDevice(resID)
    #===========================================================================
    
    def queuePacket(self, packet_obj, ttl):
        """
        Insert a packet into the queue. If unable to queue packet, raises Full
         
        :param packet_obj: ICP Packet Object
        :type packet_obj: ICP_Packet
        :param ttl: Time to Live (seconds)
        :type ttl: float
        :returns: packetID or none if unable to queue message
        """
        with self.__queue_lock:
            try:
                 
                # Assign a PacketID
                packetID = self.__nextID
                
                # Increment next packet ID
                self.__nextID = (self.__nextID + 1) % 256
                 
                packet_obj.setPacketID(packetID)
                     
                self.__messageQueue.put(packet_obj, False)
                
                return packetID
             
            except KeyError:
                # No IDs available
                raise Queue.Full
             
            except Queue.Full:
                # Failed to add to queue
                raise
        
    def _serviceSocket(self):
            read, _, _ = select.select([self.__socket],[],[], 0.1)
            
            if self.__socket in read:
                data, address = self.__socket.recvfrom(4096)
                sourceIP, sourcePort = address
            
                try:
                    resp_pkt = ICP_Packet(packet_data=data)
                    packetID = resp_pkt.getPacketID()
                    packetType = resp_pkt.getPacketType()
                    packetTypeClass = packet_types.get(packetType)
                    
                    if packetTypeClass is not None:
                        pkt = packetTypeClass(packet_data=data, source=sourceIP)
                    
                    # Debug output
                    if self.DEBUG_INTERFACE_ICP:
                        self.logger.debug("ICP RX [ID:%i, TYPE:%X, SIZE:%i] from %s", 
                                          packetID, packetType, len(resp_pkt.getPayload()), 
                                          sourceIP)
                    
                    # Route Packets by type
                    if packetTypeClass is None:
                        self.logger.error("ICP RX [ID:%i] INVALID PACKET TYPE: %s", packetType)
                        
                    elif packetTypeClass == EnumerationPacket:
                        # Create new device if resource doesn't already exist
                        if sourceIP not in self._resources.keys():
                            self._resources[sourceIP] = r_ICP(manager=self.manager,
                                                             interface=self,
                                                             resID=sourceIP,
                                                             logger=self.logger,
                                                             enumeration=pkt.getEnumeration())
                        
                            self.logger.info("Found ICP Device: %s" % sourceIP)
                            
                            self.manager._cb_new_resource()
                            
                    elif sourceIP in self._resources.keys():
                        # Let the resource process the packet
                        dev = self._resources.get(sourceIP)
                            
                        dev._processResponse(resp_pkt)
                            
                    else:
                        self.logger.error("ICP RX [ID:%i] NO RESOURCE TO ROUTE", packetID)
                        
                except ICP_Invalid_Packet:
                    self.logger.error("ICP RX Invalid Packet")
                
                #except:
                    # Pass on all errors for the time being
                    #pass
                
    def _serviceQueue(self):
        """
        :returns: bool - True if the queue was not empty, False otherwise
        """
        if not self.__messageQueue.empty():
            try:
                packet_obj = self.__messageQueue.get_nowait()
                
                if issubclass(packet_obj.__class__, ICP_Packet):
                    destination = packet_obj.getDestination()
                    
                    # Assign a packet ID
                    packetID = packet_obj.PACKET_ID
                    
                    # Pack for transmission
                    packet = packet_obj.pack()
                    
                    # Override broadcast address if necessary
                    if destination == "<broadcast>":
                        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                            
                    else:
                        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
                    
                    # Transmit
                    self.__socket.sendto(packet, (destination, self.DEFAULT_PORT))
                    
                    if self.DEBUG_INTERFACE_ICP:
                        self.logger.debug("ICP TX [ID:%i] to %s", packetID, destination)
                    
                else:
                    return True
                
            except KeyError:
                # No IDs available
                return True
            
            except Queue.Empty:
                return False
            
        else:
            return False

    
class r_ICP(Base_Resource):
    """
    Resource class for ICP devices. Used by Drivers to communicate with ICP
    devices over the network. 
    """
    
    type = "ICP"
    
    CR = '\r'
    LF = '\n'
    termination = LF
    
    timeout = 5.0
    
    def __init__(self, manager, interface, resID, **kwargs):
        Base_Resource.__init__(self, manager, interface, resID, **kwargs)
        
        self.address = resID
        
        if 'enumeration' in kwargs:
            self.vendor, self.model = kwargs.get('enumeration')
        else:
            self.vendor = ''
            self.model = ''
            
        if self.model == 'ETH_ADAPTER':
            self.type = "Serial"
        
        self.incomingPackets = dict()
        
        self.serialStream = str()
        
    def _processResponse(self, pkt):
        """
        Called by the controller thread when a response packet is
        received that originated from this instrument.
        """
        packetID = pkt.PACKET_ID
        
        if isinstance(pkt, SerialDescriptorPacket):
            new_data = pkt.getData()
            self.serialStream += str(new_data)
        
        else:
            self.incomingPackets[packetID] = pkt
        
    def _getResponse(self, packetID, block=False, timeout=10.0):
        """
        Get a response packet from the incoming packet queue. Non-blocking
        unless block is set to True.
        
        :param packetID: PacketID of desired packet
        :type packetID: int
        :param block: Block until packet is received or timeout occurs
        :type block: bool
        :returns: ICP_Packet object or None if no response
        """
        if block:
            start = time.time()
            while (time.time() < start + timeout):
                ret = self._getResponse(packetID, block=False)
                
                if ret is not None:
                    return ret
                
            raise ICP_Timeout()
        
        else:
            try:
                pkt = self.incomingPackets.pop(packetID)
            
                if isinstance(pkt, ErrorPacket):
                    raise ICP_DeviceError(pkt)
                
                else:
                    return pkt
                
            except KeyError:
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
    
    def getProperties(self):
        def_prop = Base_Resource.getProperties(self)
        
        def_prop.setdefault('deviceVendor', self.vendor)
        def_prop.setdefault('deviceModel', self.model)
        
        return def_prop
    
    #===========================================================================
    # Resource State
    #===========================================================================
        
    def open(self):
        address = socket.gethostbyname(socket.gethostname())
        oct = address.split('.')
        oct = map(int, oct)
        
        nbo_address = (oct[0]) | (oct[1] << 8) | (oct[2] << 16) | (oct[3] << 24)
        
        self.register_write(0xA, nbo_address)
        
        ret = self.register_read(0xA)
        self.logger.debug('ICP OPEN: %X', ret)
        
    def isOpen(self):
        return False
    
    def close(self):
        pass
        
    #===========================================================================
    # Device State
    #===========================================================================
    
    def getState(self):
        """
        Query the ICP Device for the current state.
        
        :returns: int
        """
        packet = StateChangePacket(state=0,
                                       destination=self.address)

        try:
            packetID = self.interface.queuePacket(packet, 10.0)
            
            pkt = self._getResponse(packetID, block=True)
            return pkt.getState()
            
        except ICP_Timeout:
            return None
        
    def setState(self, new_state):
        packet = StateChangePacket(state=new_state,
                                       destination=self.address)
        
        try:
            packetID = self.interface.queuePacket(packet, 10.0)
            
            pkt = self._getResponse(packetID, block=True)
            return pkt.getState()
            
        except ICP_Timeout:
            return None
        
    #===========================================================================
    # Serial Data Operations
    #===========================================================================
    
    def configure(self, **kwargs):
        """
        Configure Serial port parameters for the resource.
        
        :param baudrate: Serial - Baudrate. Default 9600
        :param timeout: Read timeout
        :param bytesize: Serial - Number of bits per frame. Default 8.
        :param parity: Serial - Parity
        :param stopbits: Serial - Number of stop bits
        :param termination: Write termination
        """
        if 'baudrate' in kwargs:
            self.instrument.setBaudrate(int(kwargs.get('baudrate')))
            
        if 'timeout' in kwargs:
            self.instrument.setTimeout(float(kwargs.get('timeout')))
            
        if 'bytesize' in kwargs:
            self.instrument.setByteSize(int(kwargs.get('bytesize')))
            
        if 'parity' in kwargs:
            self.instrument.setParity(kwargs.get('parity'))
            
        if 'stopbits' in kwargs:
            self.instrument.setStopbits(int(kwargs.get('stopbits')))
            
        if 'termination' in kwargs:
            self.termination = kwargs.get('termination')
            
    def getConfiguration(self):
        return self.instrument.getSettingsDict()
    
    def write(self, data, termination='\n'):
        packet = SerialDescriptorPacket(destination=self.address,
                                        data=(data+str(termination)))
        packetID = self.interface.queuePacket(packet, 1.0)
        
    def write_raw(self, data):
        packet = SerialDescriptorPacket(destination=self.address,
                                        data=data)
        packetID = self.interface.queuePacket(packet, 1.0)
        
    def read(self):
        ret = ''
        
        if self.termination is None:
            ret = self.serialStream
            self.serialStream = ''
        
        else:
            start = time.time()
            while (time.time() < start + self.timeout):
                index = self.serialStream.find(self.termination) #self.instrument.read(1)
                
                if index != -1:
                    ret = self.serialStream[:(index+len(self.termination))]
                    self.serialStream = self.serialStream[(index+len(self.termination)):]
                    return ret
                else:
                    pass
                
        return ret

    def read_raw(self, size=1):
        ret = ''
        start = time.time()
        while (time.time() < start + self.timeout):
            if len(self.serialStream) >= size:
                ret = self.serialStream[:size]
                self.serialStream = self.serialStream[size:]
            
        return ret
    
    def query(self, data):
        self.write(data)
        return self.read()
            
    def inWaiting(self):
        return len(self.serialStream)
    
    #===========================================================================
    # Register Operations
    #===========================================================================
    
    def register_write(self, address, data):
        """
        Write a value to a register. Blocking operation.
            
        :param address: 16-bit address
        :type address: int
        :param data: Data to write
        :type data: variable
        """
        try:
            packet = RegisterWritePacket(address=address,
                                             data=data,
                                             destination=self.address)
        
            packetID = self.interface.queuePacket(packet, 10.0)
            
        except ICP_DeviceError as e:
            epkt = e.get_errorPacket()
            
            print epkt.getError()
            print epkt.getMessage()
                
        except ICP_Timeout:
            raise InterfaceTimeout()
        
    def register_read(self, address):
        """
        Read a value from a register. Blocks until data returns.
        
        :param address: 16-bit address
        :type address: int
        :returns: str
        """
        packet = RegisterReadPacket(address=address,
                                        destination=self.address)
        
        packetID = self.interface.queuePacket(packet, 10.0)
        
        try:
            data = self._getResponse(packetID, block=True)
            
            return data.getData()
            
        except ICP_DeviceError as e:
            epkt = e.get_errorPacket()
            
            print epkt.getError()
            print epkt.getMessage()
                
        except ICP_Timeout:
            raise InterfaceTimeout()

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
    0x05: 'uint8',
    0x06: 'uint16',
    0x07: 'uint32',
    0x08: 'uint64',
    0x10: 'float',
    0x11: 'double'
    }

data_format_struct = {
    'string': 's',
    'int8': 'b',
    'int16': 'h',
    'int32': 'i',
    'int64': 'q',
    'uint8': 'B',
    'uint16': 'H',
    'uint32': 'I',
    'uint64': 'Q',
    'float': 'f',
    'double': 'd'
    }

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
                raise ICP_Invalid_Packet

            if len(data) > self.header_size:
                self.PAYLOAD = data[self.header_size:]

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

    def _strip(self, data):
        # Strip control codes and null terminators from data
        return ''.join([x for x in data if 31 < ord(x) < 127 or x in ['\r', '\n', '\t']])

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
        #if type(self.PAYLOAD) is not bytearray:
        #    self.PAYLOAD = bytearray(self.PAYLOAD)

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

        self.vendor = self._strip(str(self.data[0:31]))
        self.model = self._strip(str(self.data[32:63]))

        packet_types = self.data[64:]
        if len(packet_types) == 64:
            packet_types = struct.unpack('h'*32, packet_types)
            self.packet_types = list(set(packet_types)) # Get unique values

    def getEnumeration(self):
        return (self.vendor, self.model)

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
        try:
            self.error, self.msg = struct.unpack(self.payload_format, self.getPayload())
        except:
            self.error = 0xFFFFFFFF
            self.msg = 'Unknown Error'

    def getError(self):
        return self.error

    def getMessage(self):
        return self.msg

#===============================================================================
# Device Packets
#===============================================================================

class ResponsePacket(ICP_Packet):
    PACKET_TYPE = 0x80

    payload_format = 'xBxB'

    def _parse(self):
        payload = self.getPayload()

        self.format, elems = struct.unpack(self.payload_format, payload[0:4])
        data = payload[4:]

        if elems > 0:
            try:
                data_code = data_format_codes.get(self.format, 'string')
                data_unpack_code = data_format_struct.get(data_code, 's')
                fmt = data_unpack_code * elems

                data_size = struct.calcsize(fmt)
                self.data = struct.unpack(fmt, data[:data_size])

            except:
                self.data = self._strip(data)

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
        return self._strip(self.getPayload())

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

packet_types = {
    0x00: DiscoveryPacket,
    0x01: EnumerationPacket,
    0x02: HeartbeatPacket,
    0x03: StateChangePacket,
    0x0F: ErrorPacket,
    0x80: ResponsePacket,
    0x81: CommandPacket,
    0x82: RegisterReadPacket,
    0x83: RegisterWritePacket,
    0x88: SerialDescriptorPacket,
    0x89: CANDescriptorPacket
}