Getting Started
===============

Introduction
------------

The primary use case for Labtronyx is as a Python library. This way, it can be imported into an existing script,
framework or application to enable automation with ease. Once Labtronyx is installed, it can be imported and used as
a module::

   import labtronyx
   instr = labtronyx.InstrumentManager()

The Instrument Manager is the core of the Labtronyx framework. It connects to all of the compatible interfaces and
discovers connected instruments. The command :func:`findInstruments` can be used to return a list of connected
instruments.::

   dev_list = instr.findInstruments()

.. note::

   :func:`labtronyx.InstrumentManager.findInstruments` will always return a list of instrument objects, even if only one
   was found.

To find a specific instrument connected to a specific port, you can specify the resourceID parameter to pinpoint which
instrument you would like. This requires some knowledge of how the instrument is connected to the system::

   device = instr.findInstruments(resourceID='COM16')   # Serial
   device = instr.findInstruments(resourceID='ASRL::16') # VISA

Additional :class:`labtronyx.InstrumentManager` methods can be found here: :doc:`InstrumentManager API <api/manager>`.

Using Instruments
-----------------

Instruments are objects that allow you to control a physical device connected to the system. Instruments interact with
the physical device through a `Resource` object which is managed by an interface connector (such as VISA, Serial, USB,
etc). Before you can do anything with an instrument, it must be opened. Opening an instrument allows Labtronyx to
communicate with the physical device and also acquires a lock to prevent other software on your computer from
controlling this device as well.::

   device.open()

By default, instruments contain only a small set of methods to interact with a device
(see :doc:`Resource API <api/resources>`). These methods allow you to read and write to the device, but it has no
knowledge of the capabilities of the device or the commands required to interact with that particular device.::

   device.write('*IDN?')
   identity = device.read()

In order to access the full capabilities of a device, you must load a `Driver`. When a driver is loaded for an
instrument, additional methods are made available that may allow you to interact with the device without having to know
all of the commands a device supports. Some interfaces, such as VISA, support automatically loading a `Driver` by using
a discovery process supported by a majority of commercially available devices. For devices that do not support
discovery, you will need to load a driver manually.::

   device_list = instr.findInstruments(resourceID='ASRL::9')

   if len(device_list) > 0:
       instrument = device_list[0]

       instrument.loadDriver('drivers.BK_Precision.Load.m_85XX')

Similarly, to unload a driver::

   instrument.unloadDriver()

Once a driver is loaded, you can interact with the device using methods specific to that device. For documentation on
the supported instruments and available commands for those instruments, see :doc:`Supported Instruments <instruments>`.

Finding Instruments
-------------------

If a driver is loaded for a particular instrument, you may be able to find instruments based on device metadata:

   * Manufacturer
   * Device Type
   * Serial Number
   * Model Number

To find devices by Manufacturer::

   dev = instr.findInstruments(deviceVendor='Tektronix')

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

   * resourceID
   * interface
   * driver
   * deviceVendor
   * deviceModel
   * deviceSerial
   * deviceFirmware

Resources or drivers may specify additional properties that can be used to identify instruments. See the resource
or driver documentation for your instrument to find out what else may be available. See
:doc:`Supported Instruments <instruments>`.

Instrument Metadata (Properties)
--------------------------------

Instrument objects provide additional metadata about the physical device it is connected to. It could include
information such as:

   * Manufacturer
   * Model number(s)
   * Firmware Revision
   * Serial Numbers
   * Capabilities
   * Channels/Probes
   * etc.

This metadata is retrieved by calling :func:`getProperties` and returned as a dictionary. All instruments provide the
following keys, with additional keys optionally added by the driver:

+---------------+-------------------------------------------------+
| Key           | Description                                     |
+===============+=================================================+
| uuid          | Resource UUID                                   |
+---------------+-------------------------------------------------+
| fqn           | Fully Qualified Name of resource class          |
+---------------+-------------------------------------------------+
| interfaceName | The name of the associated interface            |
+---------------+-------------------------------------------------+
| resourceID    | Resource ID specific for that interface         |
+---------------+-------------------------------------------------+
| driver        | Driver name                                     |
+---------------+-------------------------------------------------+
| deviceType    | Device type                                     |
+---------------+-------------------------------------------------+
| deviceVendor  | Device vendor or manufacturer                   |
+---------------+-------------------------------------------------+
| deviceModel   | Device model number                             |
+---------------+-------------------------------------------------+
| deviceSerial  | Device serial number                            |
+---------------+-------------------------------------------------+
| deviceFirmware| Device firmware revision number                 |
+---------------+-------------------------------------------------+