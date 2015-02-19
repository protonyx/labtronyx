Managing Models and Instruments
===============================

.. image:: media/instruments.png
   :scale: 50%

Instruments are Python objects that are linked to physical devices on a local
or remote machine. Many different machines may connect to the same physical
device because all communication is arbitrated by the InstrumentManager
running on the computer where the physical device is connected. 

All of the attributes and methods contained in an Instrument object are copied 
from the a Model object on the machine where the device is connected. In order
to connect to an Instrument, a Model must first be loaded.

Loading and Unloading Models
----------------------------

Models are typically handled automatically by the InstrumentManager. There are
a few cases, however, when you would need to manually load or unload a Model.
These cases are:

	* Multiple compatible Models exist, and the autoloader picked the wrong Model
	* The Controller does not support enumeration or autoloading Models
	* The Controller Resource was created manually
	* The Model you wish to load is not considered compatible (experimental code, etc.)

To load a Model for a resource, you must get the UUID of the resource and then
unload any existing Model::

	instr = InstrumentControl()
	
	uuid = instr.findResource('localhost', 'ASRL::9')[0]
	
	instr.unloadModel(uuid)
	
Then specify a package name and class name::

	instr.loadModel(uuid, 'models.Tektronix.Oscilloscope.m_DigitalPhosphor', 'm_DigitalPhosphor')
	
For more details, see :func:`InstrumentControl.unloadModel` and 
:func:`InstrumentControl.loadModel`

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

see :doc:`Supported Instruments <supported_instruments>` for further
documentation on each instrument.

Using Collectors
----------------

In some applications, it may be beneficial to collect data at a regular and
precise intervals. Collectors serve this purpose by running regularly within
the InstrumentManager to prevent network latency from skewing data samples.

.. note::

   Make sure to take into account the amount of time it takes to retrieve data
   from a physical device. This will depend on the interface used, the data
   transfer rate, operating system overhead and the process priority. This will 
   limit how quickly you will be able to collect data.
   
To start a collector, you must tell the Model which function you would like to
call, how often you would like to call it and how to interpret the returned
data. This is done by calling :function:`startCollector` on the Instrument
object.

.. autoclass:: models.m_Base
   :members: startCollector

Example::

	instr = InstrumentControl()
	
	dev = instr.getInstrument_list()[0]
	
	dev.startCollector('getMeasurement', 100, lambda x: print x)
	
To stop a collector, notify the Model by calling `stopCollector` with the
name of the method.

Example::

	dev.stopCollector('getMeasurement')
	
To change the interval time, call the `startCollector` method with the new
interval. Only one collector can be running at a time for each method, so the
old collector will be destroyed and a new one will be created.

Retrieving data from collectors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


