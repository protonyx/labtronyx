Remote Control
==============

Listening for Remote Connections
--------------------------------

The Labtronyx InstrumentManager runs locally by default. To run Labtronyx in server mode, run the console script::

   python labtronyx/cli.py

If Labtronyx was properly installed, it can be called from the command line::

   labtronyx

For both of these methods, the server will block input and the terminal window will be unavailable for use, but all
logging events will be displayed there. If you need to start the server in a new thread, it must be done in code::

   import labtronyx

   manager = labtronyx.InstrumentManager()
   manager.server_start()

Connect to a Remote InstrumentManager
-------------------------------------

Connections to remote InstrumentManager instances is done using the
:class:`RemoteManager` class::

   import labtronyx
   
   remote = labtronyx.RemoteManager(address='192.168.0.1')

Error Handling
--------------

Exceptions raised from a remote InstrumentManager are handled in the same way they would be handled locally. See
:doc:`api/exceptions` for more details on Labtronyx exception classes.

RemoteManager API
-----------------

The API for the RemoteManager is exactly the same as :class:`labtronyx.InstrumentManager`, though the initialization
of a Remote Manager requires a few additional parameters. Any function call that is executed on a RemoteManager object
is actually executed on the remote computer.

.. autoclass:: labtronyx.RemoteManager