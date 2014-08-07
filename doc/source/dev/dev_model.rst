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
    
Execution Model
---------------

When a Model is loaded, all of its data and attributes are stored in the same
process as InstrumentManager. If no errors are raised during Model instantiation,
an RPC Server thread is spawned for that Model by calling :func:`rpc_start`.
This function is inherited from :class:`common.Rpc.RpcBase`, which is inherited
from :class:`models.m_Base`. For information about the execution model of the
RPC server, see :doc:`Remote Procedure Call (RPC) Library <common>`.

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
	 
:func:`models.m_Base.getProperties` returns a default set of properties:

	* 'uuid': Resource UUID
	* 'controller': The module name for the controller
	* 'id': Resource ID specific for the controller
	* 'driver': The module name for the currently loaded model, None if not loaded
	* 'port': RPC Server port
    
There are also some recommended properties:

    * 'deviceVendor': The device vendor
    * 'deviceModel': The device model number
    * 'deviceSerial': The device serial number
    * 'deviceFirmware': The device firmware revision
    * 'deviceType': The device type from the model
    
Models should override :func:`getProperties` and add additional properties that
may be useful for application and script development. In order to prevent errors
in scripts that expect some or all of the default parameters, the Model should
get the default parameters and append to the returned dict::

	def getProperties(self):
	
        prop = models.m_Base.getProperties(self)
	
		prop['deviceVendor'] = 'my vendor'
		prop['deviceModel'] = 'ABC 12345'
		prop['deviceSerial'] = '0123456789'
		prop['deviceFirmware'] = '1.0'
		prop['deviceType'] = 'Widget'
		
		return prop
	
.. warning::

	Not returning a properties dict with the required keys may cause problems
	with scripts or applications that expect those keys. It is highly
	recommended, though not currently enforced.
        
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
-------------------

.. literalinclude:: m_Template.py

Recommended API Implementations
----------------------------

.. autoclass:: models.m_Base
   :members: _onLoad, _onUnload