import threading
import struct
#from . import Base_Serial

from . import *

#print dir()

class m_BDPC_BR32(Base_Serial.Base_Serial):
    """
    
    """
    
    def _onLoad(self):
        Base_Serial.Base_Serial._onLoad(self)
        
        # Set the controller into passthrough mode
        self.instr.write("mode 2\n")
        
    def _onUnload(self):
        # Set the controller into debug mode
        magic = struct.pack('BB', 0x24, 0x1E)
        self.instr.write(magic)
        
        Base_Serial.Base_Serial._onUnload(self)
    
    def getProperties(self):
        prop = Base_Serial.Base_Serial.getProperties(self)
        
        prop['deviceVendor'] = 'UPEL'
        prop['deviceModel'] = 'BDPC 32kW'
        
        return prop
    
