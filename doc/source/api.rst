InstrumentControl API
=====================

The InstrumentControl API is the core of the Application GUI. It simplifies script development by abstracting local and remote instruments as simple Python objects and providing helper functions to handle all of the low-level communication with InstrumentManagers

The InstrumentControl API can be imported from an existing install of the Application GUI or using the slim installer that integrates the necessary files directly into your local Python installation.

To use the InstrumentControl API::

	import InstrumentControl
	
	ic = InstrumentControl.InstrumentControl()
	
.. note::

	To import InstrumentControl from an Application GUI install, the folder must be in your PYTHONPATH
	
.. autoclass:: InstrumentControl.InstrumentControl
   :members: