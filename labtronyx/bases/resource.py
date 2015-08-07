import uuid
import importlib
import socket

import labtronyx.common.status as resource_status

class Base_Resource(object):
    type = "Generic"
    
    def __init__(self, manager, interface, resID, **kwargs):
        
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')

        self.__manager = manager
        self.__interface = interface
        
        self.__uuid = str(uuid.uuid4())
        self.__resID = resID
        self.__status = 'INIT'
        self.__error = None
        
        self.__lock = None
        
        self.driver = None
            
    def __del__(self):
        try:
            self.close()
        except Exception as e:
            pass
        
    def __getattr__(self, name):
        if self.driver is not None:
            if hasattr(self.driver, name):
                return getattr(self.driver, name)
            else:
                raise AttributeError
            
        else:
            raise AttributeError

    @property
    def manager(self):
        return self.__manager

    @property
    def interface(self):
        return self.__interface

    def getResourceID(self):
        return self.__resID

    resID = property(getResourceID)

    def getUUID(self):
        return self.__uuid

    uuid = property(getUUID)
    
    def getResourceType(self):
        return self.type
    
    def getResourceStatus(self):
        return self.__status
    
    def setResourceStatus(self, new_status):
        self.__status = new_status

    def getError(self):
        """
        Get the last error that occured during the last interface I/O operation.

        :returns: str
        """
        return self._error
    
    def getInterfaceName(self):
        """
        Returns the Resource's Controller class name
        
        :returns: str
        """
        return self.__interface.getInterfaceName()
    
    def getProperties(self):
        driver_prop = {}

        # Append Driver properties if a Driver is loaded
        if self.driver is not None:
            driver_prop = self.driver.getProperties()

            driver_prop.setdefault('driver', self.driver.name)
            driver_prop.setdefault('deviceType', self.driver.info.get('deviceType', ''))
            driver_prop.setdefault('deviceVendor', self.driver.info.get('deviceVendor', ''))
        
        res_prop = {
            'uuid': self.getUUID(),
            'interface': self.getInterfaceName(),
            'resourceID': self.getResourceID(),
            'resourceType': self.getResourceType(),
            'status': self.getResourceStatus(),
            'error': self.__error
            }
          
        driver_prop.update(res_prop)
        
        return driver_prop
    
    #===========================================================================
    # Resource State
    #===========================================================================
    
    def isOpen(self):
        raise NotImplementedError
        
    def open(self):
        """
        Open the resource
        
        :returns: True if open was successful, False otherwise
        """
        if self.driver is not None:
            self.driver.open()

        else:
            raise NotImplementedError
    
    def close(self):
        """
        Close the resource
        
        :returns: True if close was successful, False otherwise
        """
        if self.driver is not None:
            self.driver.close()
        else:
            raise NotImplementedError
    
    def checkResourceStatus(self):
        """
        Raise an error if the resource is not ready. Used in resources that
        sub-class Base_Resource to prevent attempted data transfer when the
        resource is in a bad state.
        
        :raises: common.resource_status.ResourceNotReady()
        """
        if self.getResourceStatus() != resource_status.READY:
            raise resource_status.ResourceNotReady()
        
    def refresh(self):
        """
        Refresh the resource
        """
        raise NotImplementedError
    
    #===========================================================================
    # Data Transmission
    #===========================================================================
    
    def write(self, data):
        raise NotImplementedError
    
    def read(self):
        raise NotImplementedError
    
    def query(self, data):
        raise NotImplementedError

    #===========================================================================
    # Driver
    #===========================================================================
    
    def hasDriver(self):
        return self.driver is not None
    
    def loadDriver(self, driverName):
        """
        Load a Driver for a resource. A driver name can be specified to load a 
        specific module, even if it may not be compatible with this resource. 
        Reloads driver when importing, in case an update has occured.
        
        Example::
        
            instr = manager.findInstruments(resourceID='COM5')[0]
            
            instr.loadDriver('drivers.BK_Precision.Load.m_85XX')
        
        :param driverName: Module name of the desired Model
        :type driverName: str
        :returns: True if successful, False otherwise
        """
        if self.driver is not None:
            return False
        
        try:
            # Check if the specified model is valid
            testModule = importlib.import_module(driverName)
            reload(testModule) # Reload the module in case anything has changed
            
            className = driverName.split('.')[-1]
            testClass = getattr(testModule, className)
            
            self.logger.debug('Loading driver [%s] for resource [%s]', driverName, self.getResourceID())
            
            # Instantiate driver
            self.driver = testClass(self, 
                                    logger=self.logger, 
                                    config=self.config)
            
            return True

        except:
            self.logger.exception('Exception during driver load: %s', driverName)
            
            self.unloadDriver()
            
            return False
    
    def unloadDriver(self):
        """
        If a Driver is currently loaded for the resource, unload it. This will close the resource as well.
        
        :returns: True if successful, False otherwise
        """
        if self.driver is not None:
            try:
                self.close()
                
            except:
                self.logger.exception('Exception while unloading driver')
                
            self.driver = None
            
            self.logger.debug('Unloaded driver for resource [%s]', self.getResourceID())
               
            return True
        
        else:
            return False

class ResourceNotOpen(RuntimeError):
    pass
