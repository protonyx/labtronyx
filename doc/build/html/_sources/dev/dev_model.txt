Models
======

Models are responsible for high-level communication with devices. They should
not make system driver calls. Models can send and recieve commands from the
device using a controller, but the physical communication protocol is
transparent to the model. For instruments that use the same command set but are
capable of communicating over a variety of protocols (Serial, Ethernet, CAN,
etc.), the same model can be used without needing knowledge of the underlying
controller.