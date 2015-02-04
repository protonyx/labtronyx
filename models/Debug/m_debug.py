import models

import math
import time

class m_debug(models.m_Base):
    
    info = {
        # Model revision author
        'author':               'KKENNEDY',
        # Model version
        'version':              '1.0',
        # Revision date of Model version
        'date':                 '2015-01-31',
        # Device Manufacturer
        'deviceVendor':         '',
        # List of compatible device models
        'deviceModel':          [''],
        # Device type    
        'deviceType':           'Debug',      
        
        # List of compatible resource types
        'validResourceTypes':   ['c_Debug']            
    }
    
    def _onLoad(self):
        self.instr = self.getResource()
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        ret = models.m_Base.getProperties(self)
        
        ret['deviceModel'] = 'Debug Model'
        ret['deviceSerial'] = ''
            
        return ret
    