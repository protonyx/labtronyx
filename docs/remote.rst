Remote Control
==============

Listening for Remote Connections
--------------------------------

The Labtronyx InstrumentManager runs locally by default. To run Labtronyx in server mode, run the console script::

   python labtronyx/cli.py

To start the server programmatically, use::

   import labtronyx
   
   manager = labtronyx.InstrumentManager()
   manager.rpc_start()

If Labtronyx was properly installed, it can be called from the command line::

   labtronyx

While in server mode, the terminal window will be unavailable for use, but all logging events will be displayed there.

Connect to a Remote InstrumentManager
-------------------------------------

Connections to remote InstrumentManager instances is done using the
:class:`RemoteManager` class::

   import labtronyx
   
   remote = labtronyx.RemoteManager(address='192.168.0.1')

Error Handling
--------------

All errors that occur using a Remote InstrumentManager are raised as RuntimeError objects.