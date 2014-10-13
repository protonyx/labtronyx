import controllers
import common.upel_icp as icp

import socket
import select
import time
import threading
import Queue
from sets import Set

class c_UPEL(controllers.c_Base):
    
    # Dict: ResID -> (VID, PID)
    resources = {}
    # Dict: ResID -> UPEL_ICP_Device Object
    devices = {}

    def open(self):
        
        # Start the arbiter thread
        self.arbiter = c_UPEL_arbiter(self)
        self.arbiter.start()
        self.arbiter.alive.wait(5.0)
        
        return self.arbiter.alive.is_set()
    
    def close(self):
        self.arbiter.stop()
    
    def getResources(self):
        return self.resources
    
    def canEditResources(self):
        return True
    
    #===========================================================================
    # Optional - Automatic Controllers
    #===========================================================================
    
    def refresh(self):
        """
        Queues a broadcast discovery packet. The arbiter will automatically
        update the resource table as responses come in. 
        
        :returns: None
        """
        packet = icp.DiscoveryPacket()
        packet.setDestination('<broadcast>')

        # Queue Discovery Packet
        self.arbiter.queueMessage(packet, 10.0)
        
        # Give the arbiter time to process responses
        time.sleep(2.0)
        
        #self.socket.sendto(packet, (broadcast_ip, self.DEFAULT_PORT))
        
        #s.sendto(packet, ('192.168.1.130', self.DEFAULT_PORT))
        #s.sendto(packet, ('192.168.1.137', self.DEFAULT_PORT))
        #t_start = time.time()
        
#===============================================================================
#         while (time.time() - t_start) < 2.0:
#             #data = repr(time.time()) + '\n'
#             read, _, _ = select.select([self.socket],[],[], 2.0)
#             
#             if self.socket in read:
#                 data, address = self.socket.recvfrom(4096)
# 
#                 try:
#                     resp_pkt = icp.UPEL_ICP_Packet(data)
#                     
#                     if resp_pkt.PACKET_TYPE == 0xF:
#                         # Filter Discovery Packets
#                         ident = resp_pkt.PAYLOAD.split(',')
#                         
#                         res = (ident[0], ident[1])
#                         self.resources[address[0]] = res
#                         
#                         self.logger.info("Found UPEL ICP Device: %s %s" % res)
#                     
#                     
#                 except icp.ICP_Invalid_Packet:
#                     pass
#===============================================================================

    def _getInstrument(self, resID):
        return self._getDevice(resID)
        
    def _getDevice(self, resID):
        return self.devices.get(resID, None)
    
    #===========================================================================
    # Optional - Manual Controllers
    #===========================================================================
    
    def addResource(self, ResID, VID=None, PID=None):
        """
        Treats an addResource request as a hint that a device exists. Attempts
        to send a discovery packet to the device to get more information.
        
        The arbiter thread will automatically handle the creation of an
        instrument for the new resource.
        
        :param ResID: Resource ID (IP Address)
        :type ResID: str
        :returns: bool. True if successful, False otherwise
        """
        packet = icp.DiscoveryPacket()
        packet.setDestination(ResID)

        # Queue Discovery Packet
        self.arbiter.queueMessage(packet, 60.0)
        
        # Wait for the packet to come back
        time.sleep(1.0)
    
    def destroyResource(self):
        pass
    
