Interfaces
==========

Interfaces handle low-level operating system interactions. This may include 
calls to hardware via driver stacks, or calls to other Python libraries.



.. note::
	VISA, Serial (RS-232), USB are examples of controllers

Types of Controllers
--------------------

* Automatic - These controllers can find resources on their own without any 
  additional knowledge. This is typically achieved with a system driver that is
  "plug-'n-play" capable and enumerates devices on insertion.
  
* Manual - These controllers must have additional knowledge to discover a 
  resource. An example of a manual controller is a TCP/IP device. Not all 
  devices will respond to a multi-cast packet, so the user must supply an IP 
  address to find the device.
  
* Hybrid - These controllers can discover resources, but without additional
  information, they will not be able to match a model driver to the
  resource. A serial port controller is an example of this, as the system
  maintains a list of available COM ports, but the user must supply the
  baud rate, stop bits and parity information for the controller to be able
  to establish communication. 

Resources
=========

Interfaces are responsible for maintaining a list of available resources that 
it has access to. Controller resources are identified by a string identifier
that directly corresponds to the device within the system. In general, a 
resource represents an instrument or device that is connected to the local 
machine and is known to the operating system.

When new resources are found, the interface should instantiate an object that
extends the Base_Resource class. The interface should then notify the
Instrument Manager that a new resource is available. 
	
Properties
----------

Properties are auxiliary information about a physical device. The keys and data
contained in the properties are dependent on the device and Model, but the
following keys will exist for all resources.

	* 'uuid': Unique Resource Identifier
	* 'controller': The module name for the controller
	* 'resourceID': Resource ID specific for the controller
	
  
Controller Template
-------------------

.. literalinclude:: templates/tp_interface.py

Required API Implementations
----------------------------

.. autoclass:: labtronyx.Base_Interface.Base_Interface
   :members: open, close, getResources

Optional API Implementations
----------------------------

.. autoclass:: labtronyx.Base_Interface.Base_Interface
   :members: refresh
   
