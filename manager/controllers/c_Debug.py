import sys

import controllers

class c_Debug(controllers.c_Base):
    
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
        return True
    
    def refresh(self):
        if "-d" in sys.argv[1:]:
            if 'DEBUG' not in self.resources:
                new_res = r_Debug('DEBUG', self)
                self.resources['DEBUG'] = new_res
                
                self.manager._cb_new_resource()
        
    def getResources(self):
        return self.resources
            
class r_Debug(controllers.r_Base):
    type = "Debug"
    
    def open(self):
        return True
    
    def close(self):
        return True