"""
UPEL Instrument Control Protocol (ICP)
======================================

Dependencies
------------

None

Detailed Operation
------------------

The UPEL ICP thread manages communication in and out of the network socket
on port 7968.

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

from Base_Interface import Base_Interface
from Base_Resource import Base_Resource

import struct
import time
import socket
import select
import threading
import Queue
from sets import Set
import errno

import numpy

import interfaces.upel as icp

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

class i_UPEL(Base_Interface):
    """
    Conforms to Rev 1.0 of the UPEL Instrument Control Protocol

    :author: Kevin Kennedy
    """
    
    info = {
        # Interface Author
        'author':               'KKENNEDY',
        # Interface Version
        'version':              '1.0',
        # Revision date
        'date':                 '2015-03-06'
    }
    
    # Dict: ResID -> Resource Object
    resources = {}
    
    # UPEL Controller Config
    broadcastIP = '192.168.1.255'
    DEFAULT_PORT = 7968
    
    e_conf = threading.Event()

    def open(self):
        # Init
        self.__messageQueue = Queue.Queue()
        self.__routingMap = {} # { PacketID: ResID }
        self.__expiration = {} # { PacketID: Expiration time }
        self.__availableIDs = Set(range(1,255))
        
        # Configure Socket
        # IPv4 UDP
        try:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.__socket.bind(('', self.DEFAULT_PORT))
            self.__socket.setblocking(0)
            self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            _, port = self.__socket.getsockname()
            
            self.logger.debug("ICP Socket Bound to port %i", port)
            
            self.refresh()
            
        except:
            self.logger.exception("UPEL ICP Socket Exception")
            
        self.e_conf.set()
        
        return True
    
    def close(self):
        self.stop()
        
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
                
                #===================================================================
                # Check for dead entries in the routing map
                #===================================================================
                self._serviceRoutingMap()
                
                # TODO: Do we need to sleep here or run full speed?
                
            except socket.error as e:
                if e.errno == errno.EACCES:
                    # Permission denied
                    self.logger.error('Unable to send: permission denied. Check firewall policy')
                    self.e_alive.clear()
                
            except:
                self.logger.exception("UPEL ICP Thread Exception")
    
    def getResources(self):
        return self.resources
    
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
        
        packet = icp.packets.DiscoveryPacket()
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
        packet = icp.packets.DiscoveryPacket()
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
        :type packet_obj: UPEL_ICP_Packet
        :param ttl: Time to Live (seconds)
        :type ttl: float
        :returns: packetID or none if unable to queue message
        """
        if len(self.__availableIDs) > 0:
            try:
                 
                # Assign a PacketID
                packetID = self.__availableIDs.pop()
                 
                packet_obj.setPacketID(packetID)
                     
                self.__messageQueue.put(packet_obj, False)
                self.__expiration[packetID] = time.time() + ttl
                
                return packetID
             
            except KeyError:
                # No IDs available
                raise Full
             
            except Full:
                # Failed to add to queue
                raise
             
        else:
            return None
        
    def _serviceSocket(self):
            read, _, _ = select.select([self.__socket],[],[], 0.1)
            
            if self.__socket in read:
                data, address = self.__socket.recvfrom(4096)
                sourceIP, sourcePort = address
            
                try:
                    resp_pkt = icp.packets.ICP_Packet(packet_data=data)
                    
                    # Debug output
                    packetID = resp_pkt.getPacketID()
                    packetType = resp_pkt.getPacketType()
                    self.logger.debug("ICP RX [ID:%i, TYPE:%X, SIZE:%i] from %s", 
                                      packetID, packetType, len(resp_pkt.getPayload()), 
                                      sourceIP)
                    
                    packetTypeClass = icp.packet_types.get(packetType)
                    pkt = packetTypeClass(packet_data=data,
                                          source=sourceIP)
                    
                    # Route Packets
                    if packetTypeClass == icp.packets.EnumerationPacket:
                        # TODO: New format for enumeration packets
                        # Filter Discovery Packets
                        enum = pkt.getSuuportedPacketTypes()
                        
                        self.logger.debug(str(enum))
                        
                        # Check if resource exists
                        # TODO: Resource creation depends on device type
                        if resID not in self.resources.keys():
                            # Create new device
                            self.resources[resID] = r_UPEL(resID, self,
                                                           logger=self.logger,
                                                           config=self.config,
                                                           enableRpc=self.manager.enableRpc)
                        
                            self.logger.info("Found UPEL ICP Device: %s" % res)
                    
                    elif packetID in self.__routingMap.keys():
                        destination = self.__routingMap.get(packetID, None)
                        
                        if destination in self.resources.keys():
                            dev = self.resources.get(destination)
                            
                            dev._processResponse(resp_pkt)
                            
                            # Remove entry from routing map
                            self.__routingMap.pop(packetID)
                            
                            # Remove entry from expiration table
                            self.__expiration.pop(packetID)
                            
                            # Add free ID back into pool
                            self.__availableIDs.add(packetID)
                            
                    else:
                        self.logger.error("ICP RX [ID:%i] EXPIRED/INVALID PACKET ID", packetID)
                        
                except icp.errors.ICP_Invalid_Packet:
                    self.logger.error("ICP Invalid Packet")
                
                #except:
                    # Pass on all errors for the time being
                    #pass
                
    def _serviceQueue(self):
        """
        :returns: bool - True if the queue was not empty, False otherwise
        """
        if not self.__messageQueue.empty() and len(self.__availableIDs) > 0:
            try:
                packet_obj = self.__messageQueue.get_nowait()
                
                if issubclass(packet_obj.__class__, icp.packets.ICP_Packet):
                    destination = packet_obj.getDestination()
                    
                    # Assign a packet ID
                    packetID = packet_obj.PACKET_ID
                    
                    # Pack for transmission
                    packet = packet_obj.pack()
                    
                    # Override broadcast address if necessary
                    if destination == "<broadcast>":
                        #=======================================================
                        # if self.config.broadcastIP:
                        #     try:
                        #         destination = self.config.broadcastIP
                        #     except:
                        #         pass
                        #=======================================================
                        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                            
                    else:
                        # Add entry to routing map
                        self.__routingMap[packetID] = destination
                        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
                    
                    # Transmit
                    self.__socket.sendto(packet, (destination, self.DEFAULT_PORT))
                    
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
        
    def _serviceRoutingMap(self):
        for packetID, ttl in self.__expiration.items():
            if time.time() > self.__expiration.get(packetID):
                # packet expired, notify ICP Device
                try:
                    destination = self.__routingMap.pop(packetID)
                    
                    if destination in self.resources.keys():
                        dev = self.resources.get(destination)
                    
                        dev._processTimeout(packetID)
                    
                except KeyError:
                    # Not in routing map
                    pass
                    
                finally:
                    # Remove entry from expiration table
                    self.__expiration.pop(packetID)
                    # Add free ID back into pool
                    self.__availableIDs.add(packetID)

    

    
