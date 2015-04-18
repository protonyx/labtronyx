Resources
=========

Resources are objects that represent a physical device connected to the system.

If you need to send commands directly to the device, the resource API documents 
the available functions. This is necessary if the driver does not support a 
particular function or a driver does not exist for the device you are 
interacting with.

The Resource types that are currently supported are:

   - :class:`labtronyx.interfaces.i_VISA.r_VISA`
   - :class:`labtronyx.interfaces.i_Serial.r_Serial`
   - :class:`labtronyx.interfaces.i_UPEL.r_UPEL`
   
Status
------

The status of a resource can be queried by calling 
:func:`labtronyx.Base_Resource.getResourceStatus`. Resource status can be in
any of these states:

   * INIT - Resource does not have a driver loaded
   * READY - Resource has a driver loaded and is ready
   * ERROR - An error has occurred
   
To get additional information about an error, call
:func:`labtronyx.Base_Resource.getResourceError`. Errors include any of the
following:

   * UNAVAILABLE - The Resource is locked by the system or is busy and cannot be 
     used
   * NOTFOUND - The Interface denies knowing anything about the Resource. It may
     have been disconnected. A Resource with this error will likely be deleted
     soon
   * UNRESPONSIVE - The Resource is available, but there are no responses from
     any connected instruments or devices
   * UNKNOWN - Some other error has occurred that could not be explained. Good
     luck.

Properties
----------

Properties are auxiliary information about a physical device. It could include
information such as:

	* Firmware Revision
	* Serial Numbers
	* Product Codes
	* Number of channels
	* Operating Frequencies
	* Command Set Revision
	* etc.
	
Properties are retrieved by calling :func:`getProperties`. D

+---------------+-------------------------------------------------+
| Key           | Description                                     |
+---------------+-------------------------------------------------+
| 'uuid'        | Resource UUID                                   |
+---------------+-------------------------------------------------+
| 'controller'  | The module name for the controller              |
+---------------+-------------------------------------------------+
| 'resourceID'  | Resource ID specific for the controller         |
+---------------+-------------------------------------------------+
| 'vendorID'    | Vendor ID used to find compatible Drivers       |
+---------------+-------------------------------------------------+
| 'productID'   | Product ID used to find compatible Drivers      |
+---------------+-------------------------------------------------+
| 'modelName'   | The module name for the currently loaded model  |
+---------------+-------------------------------------------------+
| 'port'        | RPC port                                        |
+---------------+-------------------------------------------------+

Error Handling
--------------

If an error is encountered during communication with an instrument or device,
an exception will be raised that must be caught downstream.

Interface related exceptions are generated when a problem occurs during a
device-level function call like :func:`write`, :func:`read` or :func:`query`:

   - InterfaceError
   - InterfaceTimeout
   - ResourceNotOpen

Driver-specific exceptions are generated based on data received from an
instrument. The documentation for each driver will specify how these exceptions
are to be handled:

   - InvalidData
   - DeviceError

Manually Managing Resources
---------------------------

.. note::

   This is an experimental feature and has not been well tested, since there
   are no devices currently that would need this support. Its possible it won't
   work at all. This section should give you an idea of how it will work...
   someday.

The ability to manage resources is dependent on the nature of a controller.
Most controllers accessed a fixed set of system resources that are known.
A serial controller is an example of this, as the system only allows connection
to a known COM port and provides a list of available ports. Some controllers
may not always be aware of available resources. For example, if a controller
interfaces with a CAN bus, it may need additional information like a device
address in order to establish communication. It is not always practical to scan
through the entirety of possible device addresses to find a device.

For controllers that support manually adding resources::

	from InstrumentControl import InstrumentControl
   	instr = InstrumentControl()
   	
   	new_uuid = instr.addResource('c_CAN', 'ACME', 'ABC 2000')
   	
   	# Refresh the resources list to find the new resource
   	instr.refreshManager()
   	
   	widget = instr.getInstrument_model('ABC 2000')
   	
To destroy a resource, provide the Resource UUID::

	instr.destroyResource('c_CAN', '360ba14f-19be-11e4-95bf-a0481c94faff')
   
Resource APIs
-------------

.. autoclass:: labtronyx.interfaces.i_VISA.r_VISA
   :members:

.. autoclass:: labtronyx.interfaces.i_Serial.r_Serial
   :members:

.. autoclass:: labtronyx.interfaces.i_UPEL.r_UPEL
   :members: