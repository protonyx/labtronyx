Instrument Manager Developer Guide
==================================

This section of the documentation is dedicated to providing the necessary 
resources for developers to expand the capabilities of this framework to new
lab instruments and protocols.

Architecture
------------

The InstrumentManager class uses a model-view-controller design paradigm, which
seperates the low-level system calls from the instrument drivers. By using this
design approach, core program functionality is isolated into smaller chunks in
order to keep errors from propagating throughout the entire program. If an
exception is raised in a Controller or Model, it can be caught easily before
the entire framework is destabilized.

Contents
--------

.. toctree::
   :maxdepth: 2
   
   conventions
   dev_controller
   dev_model
