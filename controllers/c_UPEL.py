import controllers
import common.upel_icp as icp

import socket
import select
import time
import threading
import Queue
from sets import Set

class c_UPEL(controllers.c_Base):
    
    resources = {}
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

        # Queue Discovery Packet
        self.arbiter.queueMessage('<broadcast>', 60.0, None, packet)
        
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
    
    #===========================================================================
    # Optional - Manual Controllers
    #===========================================================================
    
    def addResource(self, ResID, VID, PID):
        pass
    
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
        self.__routingMap = {}
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
            
            # Sleep?
            
    def stop(self):
        self.socket.shutdown(1)
        self.socket.close()
        
        self.alive.clear()
        
    def queueMessage(self, destination, ttl, response_queue, packet_obj):
        """
        Insert a message into the queue
        
        :param destination: Destination IP Address
        :type destination: str
        :param ttl: Time to Live (seconds)
        :type ttl: int
        :param response_queue: Queue to drop response into
        :type response_queue: Queue
        :param packet_obj: ICP Packet Object
        :type packet_obj: UPEL_ICP_Packet
        :returns: bool - True if messaged was queued successfully, False otherwise
        """
        try:
            self.__messageQueue.put((destination, ttl, response_queue, packet_obj), False)
            return True
        
        except Full:
            return False
        
    def _getPacketID(self):
        """
        Get the next available packet ID
        
        :returns: int or None if there are no available IDs
        """
        try:
            s = self.__availableIDs.pop()
            return s
        
        except KeyError:
            return None
        
    def _packetID_available(self):
        return len(self.__availableIDs) > 0
        
    def _serviceSocket(self):
            read, _, _ = select.select([self.socket],[],[], 0.5)
            
            if self.socket in read:
                data, address = self.socket.recvfrom(4096)
            
                try:
                    resp_pkt = icp.UPEL_ICP_Packet(data)
                    
                    if resp_pkt.PACKET_TYPE == 0xF:
                        # Filter Discovery Packets
                        ident = resp_pkt.PAYLOAD.split(',')
                        
                        res = (ident[0], ident[1])
                        self.resources[address[0]] = res
                        
                        self.logger.info("Found UPEL ICP Device: %s %s" % res)
                    
                    elif resp_pkt.PACKET_ID in self.__routingMap.keys():
                        destination, _, response_queue = self.__routingMap[resp_pkt.PACKET_ID]
                        
                        
                        
                except icp.ICP_Invalid_Packet:
                    pass
                
    def _serviceQueue(self):
        """
        :returns: bool - True if the queue was not empty, False otherwise
        """
        if not self.__messageQueue.empty() and self._packetID_available():
            try:
                msg = self.__messageQueue.get_nowait()
                destination, ttl, response_queue, packet_obj = msg
                
                # Assign a PacketID
                packetID = self._getPacketID()
                
                if issubclass(packet_obj.__class__, icp.UPEL_ICP_Packet) and packetID is not None:
                    # Assign the PacketID
                    packet_obj.PACKET_ID = packetID
                    
                    # Pack for transmission
                    packet = packet_obj.pack()
                    
                    # Override broadcast address if necessary
                    if destination is '<broadcast>':
                        if self.config.broadcastIP:
                            try:
                                destination = self.config.broadcastIP
                            except:
                                pass
                        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                            
                    else:
                        # Add entry to routing map
                        self.__routingMap[packetID] = (destination, ttl, response_queue)
                        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
                    
                    # Transmit
                    self.socket.sendto(packet, (destination, self.port))
                    
                else:
                    return True
            
            except Queue.Empty:
                return False
            
        else:
            return False