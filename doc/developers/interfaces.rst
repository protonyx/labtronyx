Interfaces
==========

Interfaces handle low-level operating system interactions. This may include 
calls to hardware via driver stacks, or calls to other Python libraries.

.. note::
	VISA, Serial (RS-232), USB are examples of controllers
  
Interface Template
------------------

.. literalinclude:: templates/tp_interface.py

Required API Implementations
----------------------------

.. autoclass:: labtronyx.Base_Interface.Base_Interface
   :members: open, close, getResources

Optional API Implementations
----------------------------

.. autoclass:: labtronyx.Base_Interface.Base_Interface
   :members: refresh
   
