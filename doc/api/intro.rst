Introduction
============

Labtronyx was built in Python to take advantage of the powerful capabilities
and rapid development 

Importing InstrumentControl
---------------------------

To use the InstrumentControl API::
   
   import labtronyx
   instr = labtronyx.InstrumentControl()

Connect to a Host
-----------------

On instantiation, InstrumentControl will attempt to connect to a local
InstrumentManager instance. Connections to InstrumentManager instances on remote
machines can be added or removed using :func:`InstrumentControl.addManager` and
:func:`InstrumentControl.removeManager`, respectively. 

When an InstrumentManager is added using :func:`InstrumentControl.addManager`,
all of the remote resources are cached by an internal call to 
:func:`InstrumentControl.refreshManager`. Cached resources are indexed by their
Unique Resource Identifier (UUID). 

If an :class:`InstrumentManager` instance is not already running, you can start
one using :func:`startWaitManager` or :func:`startManager`::

	instr.startWaitManager()
	
By default, InstrumentControl will attempt to connect to a local instance of
InstrumentManager. To connect to an InstrumentManager instance on another host::

	instr.addManager('192.168.0.1')
	
InstrumentControl can also resolve hostnames::

	instr.addManager('kkennedy')
	
Connecting to Instruments
-------------------------

InstrumentControl can connect to any Instrument on any machine that has been
added using :func:`InstrumentControl.addManager`. You can find instruments by:

	* Type
	* Model Number
	* Serial Number
	
Looking up instruments by Type and Model Number may return multiple instruments
if there are many devices connected. In these cases, InstrumentControl will
return a list of devices that match. The programmer will have to use other
logic to determine which device to use. The easiest way to deal with this
situation is to identify a device by serial number, though there is always the
possibility that devices from different vendors could have the same serial
number.

To connect to instruments by type::

	scope = instr.getInstrument_type('Oscilloscope')

To connect to instruments by Model number::

	smu = instr.getInstrument_model('B2902A')
	
To connect to instruments by Serial number::

	dev = instr.getInstrument_serial('12345')
	
To get a list of all instruments::

	all = instr.getInstrument_list()

Using Instruments
-----------------

Instruments can be used like any Python object, with some limitations. Under
the hood, Instruments are an RPC-endpoint connected to a socket on the
InstrumentManager. While this whole process should be mostly transparent to
both the user and the developer, some things are limited:

	* Only methods can be called, it is not possible to access object attributes
	* Accessing or Modifying attributes can only be done by wrapping the attribute in a set of methods (getters and setters) 
	* Methods that begin with '_' are considered protected and cannot be accessed
	* The RPC subsystem introduces 2-20 milliseconds of latency

see :doc:`Driver APIs <drivers/index>` for further documentation on each 
driver.

Loading and Unloading Drivers
-----------------------------

Drivers are code modules that contain the information needed to communicate
with a specific instrument. Labtronyx will try to automatically identify a
suitable driver to load, but it is sometimes necessary to load a specific
driver.

To load a driver for an instrument, you must know the UUID of the instrument.
The UUID can be retrieved if you know the Resource Identifier (Resource ID) of
the instrument. The Resource ID is related to how the instrument is connected
to the computer. e.g. COM5 (Serial), ASRL::5 (VISA)::

	instrument = instr.getInstrument(address='localhost', resID='ASRL::9')
	
	instrument.loadDriver('Tektronix.Oscilloscope.m_DigitalPhosphor')
	
To unload a driver::

	instrument.unloadModel()

API Documentation
-----------------

The InstrumentControl object is the primary interface to communicating with
instruments. It simplifies script development by abstracting local and remote 
instruments as simple Python objects.

.. autoclass:: labtronyx.InstrumentControl.InstrumentControl
   :members: