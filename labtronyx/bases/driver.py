"""
Getting Started
---------------

All Drivers extend :class:`labtronyx.DriverBase`::

    import labtronyx

    class DRIVER_CLASS_NAME(labtronyx.DriverBase):
        pass

Required Attributes
-------------------

Drivers require some attributes to be defined in order to specify which resource types and interfaces they are
compatible with.

   * `deviceType` - str to describe the type or function of the device
   * `compatibleInterfaces` - list of interface names that the driver is compatible with e.g. ['Serial', 'VISA']
   * `compatibleInstruments` - dict of vendors and models that the driver is compatible with. The keys to the dictionary
     are vendors and the values are a list of models e.g. {'Agilent': ['ACME123']}

Properties
----------

Like Resources, Drivers can provide auxiliary information about a physical device by returning a dictionary of
key-value pairs from the method :func:`getProperties`. Properties can be useful for application and script
development by enabling or disabling features according to data contained in the properties. Driver properties can
relate information about a device or instrument that require specific commands such as:

   * Serial number
   * Model number
   * Firmware revision
   * Product Codes
   * Number of channels
   * Operating Frequencies
   * Command Set Revision

Warning::

   The :func:`getProperties` method of the driver may be called when a resource is not open, so any commands that
   require the resource to be open should be wrapped with :func:`isOpen` to prevent exceptions from being raised.

It is recommended that drivers should provide these properties to assist scripts or applications to locate a resource:

+-----------------+---------------+-------------------------------------+
| Key             | Default Value | Examples                            |
+=================+===============+=====================================+
| deviceVendor    | 'Generic'     | 'Tektronix', 'Agilent Technologies' |
+-----------------+---------------+-------------------------------------+
| deviceModel     | 'Device'      | 'DPO2024', '2831E'                  |
+-----------------+---------------+-------------------------------------+
| deviceSerial    | 'Unknown'     | '12345'                             |
+-----------------+---------------+-------------------------------------+
| deviceFirmware  | 'Unknown'     | '1.0.0'                             |
+-----------------+---------------+-------------------------------------+

If serial number and firmware information has be retrieved from the device, it should be done during the :func:`open`
method.

Usage Model
-----------

Driver objects are instantiated and stored in the resource object. When a driver is loaded, all methods are dynamically
loaded into the resource object and can be accessed by calling the method from the resource. To prevent exceptions,
Driver methods are inaccessible unless the resource is open by a call to the resource method `open`.

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
# Package relative imports
from ..common import events
from ..common.errors import *
from ..common.plugin import PluginBase, PluginAttribute

__all__ = ['DriverBase']


class DriverBase(PluginBase):
    """
    Driver Base Class

    :param resource:        Resource instance
    :type resource:         labtronyx.bases.resource.ResourceBase
    :param logger:          Logger instance
    :type logger:           logging.Logger
    """
    pluginType = 'driver'

    deviceType = PluginAttribute(attrType=str, defaultValue="Generic")
    compatibleInterfaces = PluginAttribute(attrType=list, required=True)
    compatibleInstruments = PluginAttribute(attrType=dict, defaultValue={})
    
    def __init__(self, resource, **kwargs):
        PluginBase.__init__(self, **kwargs)

        self._resource = resource

    def __getattr__(self, name):
        if hasattr(self._resource, name):
            return getattr(self._resource, name)
        else:
            raise AttributeError("Unable to find attribute in driver or resource")

    def _rpc(self, request):
        raise RuntimeError("Driver methods must be accessed through resource")

    @property
    def resource(self):
        return self._resource
            
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