InstrumentManager
=================

InstrumentManager is a self-contained class to interface with test instruments
on the local system. 

Only one instance of InstrumentManager can be running at a time. This is because
each InstrumentManager is attached to a fixed port to facilitate communication
between different hosts easily. Also, InstrumentManagers tend to lock system 
resources, so only one should be running at a time. 

If an attempt is made to start a second InstrumentManager instance, the 
initialization sequence will find that the socket is in use and will exit right 
away.

.. note::

	All interactions with InstrumentManager instances are handled by the
	InstrumentControl API. This documentation is mostly for reference and to
	aid development of instrument drivers.
	
Architecture
------------

The InstrumentManager class uses a slightly modified `Model-View-Controller`_ 
design paradigm, which separates the low-level system calls from the instrument 
drivers. By using this design approach, core program functionality is isolated 
into smaller chunks in order to keep errors from propagating throughout the 
entire program. If an exception is raised in a Controller or Model, it can be 
caught easily before the entire framework is destabilized.

.. _Model-View-Controller: http://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller

On startup, the InstrumentManager will scan the program directory for valid
controllers. For each controller that is found, a scan will be initiated and the
found resources indexed. Once all resources are indexed, InstrumentManager
attempts to load models for each of them based on the Vendor and Product
identifier returned from the controller. 

Resources
---------

The core function of the InstrumentManager is to manage resources that are
connected to that system. In general, a resource represents an instrument that
is connected to the local machine and is known to the operating system.

Internally, resources are stored using three pieces of information that make 
them uniquely identifiable and can be used to establish communication with the 
physical device:

	* Universally Unique IDentifier (str)
	* `Controller` name (str)
	* Resource Identifier (str)

Internal API
------------

Like models, an InstrumentManager can also be connected to with a
:class:`RpcClient` instance. The following functions are listed only for
reference, as the InstrumentControl API should be used to manage all 
communication with each InstrumentManager.

.. autoclass:: InstrumentManager.InstrumentManager
   :members:
