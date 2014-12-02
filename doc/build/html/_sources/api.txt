InstrumentControl API
=====================

The InstrumentControl API is the core of the Application GUI. It simplifies 
script development by abstracting local and remote instruments as simple Python 
objects and providing helper functions to handle all of the low-level 
communication with :class:`InstrumentManager` instances.

The InstrumentControl object is essentially a wrapper for InstrumentManager,
but simplifies the API by managing the communication to InstrumentManager
instances on multiple machines. All of the resources from all of the connected
InstrumentManager instances are cached locally and can be accessed using the
API as if they were all local objects.

.. autoclass:: InstrumentControl.InstrumentControl
   :members: