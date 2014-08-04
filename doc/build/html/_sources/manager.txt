InstrumentManager
=================

InstrumentManager is a self-contained class to interface with test instruments
on the local system. Only one instance of InstrumentManager can be running at a
time on a given machine, since it will keep a socket open on a fixed port. 

Resources
---------

The core function of the InstrumentManager is to manage resources that are
connected to that system. In general, a resource represents an instrument that
is connected to the local machine and is known to the operating system.

Internally, resources are stored using three pieces of information that make 
them uniquely identifiable and can be used to establish communication with the 
physical device:

	* UUID (Universally Unique IDentifier)
	* `Controller` name
	* String identifier



Theory of Operation
-------------------

Test

Controllers
^^^^^^^^^^^

test



Models
^^^^^^

test

Each model has a `properties` attribute where information about each physical
device is stored. It is formatted as a dictionary and contains (among other
things):

	* Vendor (deviceVendor)
	* Serial Number (deviceSerial)
	* Model Number (deviceModel)
	* Firmware Revision (deviceFirmware)
	* Device Type (deviceType)

The parenthesized strings above are the keys for these standard values in the
property dictionary. There can exist any number of properties in this dictionary,
and there is no standard yet for how they should be named (aside from these 
five). To ease script development in the future, there may be a standardization
of property keys that depends on the type of each device.

Internal API
------------

Like models, an InstrumentManager can also be connected to with a
:class:`RpcClient` instance. The following functions are listed only for
reference, as the InstrumentControl API should be used to manage all 
communication with each InstrumentManager.

.. autoclass:: InstrumentManager.InstrumentManager
   :members: