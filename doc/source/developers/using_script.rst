Getting Started with the Programming Interface
==============================================

Importing InstrumentControl
---------------------------

To use the InstrumentControl API::
   
   from InstrumentControl import InstrumentControl
   instr = InstrumentControl()
   
.. note::

	To import InstrumentControl, the folder must be in your PYTHONPATH

Connecting to InstrumentManager instances
-----------------------------------------

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