class r_UPEL(Base_Resource):
    """
    Instrument class for ICP devices. Used by Models to communicate with ICP
    devices over the network. 
    """
    
    type = "UPEL"
    
    def __init__(self, resID, interface, **kwargs):
        Base_Resource.__init__(self, resID, interface, **kwargs)
        
        self.address = address
        self.queue = packetQueue
        
        self.acc_thread = None
        
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
        
        if isinstance(pkt, RegisterPacket):
            # Check if the register should be cached or accumulated
            try:
                address, subindex, data_type = self.reg_outgoing.pop(packetID)
                key = (address, subindex)
                
                if key in self.reg_cache.keys():
                    self.reg_cache[key] = pkt.get(data_type)
                    
                if key in self.accumulators.keys():
                    # TODO: add new value to accumulator
                    acc = self.accumulators.get(key)
                    acc.push(pkt.get(data_type))
                    
            except:
                pass
        
        self.incomingPackets[packetID] = pkt
        
    def _getResponse(self, packetID, block=False):
        """
        Get a response packet from the incoming packet queue. Non-blocking
        unless block is set to True.
        
        :param packetID: PacketID of desired packet
        :type packetID: int
        :param block: Block until packet is received or timeout occurs
        :type block: bool
        :returns: UPEL_ICP_Packet object or None if no response
        """
        if block:
            while (True):
                ret = self._getResponse(packetID)
                
                if ret is not None:
                    return ret
            
        else:
            try:
                pkt = self.incomingPackets.pop(packetID)
            
                if isinstance(pkt, ICP_Timeout):
                    raise pkt
                
                elif isinstance(pkt, ErrorPacket):
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
    

        
    #===========================================================================
    # Device State
    #===========================================================================
    
    def getState(self):
        """
        Query the ICP Device for the current state.
        
        :returns: int
        """
        packet = StateChangePacket(0)
        packet.setDestination(self.address)

        try:
            packetID = self.queue(packet, 10.0)
            
            pkt = self._getResponse(packetID, block=True)
            return pkt.getState()
            
        except ICP_Timeout:
            return None
        
    def setState(self, new_state):
        packet = StateChangePacket(new_state)
        packet.setDestination(self.address)
        
        try:
            packetID = self.queue(packet, 10.0)
            
            pkt = self._getResponse(packetID, block=True)
            return pkt.getState()
            
        except ICP_Timeout:
            return None
        
    #===========================================================================
    # Command Operations
    #===========================================================================
    
    def write(self, data):
        pass
    
    def read(self):
        pass
    
    def query(self, data):
        pass
    
    #===========================================================================
    # Register Operations
    #===========================================================================
    
    def register_write(self, address, subindex, data, data_type):
        """
        Write a value to a register. Blocking operation.
        
        :warning::
        
            Binary data cannot be encoded for network transmission from a Model.
            Models should use the appropriate writeReg function for the desired
            data type to avoid raising exceptions or corrupting data.
            
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        :param data: Data to write
        :type data: variable
        :param data_type: Data type
        :type data_type: str
        """
        try:
            packetID = self.register_write_queue(address, subindex, data, data_type)
        
            data = self._getResponse(packetID, block=True)
                    
            if data is not None:
                return data.get(data_type)
                
        except ICP_Timeout:
            return None
    
    def register_write_queue(self, address, subindex, data, data_type):
        """
        Queue a write operation to a register. Returns packet ID for the sent
        packet. If there are no packet IDs currently available, this call
        blocks until one is available. Otherwise, this call returns immediately.
        
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        :param data: Data to write
        :type data: variable
        :param data_type: Data type
        :type data_type: str
        :returns: packetID
        """
            
        packet = RegisterWritePacket(address, subindex, data, data_type)
        packet.setDestination(self.address)
        
        try:
            packetID = self.queue(packet, 10.0)
        
            self.reg_outgoing[packetID] = (address, subindex, data_type)
        
            return packetID
        
        except:
            raise
                
    def register_read_queue(self, address, subindex, data_type):
        """
        Queue a read operation to a register. Returns packet ID for the sent
        packet. If there are no packet IDs currently available, this call
        blocks until one is available. Otherwise, this call returns immediately.
        
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        :param data_type: Data type
        :type data_type: str
        :returns: packetID
        """
        packet = RegisterReadPacket(address, subindex)
        packet.setDestination(self.address)
        
        try:
            packetID = self.queue(packet, 10.0)
        
            self.reg_outgoing[packetID] = (address, subindex, data_type)
        
            return packetID
        
        except:
            raise
    
    def register_read(self, address, subindex, data_type):
        """
        Read a value from a register. Blocks until data returns. If cached data
        exists, it will be returned. A cache update can be forced by directly
        calling register_read_queue().
        
        :warning::
        
            Binary data cannot be encoded for network transmission from a Model.
            Models should use the appropriate readReg function for the desired
            data type to avoid raising exceptions. 
        
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        :param data_type: Data type
        :type data_type: str
        :returns: str
        """
        key = (address, subindex)
        
        if key in self.reg_cache.keys():
            # Cached & Accumulated registers should get values from the reg_cache
            return self.reg_cache.get(key, None)
            
        else:
            try:
                packetID = self.register_read_queue(address, subindex, data_type)
            
                data = self._getResponse(packetID, block=True)
                        
                if data is not None:
                    return data.get(data_type)
                    
            except ICP_Timeout:
                return None
