Developing Scripts
==================

Script Framework
----------------

Tests are a collection of scripts to test the functionality of a 
device-under-test (DUT). They can be used as unit/regression tests for Models
under development, or they can automate functional testing of a physical device.

Programmatically, tests are Python objects that inherit the Test Base class
contained in :class:`tests.t_Base.t_Base`. Any class that inherits the Test
Base class will launch a Tkinter dialog when instantiated. From this dialog,
individual test functions can be run

.. autoclass:: labtronyx.Base_Script.Base_Script
   :members: