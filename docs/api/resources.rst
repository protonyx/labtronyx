Resources
=========

Resources are objects that represent a physical device connected to the system.

If you need to send commands directly to the device, the resource API documents 
the available functions. This is necessary if the driver does not support a 
particular function or a driver does not exist for the device you are 
interacting with.

Some resource type may provide additional functionality not covered here. For documentation on additional features,
see the docs for the interface for that particular resource.

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
	
Properties are retrieved by calling :func:`getProperties`. All resources provide
the following keys in the property dictionary:

+---------------+-------------------------------------------------+
| Key           | Description                                     |
+---------------+-------------------------------------------------+
| uuid          | Resource UUID                                   |
+---------------+-------------------------------------------------+
| interface     | The name of the associated interface            |
+---------------+-------------------------------------------------+
| resourceID    | Resource ID specific for that interface         |
+---------------+-------------------------------------------------+
| resourceType  | Resource type string for driver identification  |
+---------------+-------------------------------------------------+
| address       | RPC server address                              |
+---------------+-------------------------------------------------+
| hostname      | RPC server hostname                             |
+---------------+-------------------------------------------------+
| port          | RPC port                                        |
+---------------+-------------------------------------------------+

Drivers may add additional keys to the property dictionary. There are no
restrictions to the number of keys in the property dictionary, but these will
always be provided:

+---------------+-------------------------------------------------+
| Key           | Description                                     |
+---------------+-------------------------------------------------+
| driver        | Driver name                                     |
+---------------+-------------------------------------------------+
| deviceType    | Device type                                     |
+---------------+-------------------------------------------------+
| deviceVendor  | Device vendor or manufacturer                   |
+---------------+-------------------------------------------------+
| deviceModel   | Device model number                             |
+---------------+-------------------------------------------------+
| deviceSerial  | Device serial number                            |
+---------------+-------------------------------------------------+
| deviceFirmware| Device firmware revision number                 |
+---------------+-------------------------------------------------+

Error Handling
--------------

If an error is encountered during communication with an instrument or device,
an exception will be raised that must be caught downstream.

Interface related exceptions are generated when a problem occurs during a
device-level function call like :func:`write`, :func:`read` or :func:`query`:

+------------------+-----------------------------------------------------------+
| InterfaceError   | An exception was caught that could not be corrected       |
+------------------+-----------------------------------------------------------+
| InterfaceTimeout | The device took too long to respond to a request          |
+------------------+-----------------------------------------------------------+
| ResourceNotOpen  | The resource was not open                                 |
+------------------+-----------------------------------------------------------+

Driver-specific exceptions are generated based on data received from an
instrument. The documentation for each driver will specify how these exceptions
are to be handled:

+------------------+-----------------------------------------------------------+
| InvalidData      | The device returned data that didnt make sense            |
+------------------+-----------------------------------------------------------+
| DeviceError      | The device reported an error                              |
+------------------+-----------------------------------------------------------+
   
Resource API
------------

.. autoclass:: labtronyx.bases.resource.Base_Resource
   :members: