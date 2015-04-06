Resources
=========

Resources are objects that represent a physical device connected to the system.

If you need to send commands directly to the device, the resource API documents 
the available functions. This is necessary if the driver does not support a 
particular function or a driver does not exist for the device you are 
interacting with.

Resource Types
--------------

   - :class:`labtronyx.interfaces.i_VISA.r_VISA`
   - :class:`labtronyx.interfaces.i_Serial.r_Serial`
   - :class:`labtronyx.interfaces.i_UPEL.r_UPEL`

Manually Managing Resources
---------------------------

.. note::

   This is an experimental feature and has not been well tested, since there
   are no devices currently that would need this support. Its possible it won't
   work at all. This section should give you an idea of how it will work...
   someday.

The ability to manage resources is dependent on the nature of a controller.
Most controllers accessed a fixed set of system resources that are known.
A serial controller is an example of this, as the system only allows connection
to a known COM port and provides a list of available ports. Some controllers
may not always be aware of available resources. For example, if a controller
interfaces with a CAN bus, it may need additional information like a device
address in order to establish communication. It is not always practical to scan
through the entirety of possible device addresses to find a device.

For controllers that support manually adding resources::

	from InstrumentControl import InstrumentControl
   	instr = InstrumentControl()
   	
   	new_uuid = instr.addResource('c_CAN', 'ACME', 'ABC 2000')
   	
   	# Refresh the resources list to find the new resource
   	instr.refreshManager()
   	
   	widget = instr.getInstrument_model('ABC 2000')
   	
To destroy a resource, provide the Resource UUID::

	instr.destroyResource('c_CAN', '360ba14f-19be-11e4-95bf-a0481c94faff')
   
Resource APIs
-------------

.. autoclass:: labtronyx.interfaces.i_VISA.r_VISA
   :members:

.. autoclass:: labtronyx.interfaces.i_Serial.r_Serial
   :members:

.. autoclass:: labtronyx.interfaces.i_UPEL.r_UPEL
   :members: