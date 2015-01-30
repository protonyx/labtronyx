import sys

import controllers

class c_Debug(controllers.c_Base):
    
    # Dict: ResID -> r_Debug Object
    resources = {}
    
    #===========================================================================
    # Required API Function Definitions
    #===========================================================================
    
    def open(self):
        if "-d" in sys.argv[1:]:
            new_res = r_Debug('DEBUG', self)
            self.resources['DEBUG'] = new_res
            
            self.manager._notify_new_resource()
            
        return True
        
    def close(self):
        return True
    
    def refresh(self):
        return True
        
    def getResources(self):
        return self.resources
            
class r_Debug(controllers.r_Base):
    type = "Debug"
    
    def open(self):
        return True
    
    def close(self):
        return True