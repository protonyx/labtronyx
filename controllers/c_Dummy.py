import controllers

class c_Dummy(controllers.c_Base):
    # Dict: ResID -> (VID, PID)
    resources = {}
    
    #===========================================================================
    # Required API Function Definitions
    #===========================================================================
    
    def open(self):
        self.resources['DEBUG'] = ('', '')
        return True
        
    def close(self):
        return True
    
    def refresh(self):
        """
        Refresh the VISA Resource list
        """
        return True
        
    def getResources(self):
        return self.resources
            