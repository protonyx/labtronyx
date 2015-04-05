Remote Control
==============

Listening for Remote Connections
--------------------------------

The Labtronyx Server runs locally by default. To listen for remote connections,
the server should be started by executing `Server.py` in a separate process,
or by calling:

   import labtronyx
   server = labtronyx.Server()
   server.start()

Connect to a Remote Server
--------------------------

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

API Documentation
-----------------

The RemoteManager object is the primary interface to communicating with
instruments on other computers. It simplifies script development by 
abstracting nstruments as simple Python objects.

.. autoclass:: labtronyx.RemoteManager.RemoteManager
   :members: