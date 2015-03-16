from Base_Interface import Base_Interface
from Base_Resource import Base_Resource

import struct
import time
import socket
import select
import threading
import Queue
from sets import Set

import numpy

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
    The UPEL ICP thread manages communication in and out of the network socket
    on port 7968.
    
    Structure
    =========
    
    Message Queue
    -------------
    
    Packets to send out to remote devices are queued in the message queue and sent
    one at a time. Queuing a message requires:
    
      * IP Address
      * TTL (Time to Live)
      * Response Queue
      * ICP Packet Object
    
    The response packet object will be loaded into the response queue.
    
    Routing Map
    -----------
    
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
    ==================
    
    The arbiter will alternate between servicing the message queue, processing 
    any data in the __socket buffer, and checking the status of entries in the 
    routing map. If none of those tasks requires attention, the thread will 
    sleep for a small time interval to limit loading the processor excessively.
    
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
    
    # Dict: ResID -> (VID, PID)
    resources = {}
    
    # Dict: ResID -> UPEL_ICP_Device Object
    resourceObjects = {}
    
    # UPEL Controller Config
    broadcastIP = '192.168.1.255'
    DEFAULT_PORT = 7968

    def open(self):
        self.alive = threading.Event()
        
        return True
    
    def close(self):
        self.alive.clear()
        
    def run(self):
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
            
            self.logger.debug("ICP Socket Bound to port %i", self.port)
            
        except:
            pass
        
        self.alive.set()
        
        while (self.alive.is_set()):
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
                
            except:
                self.logger.exception("UPEL ICP Thread Exception")
                
        self.__socket.shutdown(1)
        self.__socket.close()
    
    def getResources(self):
        return self.resources
    
    def openResourceObject(self, resID):
        resource = self.resourceObjects.get(resID, None)
        if resource is not None:
            return resource
        else:
            resource = self.icp_manager.getDevice(resID)
            self.resourceObjects[resID] = resource
            return resource
        
    def closeResourceObject(self, resID):
        resource = self.resourceObjects.get(resID, None)
        
        if resource is not None:
            resource.close()
            del self.resourceObjects[resID]
    
    #===========================================================================
    # Resource Management
    #===========================================================================
    
    def refresh(self):
        self.icp_manager.discover(self.config.broadcastIP)
        
    def addResource(self, ResID):
        """
        Treats an addResource request as a hint that a device exists. Attempts
        to send a discovery packet to the device to get more information.
        
        The ICP thread will automatically handle the creation of an
        instrument for the new resource.
        
        :param ResID: Resource ID (IP Address)
        :type ResID: str
        :returns: bool. True if successful, False otherwise
        """
        self.icp_manager.discover(ResID)
        
    def discover(self, address='<broadcast>'):
        """
        Queues a broadcast discovery packet. The arbiter will automatically
        update the resource table as responses come in. 
        
        :returns: None
        """
        packet = DiscoveryPacket()
        packet.setDestination(address)

        # Queue Discovery Packet
        self.__messageQueue.put(packet)
        
    def getDevice(self, address):
        return self.devices.get(address, None)

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
        :type ttl: int
        :returns: packetID or none if unable to queue message
        """
        if len(self.__availableIDs) > 0:
            try:
                 
                # Assign a PacketID
                packetID = self.__availableIDs.pop()
                 
                packet_obj.PACKET_ID = packetID
                     
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
            
                try:
                    resp_pkt = UPEL_ICP_Packet(data)
                    packetID = resp_pkt.PACKET_ID
                    packetType = resp_pkt.PACKET_TYPE
                    
                    sourceIP, _ = address
                    resp_pkt.setSource(sourceIP)
                    
                    self.logger.debug("ICP RX [ID:%i, TYPE:%X, SIZE:%i] from %s", packetID, packetType, len(resp_pkt.getPayload()), sourceIP)
                    
                    # Route Packets
                    if packetType == 0xF and resp_pkt.isResponse():
                        # Filter Discovery Packets
                        ident = resp_pkt.getPayload().split(',')
                        
                        # Check if resource exists
                        resID = address[0]
                        res = (ident[0], ident[1])
                        
                        if resID not in self.devices.keys():
                            # Create new device
                            self.devices[resID] = UPEL_ICP_Device(resID, self.queuePacket)
                            self.resources[resID] = res
                        
                            self.logger.info("Found UPEL ICP Device: %s %s" % res)
                    
                    elif packetID in self.__routingMap.keys():
                        destination = self.__routingMap.get(packetID, None)
                        
                        if destination in self.devices.keys():
                            dev = self.devices.get(destination)
                            
                            dev._processResponse(resp_pkt)
                            
                            # Remove entry from routing map
                            self.__routingMap.pop(packetID)
                            
                            # Remove entry from expiration table
                            self.__expiration.pop(packetID)
                            
                            # Add free ID back into pool
                            self.__availableIDs.add(packetID)
                            
                    else:
                        self.logger.error("ICP RX [ID:%i] EXPIRED/INVALID PACKET ID", packetID)
                        
                except ICP_Invalid_Packet:
                    pass
                
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
                
                if issubclass(packet_obj.__class__, UPEL_ICP_Packet):
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
                    self.__socket.sendto(packet, (destination, self.port))
                    
                    self.logger.debug("ICP TX [ID:%i] to %s", packetID, destination)
                    
                else:
                    return True
                
            except KeyError:
                # No IDs available
                return True
            
            except Queue.Empty:
                return False
            
            except:
                self.logger.exception("Exception encountered while servicing queue")
                return True
            
        else:
            return False
        
    def _serviceRoutingMap(self):
        for packetID, ttl in self.__expiration.items():
            if time.time() > self.__expiration.get(packetID):
                # packet expired, notify ICP Device
                try:
                    destination = self.__routingMap.pop(packetID)
                    
                    if destination in self.devices.keys():
                        dev = self.devices.get(destination)
                    
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

        
class r_UPEL_Serial(Base_Resource):
    pass

class r_UPEL_CAN(Base_Resource):
    pass