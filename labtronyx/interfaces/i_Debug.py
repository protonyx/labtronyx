from labtronyx.bases.interface import Base_Interface
from labtronyx.bases.resource import Base_Resource

import sys

import common.resource_status as resource_status

class i_Debug(Base_Interface):
    
    info = {
        # Interface Author
        'author':               'KKENNEDY',
        # Interface Version
        'version':              '1.0',
        # Revision date
        'date':                 '2015-03-06'
    }
    
    # Dict: ResID -> r_Debug Object
    resources = {}
    
    #===========================================================================
    # Required API Function Definitions
    #===========================================================================
    
    def open(self):
        if "-d" in sys.argv[1:]:
            return True
        
        else:
            return False
        
    def close(self):
        for resObj in self.resources.values():
            resObj.stop()
                    
        self.resources.clear()
        
        return True
    
    def run(self):
        self.refresh()
    
    def refresh(self):
        if "-d" in sys.argv[1:]:
            if 'DEBUG' not in self.resources:
                new_res = r_Debug('DEBUG', self,
                                  logger=self.logger,
                                  config=self.config,
                                  enableRpc=self.manager.enableRpc)
                self.resources['DEBUG'] = new_res
                
                self.manager._cb_new_resource()
        
    def getResources(self):
        return self.resources
            
class r_Debug(Base_Resource):
    type = "Debug"
    
    def open(self):
        self.setResourceStatus(resource_status.READY)
        
        return True
    
    def close(self):
        return True
    
    def write(self, data):
        self.checkResourceStatus()
        
        return True
    
    def triggerDisconnect(self):
        self.setResourceStatus(resource_status.ERROR_UNRESPONSIVE)
    
    def triggerError(self):
        self.setResourceStatus(resource_status.ERROR_DEVICE_ERROR)
        
    def triggerReady(self):
        self.setResourceStatus(resource_status.READY)
    
    def getProperties(self):
        prop = Base_Resource.getProperties(self)
        prop['deviceVendor'] = 'Labtronyx'
        prop['deviceModel'] = 'Debug'
        prop['deviceType'] = 'Debug'
        
        return prop