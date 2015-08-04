Drivers
=======

Drivers are responsible for high-level communication with devices. Drivers send 
and receive commands from the physical device using a controller. In order to
maintain functional abstraction, Drivers should limit dependencies on outside
libraries and avoid making system driver calls. All code contained in Drivers 
should deal with the specific instrument's command set. 

By design, drivers should be portable across all of the instruments supported
interfaces with a single code base. By so doing, the same driver can be used 
regardless of the underlying interface that is being used.

All Drivers extend :class:`Base_Driver`.
    
Execution Model
---------------

Driver objects are stored in the same process and memory space as it's 
associated resource. Driver methods are accessed through the resource object,
as if the resource object were a subclass of the driver.

Remote Procedure Call (RPC)
---------------------------

Drivers methods can be executed through the resource RPC instance. Thus, it is
important to follow the same recommendations for return values as resources.

See :doc:`resources`
    
Properties
----------

Drivers can provide auxiliary information about a physical device in the
properties. Properties can be useful for application and script development
by enabling or disabling features according to data contained in the properties.

All drivers should provide the minimum properties to ensure a device can be
found by an application or script:

+-----------------+---------------+-------------------------------------+
| Key             | Default Value | Examples                            |
+-----------------+---------------+-------------------------------------+
| 'deviceType'    | 'Generic'     | 'Multimeter', 'Oscilloscope'        |
+-----------------+---------------+-------------------------------------+
| 'deviceVendor'  | 'Generic'     | 'Tektronix', 'Agilent Technologies' |
+-----------------+---------------+-------------------------------------+
| 'deviceModel'   | 'Device'      | 'DPO2024', '2831E'                  |
+-----------------+---------------+-------------------------------------+
| 'deviceSerial   | 'Unknown'     | '12345'                             |
+-----------------+---------------+-------------------------------------+
| 'deviceFirmware'| 'Unknown'     | '1.0.0'                             |
+-----------------+---------------+-------------------------------------+

Serial number and firmware information should be retrieved from the device.

Example::

	def getProperties(self):
	
		prop['deviceVendor'] = 'my vendor'
		prop['deviceModel'] = 'ABC 12345'
		prop['deviceSerial'] = '0123456789'
		prop['deviceFirmware'] = '1.0'
		prop['deviceType'] = 'Widget'
		
		return prop
        
Driver Inheritance
------------------

Inheritance promotes code reuse and extremely useful when multiple devices
have only small differences. It reduces risk for bugs by encouraging code reuse
and consolidation.

.. note::

	See `Python Inheritance`_ for more information

.. _Python Inheritance: https://docs.python.org/2/tutorial/classes.html#inheritance
        
Driver Template
---------------

.. literalinclude:: templates/tp_driver.py

Base Driver API
---------------

.. autoclass:: labtronyx.bases.Base_Driver
   :members: _onLoad, _onUnload, getProperties