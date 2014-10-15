import struct
import socket
import select
import time
import threading
import Queue
from sets import Set

from packets import *
from device import *
from errors import *

"""
Conforms to Rev 1.0 of the UPEL Instrument Control Protocol

Author: Kevin Kennedy
"""
class UPEL_ICP(threading.Thread):
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
    any data in the __socket buffer, and checking the status of entries in the 
    routing map. If none of those tasks requires attention, the thread will 
    sleep for a small time interval to limit loading the processor excessively.
    """
    
    devices = {}
    resources = {}
    
    DEFAULT_PORT = 7968
    
    def __init__(self, **kwargs):
        threading.Thread.__init__(self)
        self.name = "UPEL_ICP"
        
        self.port = kwargs.get('port', self.DEFAULT_PORT)
            
        # Setup Logger
        if 'logger' in kwargs:
            self.logger = kwargs.get('logger')
        
        else:
            self.logger = logging.getLogger(__name__)
            
        self.alive = threading.Event()
    
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
            self.__socket.bind(('', self.port))
            self.__socket.setblocking(0)
            self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            self.logger.debug("ICP Socket Bound to port %i", self.port)
            
        except:
            pass
        
        self.alive.set()
        
        while (self.alive.is_set()):
            try:
                #===================================================================
                # Service the __socket
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
                self.logger.exception("UPEL ICP Thread Exception")
                #continue
            
    def stop(self):
        self.__socket.shutdown(1)
        self.__socket.close()
        
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
    
    def getResources(self):
        return self.resources
        
    def queuePacket(self, packet_obj, ttl):
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
            read, _, _ = select.select([self.__socket],[],[], 0.1)
            
            if self.__socket in read:
                data, address = self.__socket.recvfrom(4096)
            
                try:
                    resp_pkt = UPEL_ICP_Packet(data)
                    packetID = resp_pkt.PACKET_ID
                    packetType = resp_pkt.PACKET_TYPE
                    
                    sourceIP, _ = address
                    resp_pkt.setSource(sourceIP)
                    
                    self.logger.debug("ICP RX [ID:%i, TYPE:%X] from %s", packetID, packetType, sourceIP)
                    
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





