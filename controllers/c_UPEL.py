import controllers
import common.upel_icp as icp

import socket
import time

import binascii

class c_UPEL(controllers.c_Base):
    
    DEFAULT_PORT = 7968
    
    resources = []
    
    

    def open(self):
        try:
            import config
            self.config = config.Config()
            
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
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('',0))
        #s.bind(('', self.DEFAULT_PORT))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        #s.connect(('<broadcast>', self.DEFAULT_PORT))
        
        packet = icp.DiscoveryPacket().pack()
        
        #local_ip = str(socket.gethostbyname(socket.getfqdn()))
        
        if self.config.broadcastIP:
            broadcast_ip = self.config.broadcastIP
        else:
            broadcast_ip = '<broadcast>'
        
        #s.sendto(packet, ('192.168.1.130', self.DEFAULT_PORT))
        #s.sendto(packet, ('192.168.1.137', self.DEFAULT_PORT))
        while 1:
            #data = repr(time.time()) + '\n'
            data = packet
            s.sendto(data, (broadcast_ip, self.DEFAULT_PORT))
            time.sleep(2)
            
        print binascii.hexlify(packet)
    
    #===========================================================================
    # Optional - Manual Controllers
    #===========================================================================
    
    def addResource(self, ResID, VID, PID):
        pass
    
    def destroyResource(self):
        pass