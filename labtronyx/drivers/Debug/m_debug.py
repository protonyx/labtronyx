from Base_Driver import Base_Driver

import math
import time

class m_debug(Base_Driver):
    
    info = {
        # Device Manufacturer
        'deviceVendor':         'Debug',
        # List of compatible device models
        'deviceModel':          ['Debug'],
        # Device type    
        'deviceType':           'Debug',      
        
        # List of compatible resource types
        'validResourceTypes':   ['Debug']            
    }
    
    def _onLoad(self):
        self.instr = self.getResource()
    
    def _onUnload(self):
        pass
    
    def test(self):
        return 1.0
    
    def __getattr__(self, name):
        return self.test
    
    def getProperties(self):
        ret = Base_Driver.getProperties(self)
        
        ret['deviceModel'] = 'Debug Model'
        ret['deviceSerial'] = '12345'
        
        return ret
    