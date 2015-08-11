Supported Interfaces
====================

Labtronyx uses a plugin architecture to allow for easy expansion and addition of interfaces on-the-fly. A set of
typical interfaces are bundled to support the vast majority of instruments. These documents will detail the capabilities
of each interface and the dependencies needed to run them. If an interface depends on external software, it will not
load and may not give any indications of the reason for the failure.

    | :doc:`VISA`
    | Serial, GPIB, Ethernet (VXI) and USB (Test and Measurement Devices)
    |
    | :doc:`Serial`
    | Serial

.. toctree::
   :hidden:

   VISA
   Serial