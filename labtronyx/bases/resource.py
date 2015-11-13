"""
Getting started
---------------

All resources are subclasses of the :class:`labtronyx.bases.ResourceBase` class. Creating a resource is simple::

    from labtronyx.bases import ResourceBase

    class RESOURCE_CLASS_NAME(ResourceBase):
        pass

Attributes
----------

Resources have some attributes that should be defined.

Errors
------

Labtronyx has a number of build-in exception types that can be raised from resources. To import them::

   from labtronyx.common.errors import *

Packaging
---------

Interfaces and Resources are typically packaged together in a single plugin, as the interface is responsible for
instantiating and maintaining resource objects.

Usage Model
-----------

When resources are created, they should default to the closed state. This is to prevent any locking issues if multiple
instances of Labtronyx are open. Resources should typically only be open if they are actively in use.

When a driver is loaded, the resource object acts as a proxy to access the driver methods. All driver functions are
accessed directly from the resource object as if they were a single object. Some things to note:

   * If there is a naming conflict between a method in the resource and a method in the driver, the resource method
     will take priority
   * Driver functions are inaccessible and cannot be called if the resource is closed

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

Resources may implement more functions than just those which are defined in the API below, see the interface and
resource class documentation to learn more.
"""
# Package relative imports
from ..common import events
from ..common.errors import *
from ..common.plugin import PluginBase, PluginAttribute

__all__ = ['ResourceBase']


class ResourceBase(PluginBase):
    """
    Resource Base Class. Acts as a proxy for driver if one is loaded.

    :param manager:         InstrumentManager instance
    :type manager:          labtronyx.InstrumentManager
    :param interface:       Reference to the interface instance
    :type interface:        labtronyx.bases.interface.InterfaceBase
    :param resID:           Resource Identifier
    :type resID:            str
    :param logger:          Logger instance
    :type logger:           logging.Logger
    """
    pluginType = 'resource'
    
    def __init__(self, manager, interface, resID, **kwargs):
        PluginBase.__init__(self, **kwargs)

        self._manager = manager
        self._interface = interface
        self._resID = resID

        # Instance variables
        self._driver = None
            
    def __del__(self):
        try:
            self.close()
        except:
            pass
        
    def __getattr__(self, name):
        if self._driver is not None:
            if hasattr(self._driver, name):
                # Only call driver functions if the resource is open
                if self.isOpen():
                    return getattr(self._driver, name)

                else:
                    # Driver functions are locked out if the resource is not open
                    raise ResourceNotOpen("Unable to call driver function on closed resource")

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
    def driver(self):
        """
        :rtype: labtronyx.bases.driver.DriverBase
        """
        return self._driver
    
    def getProperties(self):
        """
        Get the property dictionary for the resource. If a driver is loaded, the driver properties will be merged and
        returned as well

        :rtype: dict[str:object]
        """
        res_prop = super(ResourceBase, self).getProperties()
        res_prop.update({
            'interface': self._interface.interfaceName,
            'resourceID': self._resID
        })

        if self._driver is not None:
            driver_prop = self._driver.getProperties()

            if hasattr(driver_prop, 'uuid'):
                del driver_prop['uuid']
            driver_prop.setdefault('driver', self._driver.fqn)
            driver_prop.setdefault('deviceType', self._driver.deviceType)

            # Resource properties take precedence over driver properties
            driver_prop.update(res_prop)
            return driver_prop

        else:
            return res_prop
    
    #===========================================================================
    # Resource State
    #===========================================================================
    
    def isOpen(self):
        """
        Check if the resource is currently open

        :return:    bool
        """
        return False
        
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
        :raises:                KeyError if driver class not found
        """
        if self.hasDriver() and not force:
            return False

        if force:
            self.unloadDriver()

        self.logger.debug('Loading driver [%s] for resource [%s]', driverName, self._resID)

        # Instantiate driver
        try:
            self._driver = self.manager.plugin_manager.createPluginInstance(driverName,
                                                                            resource=self,
                                                                            logger=self.logger)

            # Signal the event
            self.manager._publishEvent(events.EventCodes.resource.driver_loaded, self.uuid, driverName)

            # Call the driver open if the resource is already open
            if self.isOpen():
                self._driver.open()

        except KeyError:
            raise KeyError("Driver not found")

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
            except ResourceNotOpen:
                pass
            except:
                self.logger.exception('Exception while unloading driver')
                return False
            finally:
                self.close()

            self.manager.plugin_manager.destroyPluginInstance(self._driver.uuid)
            self._driver = None
            
            self.logger.debug('Unloaded driver for resource [%s]', self._resID)

            # Signal the event
            self.manager._publishEvent(events.EventCodes.resource.driver_unloaded, self.uuid)
               
        return True