class c_UPEL_arbiter(threading.Thread):
    """
    The UPEL Arbiter thread manages communication in and out of the network socket
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
    
    The routing map has the format: { PacketID: (TTL, ResponseQueue) }
    
    Execution Strategy
    ==================
    
    The arbiter will alternate between servicing the message queue, processing 
    any data in the socket buffer, and checking the status of entries in the 
    routing map. If none of those tasks requires attention, the thread will 
    sleep for a small time interval to limit loading the processor excessively.
    """
    
    DEFAULT_PORT = 7968
    alive = threading.Event()
    
    def __init__(self, controller):
        threading.Thread.__init__(self)
        self.controller = controller
        self.name = "c_UPEL_Arbiter"
    
    def run(self):
        # Init
        self.__messageQueue = Queue.Queue()
        self.__routingMap = {} # { PacketID: ResID }
        self.__expiration = {} # { PacketID: Expiration time }
        self.__availableIDs = Set(range(1,255))
        # Import config
        try:
            import config
            self.config = config.Config()
            self.port = self.config.UPELPort
        except:
            self.port = self.DEFAULT_PORT
        
        # Configure Socket
        # IPv4 UDP
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('', self.port))
            self.socket.setblocking(0)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
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
                
                # Sleep?
                
            except:
                continue
            
    def stop(self):
        self.socket.shutdown(1)
        self.socket.close()
        
        self.alive.clear()
        
    def queueMessage(self, packet_obj, ttl):
        """
        Insert a message into the queue
        
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
                return None
            
            except Full:
                # Failed to add to queue
                return None
            
        else:
            return None
        
    def _serviceSocket(self):
            read, _, _ = select.select([self.socket],[],[], 0.1)
            
            if self.socket in read:
                data, address = self.socket.recvfrom(4096)
            
                try:
                    resp_pkt = icp.UPEL_ICP_Packet(data)
                    packetID = resp_pkt.PACKET_ID
                    packetType = resp_pkt.PACKET_TYPE
                    
                    sourceIP, _ = address
                    resp_pkt.setSource(sourceIP)
                    
                    self.controller.logger.debug("ICP RX [ID:%i, TYPE:%X] from %s", packetID, packetType, sourceIP)
                    
                    # Route Packets
                    if packetType == 0xF and resp_pkt.isResponse():
                        # Filter Discovery Packets
                        ident = resp_pkt.getPayload().split(',')
                        
                        # Check if resource exists
                        resID = address[0]
                        res = (ident[0], ident[1])
                        
                        if resID not in self.controller.resources.keys():
                            # Create new device
                            self.controller.resources[resID] = res
                            self.controller.devices[resID] = icp.UPEL_ICP_Device(resID, self)
                        
                            self.controller.logger.info("Found UPEL ICP Device: %s %s" % res)
                    
                    elif packetID in self.__routingMap.keys():
                        destination = self.__routingMap.get(packetID, None)
                        
                        if destination in self.controller.devices.keys():
                            dev = self.controller.devices.get(destination)
                            
                            dev._processResponse(resp_pkt)
                            
                            # Remove entry from routing map
                            self.__routingMap.pop(packetID)
                            
                            # Remove entry from expiration table
                            self.__expiration.pop(packetID)
                            
                            # Add free ID back into pool
                            self.__availableIDs.add(packetID)
                            
                    else:
                        self.controller.logger.error("ICP RX [ID:%i] EXPIRED/INVALID PACKET ID", packetID)
                        
                except icp.ICP_Invalid_Packet:
                    pass
                
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
                
                if issubclass(packet_obj.__class__, icp.UPEL_ICP_Packet):
                    destination = packet_obj.getDestination()
                    packetID = packet_obj.PACKET_ID
                    
                    # Pack for transmission
                    packet = packet_obj.pack()
                    
                    # Override broadcast address if necessary
                    if destination == "<broadcast>":
                        if self.config.broadcastIP:
                            try:
                                destination = self.config.broadcastIP
                            except:
                                pass
                        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                            
                    else:
                        # Add entry to routing map
                        self.__routingMap[packetID] = destination
                        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
                    
                    # Transmit
                    self.socket.sendto(packet, (destination, self.port))
                    
                    self.controller.logger.debug("ICP TX [ID:%i] to %s", packetID, destination)
                    
                else:
                    return True
            
            except Queue.Empty:
                return False
            
            except:
                self.controller.logger.exception("Exception encountered while servicing queue")
                return True
            
        else:
            return False
        
    def _serviceRoutingMap(self):
        for packetID, ttl in self.__expiration.items():
            if time.time() > self.__expiration.get(packetID):
                # packet expired, notify ICP Device
                destination = self.__routingMap.get(packetID, None)
                        
                if destination in self.controller.devices.keys():
                    dev = self.controller.devices.get(destination)
                    
                    dev._processTimeout(packetID)
                    
                # Remove entry from routing map
                self.__routingMap.pop(packetID)
                
                # Remove entry from expiration table
                self.__expiration.pop(packetID)
                
                # Add free ID back into pool
                self.__availableIDs.add(packetID)
                
        