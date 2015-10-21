"""
Getting started
---------------

All resources are subclasses of the :class:`labtronyx.bases.Base_Resource` class. Creating a resource is simple::

    from labtronyx.bases import Base_Interface, Base_Resource

    class RESOURCE_CLASS_NAME(Base_Resource):
        pass

Errors
------

Labtronyx has a number of build-in exception types that can be raised from resources. To import them::

   from labtronyx.common.errors import *

Packaging
---------

Interfaces and Resources are typically packaged together in a single plugin, as the interface is responsible for
instantiating and maintaining resource objects.

Instantiation
-------------

Resources are instantiated by an interface, not InstrumentManager.

When resources are created, they should be in the closed state. This is to prevent any locking issues if multiple
instances of Labtronyx are open. Resources should typically only be open if they are actively in use.

Usage Model
-----------

Resources may implement more functions than just those which are defined in the API below. When a driver is loaded, all
of the driver functions are linked at runtime to the resource object. All driver functions are accessed directly from
the resource object as if they were a single object. Some things to note:

   * If there is a naming conflict between a method in the resource and a method in the driver, the resource method
     will be called
   * Driver functions cannot be called if the resource is not open

.. note::

   In order to support proper operation using Remote Resources and Instruments, some limitations should be imposed to
   ensure maximum compatibility. All methods within a resource or driver must return serializable data.
   Serializable data types include:

       * str
       * unicode
       * int
       * long
       * float
       * bool
       * list
       * tuple
       * dict
       * None

   If a method returns an object that is not serializable, an exception will be passed back to the remote host. If the
   method returns a non-serializable data type, the method should be prefixed with an underscore ('_') to mark it as a
   protected function that cannot be accessed remotely.
"""

import uuid
import logging

import labtronyx.common as common

from labtronyx.common.plugin import PluginBase

class Base_Resource(PluginBase):
    """
    Resource Base Class
    """

    resourceType = "Generic"
    
    def __init__(self, manager, interface, resID, **kwargs):
        """
        :param manager:         Reference to the InstrumentManager instance
        :type manager:          InstrumentManager object
        :param interface:       Reference to the interface instance
        :type interface:        object
        :param resID:           Resource Identifier
        :type resID:            str
        """
        PluginBase.__init__(self)

        self._manager = manager
        self._interface = interface
        self._resID = resID

        self.logger = kwargs.get('logger', logging)

        # Instance variables
        self._uuid = str(uuid.uuid4())
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
                    # Driver functions are locked out if the resource is not open
                    raise common.errors.ResourceNotOpen("Unable to call driver function on closed resource")

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

    @property
    def resID(self):
        return self._resID

    @property
    def uuid(self):
        return self._uuid

    @property
    def driver(self):
        return self._driver
    
    def getProperties(self):
        """
        Get the resource property dictionary

        :return: dict
        """
        driver_prop = {}

        # Append Driver properties if a Driver is loaded
        if self._driver is not None:
            driver_prop = self._driver.getProperties()

            driver_prop.setdefault('driver', self._driver.name)
            driver_prop.setdefault('deviceType', self._driver.info.get('deviceType', ''))
            driver_prop.setdefault('deviceVendor', self._driver.info.get('deviceVendor', ''))
        
        res_prop = {
            'uuid': self._uuid,
            'interface': self._interface.name,
            'resourceID': self._resID,
            'resourceType': self.resourceType
        }
          
        driver_prop.update(res_prop)
        
        return driver_prop
    
    #===========================================================================
    # Resource State
    #===========================================================================
    
    def isOpen(self):
        """
        Check if the resource is currently open

        :return:    bool
        """
        raise NotImplementedError
        
    def open(self):
        """
        Open the resource. If a driver is loaded, the driver `open` method will also be called
        
        :returns:   True if open was successful, False otherwise
        :raises:    ResourceUnavailable
        """
        if self._driver is not None:
            return self._driver.open()

        else:
            return True
    
    def close(self):
        """
        Close the resource
        
        :returns: True if close was successful, False otherwise
        """
        if self._driver is not None:
            return self._driver.close()

        else:
            return True
        
    def refresh(self):
        """
        Refresh the resource
        """
        raise NotImplementedError
    
    #===========================================================================
    # Data Transmission
    #===========================================================================
    
    def write(self, data):
        """
        Send ASCII-encoded data to the instrument. Termination character may be appended automatically.

        :param data:        Data to send
        :type data:         str
        :raises:            ResourceNotOpen
        :raises:            InterfaceTimeout
        """
        raise NotImplementedError

    def write_raw(self, data):
        """
        Send Binary-encoded data to the instrument without modification

        :param data:        Data to send
        :type data:         str
        :raises:            ResourceNotOpen
        :raises:            InterfaceError
        """
        raise NotImplementedError
    
    def read(self):
        """
        Read ASCII-formatted data from the instrument. Return conditions are interface-dependent, but typically data is
        returned when a termination character is read or a full packet is received.

        :return:            str
        :raises:            ResourceNotOpen
        :raises:            InterfaceTimeout
        """
        raise NotImplementedError

    def read_raw(self):
        """
        Read Binary-encoded data directly from the instrument.

        :param size:        Number of bytes to read
        :type size:         int
        :raises:            ResourceNotOpen
        :raises:            InterfaceTimeout
        :raises:            InterfaceError
        """
        raise NotImplementedError
    
    def query(self, data):
        """
        Retrieve ASCII-encoded data from the device given a prompt.

        A combination of write(data) and read()

        :param data:        Data to send
        :type data:         str
        :param delay:       delay (in seconds) between write and read operations.
        :type delay:        float
        :returns:           str
        :raises:            ResourceNotOpen
        :raises:            InterfaceTimeout
        :raises:            InterfaceError
        """
        raise NotImplementedError

    #===========================================================================
    # Driver Helpers
    #===========================================================================

    def hasDriver(self):
        """
        Check if the resource has a driver loaded

        :return:                bool
        """
        return self._driver is not None
    
    def loadDriver(self, driverName, force=False):
        """
        Load a Driver for a resource. A driver name can be specified, even if it may not be compatible with this
        resource. Existing driver is no unloaded unless the `force` parameter is set to True.
        
        :param driverName:      Module name of the desired Model
        :type driverName:       str
        :param force:           Force load driver by unloading existing driver
        :returns:               True if successful, False otherwise
        """
        if self._driver is not None and not force:
            return False

        if force:
            self.unloadDriver()

        # Check if the specified model is valid
        if driverName in self.manager.drivers:
            self.logger.debug('Loading driver [%s] for resource [%s]', driverName, self._resID)

            testClass = self.manager.drivers.get(driverName)

            # Instantiate driver
            try:
                self._driver = testClass(self, logger=self.logger)
                self._driver.name = driverName

                # Signal the event
                self.manager._publishEvent(common.constants.ResourceEvents.driver_load)

                # Call the driver open if the resource is already open
                if self.isOpen():
                    self._driver.open()

            except NotImplementedError:
                pass

            except:
                self.logger.exception('Exception during driver load: %s', driverName)

                self.unloadDriver()

                return False

            return True
    
    def unloadDriver(self):
        """
        If a driver is currently loaded for the resource, unload it. This will close the resource as well.
        
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
            
            self.logger.debug('Unloaded driver for resource [%s]', self._resID)

            # Signal the event
            self.manager._publishEvent(common.constants.ResourceEvents.driver_unload)
               
            return True
        
        else:
            return False