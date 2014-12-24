import models

import math
import time

class m_test(models.m_Base):
    
    deviceType = 'Debug'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_Dummy']
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validVIDs = ['']
    validPIDs = ['']
    
    def _onLoad(self):
        pass
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        ret = models.m_Base.getProperties(self)
        
        ret['deviceVendor'] = ''
        ret['deviceModel'] = 'Debug Model'
            
        return ret
    