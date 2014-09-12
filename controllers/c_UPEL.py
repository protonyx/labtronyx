import controllers
import common.upel_icp as icp

import socket
import select
import time

import binascii

class c_UPEL(controllers.c_Base):
    
    DEFAULT_PORT = 7968
    
    resources = []
    
    

    def open(self):
        try:
            import config
            self.config = config.Config()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(('',0))
            s.setblocking(0)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket = s
            
            return True
    
        except:
            return False
    
    def close(self):
        pass
    
    def getResources(self):
        pass
    
    def canEditResources(self):
        return True
    
    #===========================================================================
    # Optional - Automatic Controllers
    #===========================================================================
    
    def refresh(self):
        """
        Send a UDP broadcast packet on port 7968 and see who responds
        """
        
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        packet = icp.DiscoveryPacket().pack()
        
        #local_ip = str(socket.gethostbyname(socket.getfqdn()))
        
        if self.config.broadcastIP:
            broadcast_ip = self.config.broadcastIP
        else:
            broadcast_ip = '<broadcast>'
        
        # Send Discovery Packet
        self.socket.sendto(packet, (broadcast_ip, self.DEFAULT_PORT))
        
        #s.sendto(packet, ('192.168.1.130', self.DEFAULT_PORT))
        #s.sendto(packet, ('192.168.1.137', self.DEFAULT_PORT))
        t_start = time.time()
        
        while (time.time() - t_start) < 1.0:
            #data = repr(time.time()) + '\n'
            read, _, _ = select.select([self.socket],[],[], 1.0)
            
            if self.socket in read:
                data, address = self.socket.recvfrom(4096)

                try:
                    resp_pkt = icp.UPEL_ICP_Packet(data)
                    print str(resp_pkt.payload)
                    #print binascii.hexlify(data)
                    
                except icp.ICP_Invalid_Packet:
                    pass
    
    #===========================================================================
    # Optional - Manual Controllers
    #===========================================================================
    
    def addResource(self, ResID, VID, PID):
        pass
    
    def destroyResource(self):
        pass