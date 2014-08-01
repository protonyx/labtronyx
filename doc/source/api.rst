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
	
If an :class:`InstrumentManager` instance is not already running, you can start
one using :func:`startWaitManager` or :func:`startManager`::

	instr.startWaitManager()
	
.. note::

	To import InstrumentControl, the folder must be in your PYTHONPATH
	
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