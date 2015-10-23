InstrumentManager
=================

The InstrumentManager object is the primary interface to communicating with instruments. It simplifies script
development by abstracting instruments as Python objects.


.. autoclass:: labtronyx.InstrumentManager
   :members:

RemoteManager
=============

The API for the RemoteManager is exactly the same as :class:`labtronyx.InstrumentManager`, though the initialization
of a Remote Manager requires a few additional parameters. Any function call that is executed on a RemoteManager object
is actually executed on the remote computer.

.. autoclass:: labtronyx.RemoteManager