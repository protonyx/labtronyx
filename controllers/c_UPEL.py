import time

import controllers
from common.icp import UPEL_ICP

class c_UPEL(controllers.c_Base):
    
    # Dict: ResID -> (VID, PID)
    resources = {}
    
    # Dict: ResID -> UPEL_ICP_Device Object
    resourceObjects = {}

    def open(self):
        
        # Start the arbiter thread
        self.icp_manager = UPEL_ICP(logger=self.logger)
        self.icp_manager.start()
        
        return True
    
    def close(self):
        self.icp_manager.stop()
    
    def getResources(self):
        return self.resources
    
    def canEditResources(self):
        return True
    
    def openResourceObject(self, resID):
        resource = self.resourceObjects.get(resID, None)
        if resource is not None:
            return resource
        else:
            resource = self.icp_manager.getDevice(resID)
            self.resourceObjects[resID] = resource
            return resource
        
    def closeResourceObject(self, resID):
        resource = self.resourceObjects.get(resID, None)
        
        if resource is not None:
            resource.close()
            del self.resourceObjects[resID]
    
    #===========================================================================
    # Optional - Automatic Controllers
    #===========================================================================
    
    def refresh(self):
        self.icp_manager.discover(self.config.broadcastIP)
        
        # Give the arbiter time to process responses
        time.sleep(2.0)
        
        self.resources = self.icp_manager.getResources()

    #===========================================================================
    # def _getInstrument(self, resID):
    #     return self.icp_manager.getDevice(resID)
    #     
    # def _getDevice(self, resID):
    #     return self.icp_manager.getDevice(resID)
    #===========================================================================
    
    #===========================================================================
    # Optional - Manual Controllers
    #===========================================================================
    
    def addResource(self, ResID, VID=None, PID=None):
        """
        Treats an addResource request as a hint that a device exists. Attempts
        to send a discovery packet to the device to get more information.
        
        The ICP thread will automatically handle the creation of an
        instrument for the new resource.
        
        :param ResID: Resource ID (IP Address)
        :type ResID: str
        :returns: bool. True if successful, False otherwise
        """
        self.icp_manager.discover(ResID)
    
    def destroyResource(self):
        pass
    
                
        