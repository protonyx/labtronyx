Instrument Manager Developer Guide
==================================

This section of the documentation is dedicated to providing the necessary 
resources for developers to expand the capabilities of this framework to new
lab instruments and protocols.

Coding Conventions
------------------

See Python PEP-8

Architecture
------------

The InstrumentManager class uses a model-view-controller design paradigm, which
seperates the low-level system calls from the instrument drivers. By using this
design approach, core program functionality is isolated into smaller chunks in
order to keep errors from propagating throughout the entire program. If an
exception is raised in a Controller or Model, it can be caught easily before
the entire framework is destabilized.

Controllers
-----------

Controllers are responsible for low-level communication between devices (models)
and system drivers. 

Models
------

Models are responsible for high-level communication with devices. They should
not make system driver calls. Models can send and recieve commands from the
device using a controller, but the physical communication protocol is
transparent to the model. For instruments that use the same command set but are
capable of communicating over a variety of protocols (Serial, Ethernet, CAN,
etc.), the same model can be used without needing knowledge of the underlying
controller.

Views
-----

Views allows a seperation of visual code from instrument control code. While the
InstrumentControl API has no visual component, the Smart Lab GUI will index
the `views` folder and make them available from the application.
