import threading
import struct
import time
#from . import Base_Serial

from . import *

#print dir()

class m_BDPC_BR32(Base_Serial.Base_Serial):
    """
    
    """
    
    info = {
        # Model revision author
        'author':               'KKENNEDY',
        # Model version
        'version':              '1.0',
        # Revision date of Model version
        'date':                 '2015-01-31',
        # Device Manufacturer
        'deviceVendor':         'UPEL',
        # List of compatible device models
        'deviceModel':          ['BDPC 32kW'],
        # Device type    
        'deviceType':           'DC-DC Converter',      
        
        # List of compatible resource types
        'validResourceTypes':   ['Serial']
    }
    
    def _onLoad(self):
        Base_Serial.Base_Serial._onLoad(self)
        
        # Set the controller into passthrough mode
        #self.instr.write("mode 2\n")
        
    def _onUnload(self):
        # Set the controller into debug mode
        #magic = struct.pack('BB', 0x24, 0x1E)
        #self.instr.write(magic)
        
        Base_Serial.Base_Serial._onUnload(self)
        
    def _SRC_comm_reset(self):
        self.logger.warning("Reset SRC Communication Link")
        magic = struct.pack('BB', 0x24, 0x1E)
        self.instr.write(magic)
        time.sleep(0.1)
        self.instr.write("mode 2\n")
    
    def getProperties(self):
        prop = Base_Serial.Base_Serial.getProperties(self)
        
        prop['deviceVendor'] = 'UPEL'
        prop['deviceModel'] = 'BDPC 32kW'
        
        return prop
    
