import common

class c_Base(common.IC_Common):
    """
    Controller Base Class
    
    Defines the controller API
    
    Wraps controller functions and performs some error checking to validate 
    return values. Also includes some helper functions that can be used or
    overridden depending on the needs of the controller.
    
    Each controller must maintain a dictionary of resource names that map to
    system resources known internally to the controller. Available resources
    should have the dictionary value set to None, whereas used resources should
    contain a reference to the model object instantiated when the model is
    created. 
    
    If a function returns an object that is not serializable, the function name
    must be prefixed with '_' in order to deny access to RPC clients who try to
    call that function. RPC servers can only serialize the following types:
    - str & unicode
    - int, long & float
    - bool
    - None
    - list & tuple
    - dict
    
    Types of Controllers
    ====================
    * Automatic
      These controllers can find resources on their own without any additional
      knowledge. This is typically achieved with a system driver that is
      "plug-'n-play" capable and enumerates devices on insertion.
      
    * Manual
      These controllers must have additional knowledge to discover a resource.
      An example of a manual controller is a TCP/IP device. Not all devices will
      respond to a multi-cast packet, so the user must supply an IP address to
      find the device.
      
    * Hybrid
      Hybrid controllers can discover resources, but without additional
      information, they will not be able to match a model driver to the
      resource. A serial port controller is an example of this, as the system
      maintains a list of available COM ports, but the user must supply the
      baud rate, stop bits and parity information for the controller to be able
      to establish communication. 
    
    TODO:
    Controllers will have hooks into the persistence config to "remember" how
    a particular device is configured when the program is run in the future.
    
    Controllers are responsible for managing available resources accessible by
    the system. That could be a serial port, USB device, VISA instrument, etc.
    Resources can be managed by the controller in whatever way is best, but a
    request to getResources should return a serializable dictionary with these
    keys:
        - 'id': How the resource will be identified when a load call is made
        - 'uuid': A UUID string for reference only
        - 'controller': The module name for the controller
        - 'driver': The module name for the currently loaded model, None if not loaded
        - 'port': If RPC Server port, if it is running
        - 'deviceVendor': The device vendor
        - 'deviceModel': The device model number
        - 'deviceSerial': The device serial number
        - 'deviceFirmware': The device firmware revision
        - 'deviceType': The device type from the model

    """
    
    resources = {}
    
    def __init__(self, **kwargs):
        super(c_Base,self).__init__(**kwargs)
        
        if 'models' in kwargs:
            self.models = kwargs['models']
        
        self.__ready = False
        
    def getControllerName(self):
        return self.__class__.__name__
        
    def _open(self):
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
        Makes necessary calls to system drivers to ready the necessary resources. 
        Populates the resources variable with a list of strings that map to 
        available resources, but does not attempt to load models for resources.
        
        Calls to open are wrapped by _open() to perform limited error handling
        
        Returns:
            True if ready, False if failure occurred
        """
        raise NotImplementedError
    
    def close(self):
        """
        Makes necessary system driver calls to close all open resources and
        deallocate all open models.
        """
        raise NotImplementedError
    
    def getModelID(self):
        raise NotImplementedError
    
    def getResources(self):
        """
        Returns:
            dict: resourceID -> (VID, PID)
        """
        raise NotImplementedError
    
    #===========================================================================
    # Automatic Controllers
    #===========================================================================
    
    def canScan(self):
        raise NotImplementedError
        
    def scan(self):
        """
        Attempts to find drivers for all available resources
        
        Returns nothing
        """
        raise NotImplementedError
    
    def refresh(self):
        """
        Refreshes the resource list, disabling resources that a no longer
        available
        """
        raise NotImplementedError

    def load(self, **kwargs):
        """
        load should be used to manually assign a driver to an available resource.
        
        Params:
           - resource - str representing the available resource
           - model - str representing the model to use
           
        If no model parameter is provided, the first suitable model will be loaded.
        
        Returns:
            True if success or False if failure
        """
        raise NotImplementedError
    
    def unload(self, **kwargs):
        """
        unload should be used to free resources and release model drivers.
        This will call a function internal to the model before marking the model
        for garbage collection
        """
        raise NotImplementedError

    
    def _getModels(self):
        """
        A protected method to get a list of model objects
        
        Returns:
            list of model objects
        """
        raise NotImplementedError
    
    #===========================================================================
    # Manual Controllers
    #===========================================================================
    
    def canEditResources(self):
        raise NotImplementedError
    
    def addResource(self):
        raise NotImplementedError
    
    def destroyResource(self):
        raise NotImplementedError
