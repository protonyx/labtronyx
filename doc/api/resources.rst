Interacting directly with Resources
===================================

If you need to send commands directly to the device, the resource API documents the available functions. This is necessary if the driver does not support a particular function or a driver does not exist for the device you are interacting with.

Common Resource API
-------------------

.. autoclass:: labtronyx.Base_Resource.Base_Resource
   :members:

VISA Resource API
-----------------

.. autoclass:: labtronyx.interfaces.i_VISA.r_VISA
   :members:

Serial Resource API
-------------------

.. autoclass:: labtronyx.interfaces.i_Serial.r_Serial
   :members:

UPEL ICP Resource API
---------------------

.. autoclass:: labtronyx.interfaces.i_UPEL.r_UPEL
   :members: