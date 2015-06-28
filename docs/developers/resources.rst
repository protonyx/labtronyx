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

Remote Procedure Call (RPC)
---------------------------

If RPC is enabled, an RPC Server will be spawned when the resource is
instantiated. RPC exposes the resource object to remote execution via a TCP/IP
port. The port is randomly selected when the RPC Server is started. 

There are limitations to the types of data that can be sent using RPC across the 
network. All functions within a resource or driver must return serializable data
for transport using. Serializable data types include:

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

If a function returns an object that is not serializable, an exception will be
passed back to the remote host. To avoid this, the function name should be 
prefixed with an underscore ('_'). This designates the function as a protected 
function, and the RPC library will reject calls that function.

.. See :doc:`Remote Procedure Call (RPC) Library <common>`.
	
Properties
----------

Properties are auxiliary information about a physical device. The keys and data
contained in the properties are dependent on the device and Model, but the
following keys will exist for all resources.

	* 'uuid': Unique Resource Identifier
	* 'controller': The module name for the controller
	* 'resourceID': Resource ID specific for the controller
	
	
Resource Template
-----------------

.. literalinclude:: templates/tp_resource.py

Base Resource API
-----------------

.. autoclass:: labtronyx.Base_Resource.Base_Resource
   :members: