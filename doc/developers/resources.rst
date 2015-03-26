Resources
=========

The core function of the InstrumentManager is to manage resources that are
connected to that system. In general, a resource represents an instrument that
is connected to the local machine and is known to the operating system.

Internally, resources are stored using three pieces of information that make 
them uniquely identifiable and can be used to establish communication with the 
physical device:

	* Universally Unique IDentifier (str)
	* `Controller` name (str)
	* Resource Identifier (str)
	
Properties
----------

Properties are auxiliary information about a physical device. The keys and data
contained in the properties are dependent on the device and Model, but the
following keys will exist for all resources.

	* 'uuid': Unique Resource Identifier
	* 'controller': The module name for the controller
	* 'resourceID': Resource ID specific for the controller
	* 'vendorID': Vendor ID used to find compatible Models
	* 'productID': Product ID used to find compatible Models