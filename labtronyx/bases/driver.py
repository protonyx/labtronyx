"""
Getting Started
---------------

All Drivers extend :class:`labtronyx.bases.Base_Driver`::

    from labtronyx.bases import Base_Driver

    class DRIVER_CLASS_NAME(Base_Driver):
        pass

Properties
----------

Drivers can provide auxiliary information about a physical device in the
properties. Properties can be useful for application and script development
by enabling or disabling features according to data contained in the properties.

All drivers should provide the minimum properties to ensure a device can be
found by an application or script:

+-----------------+---------------+-------------------------------------+
| Key             | Default Value | Examples                            |
+-----------------+---------------+-------------------------------------+
| 'deviceType'    | 'Generic'     | 'Multimeter', 'Oscilloscope'        |
+-----------------+---------------+-------------------------------------+
| 'deviceVendor'  | 'Generic'     | 'Tektronix', 'Agilent Technologies' |
+-----------------+---------------+-------------------------------------+
| 'deviceModel'   | 'Device'      | 'DPO2024', '2831E'                  |
+-----------------+---------------+-------------------------------------+
| 'deviceSerial   | 'Unknown'     | '12345'                             |
+-----------------+---------------+-------------------------------------+
| 'deviceFirmware'| 'Unknown'     | '1.0.0'                             |
+-----------------+---------------+-------------------------------------+

Serial number and firmware information should be retrieved from the device.

Example::

	def getProperties(self):

		prop['deviceVendor'] = 'my vendor'
		prop['deviceModel'] = 'ABC 12345'
		prop['deviceSerial'] = '0123456789'
		prop['deviceFirmware'] = '1.0'
		prop['deviceType'] = 'Widget'

		return prop

Usage Model
-----------

Driver objects are instantiated and stored in the resource object. When a driver is loaded, all methods are dynamically
loaded into the resource object and can be accessed by calling the method from the resource.

In order to maintain functional abstraction, Drivers should limit dependencies on outside libraries and avoid making
system driver calls. All code contained in drivers should deal with the specific instrument's command set and use
resource API calls to communicate with the instrument.

If drivers need to support more than one interface, be sure to only use resource methods that are common to all
interfaces.

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

import logging

from labtronyx.common.plugin import PluginBase

class Base_Driver(PluginBase):
    """
    Driver Base Class
    """
    
    info = {}
    
    def __init__(self, resource, **kwargs):
        """
        :param resource: Reference to the associated resource instance
        :type resource: object
        """
        PluginBase.__init__(self)

        self._resource = resource

        self.logger = kwargs.get('logger', logging)

        # Instance variables
        self._name = self.__class__.__module__ + '.' + self.__class__.__name__

    def __getattr__(self, name):
        if hasattr(self._resource, name):
            return getattr(self._resource, name)
        else:
            raise AttributeError

    @property
    def resource(self):
        return self._resource

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
            
    # ===========================================================================
    # Optional Functions
    # ===========================================================================
        
    def open(self):
        """
        Prepare the device to receive commands. Called after the resource is opened, so any calls to resource functions
        should work.

        This function can be used to configure the device for remote control, reset the device, etc.
        """
        return True
    
    def close(self):
        """
        Prepare the device to close. Called before the resource is closed, so any calls to resource functions should
        work.
        """
        return True
    
    def getProperties(self):
        return {}