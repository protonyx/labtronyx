import uuid
import importlib

import labtronyx.common as common

from labtronyx.common.plugin import PluginBase

class Base_Resource(PluginBase):
    type = "Generic"
    
    def __init__(self, manager, interface, resID, **kwargs):
        
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')

        self._manager = manager
        self._interface = interface
        self._uuid = str(uuid.uuid4())
        self._resID = resID
        
        self._driver = None
            
    def __del__(self):
        try:
            self.close()
        except Exception as e:
            pass
        
    def __getattr__(self, name):
        if self._driver is not None:
            if hasattr(self._driver, name):
                # Only call driver functions if the resource is open
                if self.isOpen():
                    return getattr(self._driver, name)
                else:
                    # TODO: Raise the correct exception on failure here
                    raise RuntimeError("Resource not open, unable to call driver function")

            else:
                raise AttributeError
            
        else:
            raise AttributeError

    def __enter__(self):
        self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def manager(self):
        return self._manager

    @property
    def interface(self):
        return self._interface

    def getResourceID(self):
        return self._resID

    resID = property(getResourceID)

    def getUUID(self):
        return self._uuid

    uuid = property(getUUID)
    
    def getResourceType(self):
        return self.type
    
    def getInterfaceName(self):
        """
        Returns the Resource's Controller class name
        
        :returns: str
        """
        return self._interface.getInterfaceName()
    
    def getProperties(self):
        driver_prop = {}

        # Append Driver properties if a Driver is loaded
        if self._driver is not None:
            driver_prop = self._driver.getProperties()

            driver_prop.setdefault('driver', self._driver.name)
            driver_prop.setdefault('deviceType', self._driver.info.get('deviceType', ''))
            driver_prop.setdefault('deviceVendor', self._driver.info.get('deviceVendor', ''))
        
        res_prop = {
            'uuid': self.getUUID(),
            'interface': self.getInterfaceName(),
            'resourceID': self.getResourceID(),
            'resourceType': self.getResourceType()
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
        if self._driver is not None:
            self._driver.open()

        else:
            raise NotImplementedError
    
    def close(self):
        """
        Close the resource
        
        :returns: True if close was successful, False otherwise
        """
        if self._driver is not None:
            self._driver.close()
        else:
            raise NotImplementedError
        
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

    @property
    def driver(self):
        return self._driver
    
    def hasDriver(self):
        return self._driver is not None
    
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
        if self._driver is not None:
            return False
        
        try:
            # Check if the specified model is valid
            if driverName in self.manager.drivers:
                self.logger.debug('Loading driver [%s] for resource [%s]', driverName, self.getResourceID())

                testClass = self.manager.drivers.get(driverName)
            
                # Instantiate driver
                self._driver = testClass(self,
                                        logger=self.logger,
                                        config=self.config)
                self._driver.name = driverName

                # Call the driver open if the resource is already open
                if self.isOpen():
                    try:
                        self._driver.open()
                    except NotImplementedError:
                        pass

                # Signal the event
                self.manager._event_signal(common.constants.ResourceEvents.driver_load)

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
        if self._driver is not None:
            try:
                self._driver.close()
            except NotImplementedError:
                pass
            except:
                self.logger.exception('Exception while unloading driver')
            finally:
                self.close()
                
            self._driver = None
            
            self.logger.debug('Unloaded driver for resource [%s]', self.getResourceID())

            # Signal the event
            self.manager._event_signal(common.constants.ResourceEvents.driver_unload)
               
            return True
        
        else:
            return False