Models
======

Models are responsible for high-level communication with devices. Models send 
and receive commands from the physical device using a controller. In order to
maintain functional abstraction, Models should limit dependencies and avoid
making system driver calls. All code contained in Models should deal with the
specific instrument's command set. 

Models are the second highest level of abstraction. By separating system driver
calls from the instrument command set, the code is more portable and adaptable
to operating system changes and even various physical connections (protocols,
connectors, etc.). By so doing, the same model can be used without needing 
knowledge of the underlying controller that is being used. The Model simply
lists which controllers it is compatible with, and InstrumentManager takes care
of the rest.

All models extend :class:`models.mBase`, which attaches a RpcServer thread to the
model, allowing communication from InstrumentManagers. Remote Procedure Call
(RPC) allows an object to be accessed from any networked machine as if it were
a local object on the operator's machine. This allows really easy application
and script development, as the communication with the instrument over the
network is taken care of by the :mod:`common.Rpc` library.
    
Execution Model
---------------

Model objects are stored in the same process and memory space as
InstrumentManager. When models are loaded, they are passed a reference to the 
parent controller and the Resource Identifier for the associated resource. 
This enables the model to communicate directly with the controller and get any 
additional information that is needed to send commands or receive data from the 
physical device.

If no errors are raised during Model instantiation,
an RPC Server thread is spawned for that Model by calling :func:`rpc_start`.
This function is inherited from :class:`common.Rpc.RpcBase`, which is inherited
from :class:`models.m_Base`. For information about the execution model of the
RPC server, see :doc:`Remote Procedure Call (RPC) Library <../common>`.

.. note::
	It is not necessary to worry about thread synchronization within a Model, 
	it is all handled by :class:`common.Rpc.RpcServer`. 
	
Models were designed from the beginning to be network transparent. The
underlying RPC framework handles all of the function calls, regardless of the
actual location of the object on a network (even if it is on the local machine).
Because of this, there are limitations to the types of data that can be sent
across the network. All functions within a Model must return serializable data
for transport using `JSON-RPC`_. Serializable data types include:

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

If a function returns an object that is not serializable, the function name
must be prefixed with an underscore ('_'). This designates the function as a
protected function, and the RPC library will reject calls that function.
    
.. _JSON-RPC: http://www.jsonrpc.org/specification
    
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
	
Properties are retrieved by calling :func:`getProperties` from the Model. Models 
should override :func:`getProperties` and add additional properties that
may be useful for application and script development, like the ones above.

The following keys will always exist for all Models:

+---------------+-------------------------------------------------+
| Key           | Description                                     |
+---------------+-------------------------------------------------+
| 'uuid'        | Resource UUID                                   |
+---------------+-------------------------------------------------+
| 'controller'  | The module name for the controller              |
+---------------+-------------------------------------------------+
| 'resourceID'  | Resource ID specific for the controller         |
+---------------+-------------------------------------------------+
| 'vendorID'    | Vendor ID used to find compatible Models        |
+---------------+-------------------------------------------------+
| 'productID'   | Product ID used to find compatible Models       |
+---------------+-------------------------------------------------+
| 'modelName'   | The module name for the currently loaded model  |
+---------------+-------------------------------------------------+
| 'port'        | RPC port                                        |
+---------------+-------------------------------------------------+

The following keys will always exist, but will assume default values if they
are not set. They are used to identify devices for scripting: 

+-----------------+---------------+
| Key             | Default Value |
+-----------------+---------------+
| 'deviceType'    | 'Generic'     |
+-----------------+---------------+
| 'deviceVendor'  | 'Generic'     |
+-----------------+---------------+
| 'deviceModel'   | 'Device'      |
+-----------------+---------------+
| 'deviceSerial   | 'Unknown'     |
+-----------------+---------------+
| 'deviceFirmware'| 'Unknown'     |
+-----------------+---------------+

Example::

	def getProperties(self):
	
		prop['deviceVendor'] = 'my vendor'
		prop['deviceModel'] = 'ABC 12345'
		prop['deviceSerial'] = '0123456789'
		prop['deviceFirmware'] = '1.0'
		prop['deviceType'] = 'Widget'
		
		return prop
        
Model Inheritance
-----------------

Inheritance is good code practice and extremely useful when multiple devices
have only small differences. It reduces risk for bugs by encouraging code reuse
and consolidation.

.. note::

	See `Python Inheritance`_ for more information

.. _Python Inheritance: https://docs.python.org/2/tutorial/classes.html#inheritance

Someday, this section will have examples.
        
Model Template
--------------

.. literalinclude:: m_Template.py

Recommended API Implementations
-------------------------------

.. autoclass:: models.m_Base
   :members: _onLoad, _onUnload, getProperties