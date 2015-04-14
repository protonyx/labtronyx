Applets
=======

.. image:: media/applet_multimeter.png
   :width: 500px

Applets allows a seperation of visual code from instrument control code. 

Applets draw the graphical user interface (GUI) and handle callbacks from GUI 
elements when the user interacts with them. Applets communicate with a model 
using the :mod:`common.Rpc` library to change the physical device state or to 
retrieve data. Views are the primary interface point for an operator. The 
purpose of views is to separate the GUI elements from the application logic.

.. note::

	Applets can only be launched in Application mode. The Application GUI will 
	index the `applets` folder and make them available.

Notifications
-------------

Event notifications can be enabled to avoid polling in applets. They are enabled
using by calling `common.rpc.RpcClient._enableNotifications`

Collectors
----------

In some applications, it may be beneficial to collect data at a regular and
precise intervals. If network latency is a concern, a collector can be used to
reduce latency caused by the RPC subsystem. Collectors run in a dedicated thread 
on the machine hosting the instrument. 

To start a collector, you must tell the driver which function you would like to
call, how often you would like to call it and how to interpret the returned
data. This is done by calling `startCollector` on the Instrument
object. To change the interval time, call the :func:`startCollector` method with 
the new interval. Only one collector can be running at a time for each method, 
so the old collector will be destroyed and a new one will be created. Data is 
retreived from a collector using :func:`getCollector`.

To stop a collector, notify the Model by calling :func:`stopCollector` with the
name of the method.

Example::
	
	dev.startCollector('getMeasurement', 100, lambda x: print x)
	
	data = []
	last_time = time.time()
	
	while an_event.is_set():
		new_data = dev.getCollector('getMeasurement', last_time)
		for timestamp, sample in new_data:
            plot_attr['time'] = timestamp
            data.append(sample)

	dev.stopCollector('getMeasurement')

.. autoclass:: labtronyx.Base_Driver.Base_Driver
   :members: startCollector, getCollector, stopCollector

Widgets
-------

Widgets are pre-built interface elements to perform common actions. A collection
of widget are provided to make building applets much easier.