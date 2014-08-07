import common

class c_Base(common.IC_Common):

    # TODO: Controllers will have hooks into the persistence config to "remember" how
    #       a particular device is configured when the program is run in the future.
    
    resources = {}

    def getControllerName(self):
        return self.__class__.__name__
        
    def _open(self):
        self.__ready = False
        
        try:
            ret = self.open()
            if type(ret) == bool:
                if ret == True:
                    self.__ready = True
                else:
                    self.__ready = False
                return ret
            
            else:
                self.logger.error("Controller function open() must return a bool type")
                return False
            
        except NotImplementedError:
            self.logger.error("Controller function open() is not implemented")
    
    def _ready(self):
        """
        If an interface error occurred, clear the ready flag to alert the calling class
        """
        return self.__ready
    
    def _scan(self):
        if self.__ready:  
            try:
                ret = self.scan()
                
                if type(ret) == bool:
                    return True
                
                else:
                    self.logger.error("Controller function scan() must return a bool type")
                    return False
                
            except NotImplementedError:
                # Controllers do not have to implement scan
                return True
                
        else:
            self.logger.error("Controller not ready")
    
    def _close(self):
        try:
            return self.close()
        except NotImplementedError:
            self.logger.error("Controller function close() is not implemented")
    
    # Inheriting classes must implement these functions:
    def open(self):
        """
        Controller Initialization
        
        Make any system driver calls necessary to initialize communication. If
        any kind of exception occurs that will inhibit communication, this
        function should return False to indicate an error to the 
        InstrumentManager.
        
        Any exceptions raised will be caught by the InstrumentManager, and it
        will be assumed that the controller failed to initialize. A subsequent
        call to :func:`close` will be made in this case.
        
        :returns: bool - True if ready, False if error occurred
        """
        raise NotImplementedError
    
    def close(self):
        """
        Controller clean-up
        
        Make any system driver calls necessary to clean-up controller
        operations. This function should explicitly free any system resources
        to prevent locking errors.
        
        Any exceptions raised will be caught by the InstrumentManager.
        """
        raise NotImplementedError

    def getResources(self):
        """
        Get a listing of resources by ID. There is no requirement for how
        resources are stored internal to the controller, but this function
        should return a dict with the format::
        
            { resourceID: (VID, PID) }
        
        :returns: dict
        """
        raise NotImplementedError
    
    def canEditResources(self):
        """
        Query the controller to find out if that controller supports manually
        adding and destroying resources. 
        """
        raise NotImplementedError
    
    #===========================================================================
    # Automatic Controllers
    #===========================================================================
    
    def refresh(self):
        """
        Refreshes the resource list. If resources are no longer available,
        they should be removed.
        """
        raise NotImplementedError
    
    #===========================================================================
    # Manual Controllers
    #===========================================================================
    
    def addResource(self, ResID, VID, PID):
        """
        Manually add a resource to the controller
        
        :param ResID: Resource Identifier
        :type ResID: str
        :param VID: Vendor Identifier
        :type VID: str
        :param PID: Product Identifier
        :type PID: str
        :returns: bool - True if successful, False otherwise
        """
        raise NotImplementedError
    
    def destroyResource(self, ResID):
        """
        Remove a manually added resource
        
        :param ResID: Resource Identifier
        :type ResID: str
        :returns: bool - True if successful, False otherwise
        """
        raise NotImplementedError
