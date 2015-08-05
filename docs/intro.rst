Getting Started
===============

This guide assumes a basic understanding of Python. It will guide the user 
through the steps needed to connect to and control instruments.

Creating an Instrument Manager
------------------------------

The Instrument Manager is the core of the Labtronyx framework. It connects to
all of the compatible interfaces and discovers connected instruments. To load
the Instrument Manager::
   
   import labtronyx
   instr = labtronyx.InstrumentManager()

Connecting to Instruments
-------------------------

The command :func:`findInstruments` can be used to return a list of instruments. This will search all resources
connected to the system for valid instruments::

   dev_list = instr.findInstruments()
   
Labtronyx may be able to discover additional information about resources that will help identify a specific instrument
connected to the system. This requires that the instrument has some means to identify itself (like the VISA *IDN?
command) and a compatible Labtronyx driver for that instrument. For instruments with this capability, you can use
the parameters to target specific instruments.

To connect to instruments by type::

   scope = instr.findInstruments(deviceType='Oscilloscope')

To connect to instruments by Model number::

   smu = instr.findInstruments(deviceModel='B2902A')

To connect to instruments by Serial number::

   dev = instr.findInstruments(deviceSerial='12345')

Multiple search criteria can also be used to pinpoint a specific instrument if there are many instruments present on
the system::

   dev = instr.findInstruments(deviceType='Oscilloscope', deviceSerial='12345')

Other parameters you can use to identify devices:

   * deviceVendor
   * deviceModel
   * deviceSerial
   * deviceFirmware

Interfaces or drivers may specify additional parameters that can be used to identify instruments. See the driver
documentation for your instrument to find out what else may be available.

If the instrument does not have any means to identify itself, you must find the instrument using information about how
the resource is connected to the system, such as:

   * Interface (VISA, Serial, etc.)
   * Location (COM Port, IP Address, etc.)

To connect to instruments by resource ID (interface dependent)::

   device = instr.findInstruments(resourceID='COM16')   # Serial
   device = instr.findInstruments(resourceID='ASRL::9') # VISA

Note::

   `findInstruments` will always return a list of instrument objects, even if only one was found.

Loading and Unloading Drivers
-----------------------------

Drivers are code modules that contain the commands needed to communicate with a specific instrument. Labtronyx will
try to automatically identify a suitable driver to load, but it is sometimes necessary to load a specific driver.

To load a driver for an instrument, call the :func:`loadDriver` method of the resource where the instrument is
connected.::

   device_list = instr.findInstruments(address='localhost', resourceID='ASRL::9')

   if len(device_list) > 0:
       instrument = device_list[0]
	
       instrument.loadDriver('drivers.BK_Precision.Load.m_85XX')
	
Similarly, to unload a driver::

   instrument.unloadModel()

Using Instruments
-----------------

When a driver is loaded for an instrument, additional methods are made available. For documentation on the available
methods, see :doc:`Supported Instruments <instruments/index>` for the desired driver. It is also possible to send
commands directly to the instrument using the :doc:`Resource API <api/resources>` for the interface where the instrument
is connected.

	
