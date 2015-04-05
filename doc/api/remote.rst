Remote Control
==============

Listening for Remote Connections
--------------------------------

The Labtronyx InstrumentManager runs locally by default. To listen for remote 
connections, call::

   import labtronyx
   
   manager = labtronyx.InstrumentManager()
   manager.start()

Connect to a Remote InstrumentManager
-------------------------------------

Connections to remote InstrumentManager instances is done using the
:class:`RemoteManager` class::

   import labtronyx
   
   remote = labtronyx.RemoteManager(address='192.168.0.1')
   
Transmission of data is over UDP ports with JSON-RPC formatted data.

API Documentation
-----------------

The RemoteManager object is the primary interface to communicating with
instruments on other computers. It simplifies script development by wrapping
communication with a JSON-RPC server inside a Python object that can be used
as if the remote InstrumentManager object was a local Python object.

.. autoclass:: labtronyx.RemoteManager.RemoteManager
   :members: