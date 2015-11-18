Resources
=========

Resources are objects that represent a physical device connected to the system. Resources are managed by a particular
interface and contain the functionality to communicate with a single device or instrument. Resources do not, by
themselves, contain any information about how to communicate with a particular instrument. `Drivers` are used to give a
resource identity and a set of commands specific to the connected device.

Drivers
-------

Drivers are responsible for high-level communication with devices. Drivers send and receive commands from the physical
device. When a driver is loaded, all of the driver methods are available from the resource object. See
:doc:`drivers/index` for details about the methods available for each driver.

Sending commands to a resource
------------------------------

If you need to send commands directly to the resource, see :doc:`interfaces/index`. This is necessary if the driver
does not support a particular command or a driver does not exist for the device.

Properties
----------

Properties are auxiliary information about a physical device. It could include information such as:

   * Vendor
   * Model number(s)
   * Firmware Revision
   * Serial Numbers
   * etc.
	
Properties are retrieved by calling :func:`getProperties`. All resources provide the following keys in the property
dictionary:

+---------------+-------------------------------------------------+
| Key           | Description                                     |
+===============+=================================================+
| uuid          | Resource UUID                                   |
+---------------+-------------------------------------------------+
| fqn           | Fully Qualified Name of resource class          |
+---------------+-------------------------------------------------+
| interfaceName | The name of the associated interface            |
+---------------+-------------------------------------------------+
| resourceID    | Resource ID specific for that interface         |
+---------------+-------------------------------------------------+

Drivers may add additional keys to the property dictionary. There are no
restrictions to the number of keys in the property dictionary, but these will
always be provided:

+---------------+-------------------------------------------------+
| Key           | Description                                     |
+===============+=================================================+
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