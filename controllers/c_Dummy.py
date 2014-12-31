import controllers

class c_Dummy(controllers.c_Base):
    
    # Dict: ResID -> (VID, PID)
    resources = {}
    
    # Dict: ResID -> ResourceObject
    resourceObjects = {}
    
    #===========================================================================
    # Required API Function Definitions
    #===========================================================================
    
    def open(self):
        self.resources['DEBUG'] = ('', '')
        return True
        
    def close(self):
        return True
    
    def refresh(self):
        return True
        
    def getResources(self):
        return self.resources
            
    def openResourceObject(self, resID, **kwargs):
        resource = self.resourceObjects.get(resID, None)
        if resource is not None:
            return resource
        else:
            resource = controllers.c_ResourceObjectBase()
            self.resourceObjects[resID] = resource
            return resource
        
    def closeResourceObject(self, resID):
        resource = self.resourceObjects.get(resID, None)
        
        if resource is not None:
            resource.close()
            del self.resourceObjects[resID]