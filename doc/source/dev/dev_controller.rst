Controllers
===========

Controllers are responsible for low-level communication between devices (models)
and system drivers. 

Types of Controllers
--------------------

* Automatic - These controllers can find resources on their own without any 
  additional knowledge. This is typically achieved with a system driver that is
  "plug-'n-play" capable and enumerates devices on insertion.
  
* Manual - These controllers must have additional knowledge to discover a 
  resource. An example of a manual controller is a TCP/IP device. Not all 
  devices will respond to a multi-cast packet, so the user must supply an IP 
  address to find the device.
  
* Hybrid - These controllers can discover resources, but without additional
  information, they will not be able to match a model driver to the
  resource. A serial port controller is an example of this, as the system
  maintains a list of available COM ports, but the user must supply the
  baud rate, stop bits and parity information for the controller to be able
  to establish communication. 
  
Controller Template
-------------------

.. literalinclude:: c_Template.py

Required API Implementations
----------------------------

.. autoclass:: controllers.c_Base
   :members: open, close, getResources, canEditResources

Optional API Implementations
----------------------------

.. autoclass:: controllers.c_Base
   :members: addResource, destroyResource, refresh