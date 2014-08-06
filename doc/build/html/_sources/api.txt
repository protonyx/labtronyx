InstrumentControl API
=====================

The InstrumentControl API is the core of the Application GUI. It simplifies 
script development by abstracting local and remote instruments as simple Python 
objects and providing helper functions to handle all of the low-level 
communication with :class:`InstrumentManager` instances.

Using InstrumentControl
-----------------------

To use the InstrumentControl API::
   
   from InstrumentControl import InstrumentControl
   instr = InstrumentControl()
   
.. note::

	To import InstrumentControl, the folder must be in your PYTHONPATH
	
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
	
InstrumentControl can connect to any instrument on any machine that has been
added using :func:`InstrumentControl.addManager`. You can find instruments by:

	* Type
	* Model Number
	* Serial Number
	
Looking up instruments by Type and Model Number may return multiple instruments
if there are many devices connected. In these cases, InstrumentControl will
return a list of devices that match. The programmer will have to use other
logic to determine which device to use. The easiest way to deal with this
situation is to identify a device by serial number.

To connect to instruments by type::

	scope = instr.getInstrument_type('Oscilloscope')

To connect to instruments by Model number::

	smu = instr.getInstrument_model('B2902A')
	
To connect to instruments by Serial number::

	dev = instr.getInstrument_serial('12345')
	
Dependencies
------------

There are no dependencies.

Theory of Operation
-------------------

Some introductory text

Managing Connections to InstrumentManager instances
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Useful text

Cached Resources
^^^^^^^^^^^^^^^^

More useful text

Instruments
^^^^^^^^^^^

Some Text
	
API Usage
---------

.. autoclass:: InstrumentControl.InstrumentControl
   :members: