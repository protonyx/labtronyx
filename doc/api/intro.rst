Getting Started
===============

This guide assumes a basic understanding of Python. It will guide the user 
through the steps needed to connect to and control instruments.

Creating an Instrument Manager
------------------------------

The Instrument Manager is the core of the labtronyx framework. It connects to
all of the compatible interfaces and discovers connected instruments. To load
the Instrument Manager, use the following code::
   
   import labtronyx
   instr = labtronyx.InstrumentManager()

Connecting to Instruments
-------------------------

In order to connect to an instrument, you must know something about how it is
connected. You may need information such as:

   * Interface (VISA, Serial, etc.)
   * Location (COM Port, IP Address, etc.)
   
Some interfaces support automatic enumeration and can detect other attributes
about the instrument such as:

	* Type
	* Vendor
	* Model Number
	* Serial Number

Without Enumeration
^^^^^^^^^^^^^^^^^^^

The command :func:`findInstruments` can be used to return a list of all
instruments::

   dev_list = instr.findInstruments()
   
It can also be used to identify a specific instrument with additional
information::

   device = instr.findInstruments(resourceID='COM16')

With Enumeration
^^^^^^^^^^^^^^^^

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




	
