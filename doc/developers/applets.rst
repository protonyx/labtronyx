Applets
=======

Applets allows a seperation of visual code from instrument control code. 


Applets draw the graphical user interface (GUI) and handle callbacks from GUI 
elements when the user interacts with them. Applets communicate with a model 
using the :mod:`common.Rpc` library to change the physical device state or to 
retrieve data. Views are the primary interface point for an operator. The 
purpose of views is to separate the GUI elements from the application logic.

.. note::

	Applets are not used in any of the API functions, they can only be launched in 
	Application mode. The Application GUI will index the `applets` folder and 
	make them available.
	
Widgets
-------

Widgets are pre-built interface elements to perform common actions. A collection
of widget are provided to make building views much easier. Widgets are
instantiated

Notifications
-------------

Event notifications can be enabled to avoid polling in applets. They are enabled
using by calling `common.rpc.RpcClient._enableNotifications`

Using Collectors
----------------

In some applications, it may be beneficial to collect data at a regular and
precise intervals. Collectors serve this purpose by running at regular 
intervals.

.. note::

   Make sure to take into account the amount of time it takes to retrieve data
   from a physical device. This will depend on the interface used, the data
   transfer rate, operating system overhead and the process priority. This will 
   limit how quickly you will be able to collect data.
   
To start a collector, you must tell the driver which function you would like to
call, how often you would like to call it and how to interpret the returned
data. This is done by calling `startCollector` on the Instrument
object.

.. autoclass:: labtronyx.Base_Driver.Base_Driver
   :members: startCollector

Example::

	dev = instr.getInstrument_list()[0]
	
	dev.startCollector('getMeasurement', 100, lambda x: print x)
	
To stop a collector, notify the Model by calling `stopCollector` with the
name of the method.

Example::

	dev.stopCollector('getMeasurement')
	
To change the interval time, call the `startCollector` method with the new
interval. Only one collector can be running at a time for each method, so the
old collector will be destroyed and a new one will be created.
