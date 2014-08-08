Views
=====

Views allows a seperation of visual code from instrument control code. 


Views draw the graphical user interface (GUI) and handle callbacks from GUI 
elements when the user interacts with them. Views communicate with a model 
using the :mod:`common.Rpc` library to change the physical device state or to 
retrieve data. Views are the primary interface point for an operator. The 
purpose of views is to separate the GUI elements from the application logic.

.. note::

	Views are not used in any of the API functions, they can only be launched in 
	Application mode. The Application GUI will index the `views` folder and 
	make them available. This is a feature that does not exist yet.