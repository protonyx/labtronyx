Introduction
============

Contributing
------------

This project is a work in progress. Due to the nature of lab instruments, 
drivers must be developed to fully utilize the features unique to each 
instrument. Therefore, this framework cannot possibly hope to have a 
comprehensive collection of drivers for every device on the market. This 
documentation includes everything a developer would need to write drivers for 
new instruments. 

Developers are encouraged to contribute their drivers to the project.

Style Guidelines
----------------

See Python :pep:`8`

See `Google Style Guide <https://google-styleguide.googlecode.com/svn/trunk/pyguide.html>`_

Exceptions to those documents are listed in the following sections.

Naming Variables, Functions and Classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Classes should be named using CamelCase with the first letter capitalized.

Functions should be named using camelCase with the first letter *not* capitalized.

Variables as class attributes should use camelCase, but variables within a
function do not have to follow any particular convention.

Constants should be ALL_CAPS with underscores for spaces

Doc Strings
^^^^^^^^^^^

This documentation is generated using `Sphinx <http://sphinx-doc.org/>`_. 
Prefer Sphinx-style doc-strings over the Google Style Guide.
	

Architecture
------------

The InstrumentManager class uses a slightly modified `Model-View-Controller`_ 
design paradigm, which separates the low-level system calls from the instrument 
drivers. By using this design approach, core program functionality is isolated 
into smaller chunks in order to keep errors from propagating throughout the 
entire program. If an exception is raised in a Controller or Model, it can be 
caught easily before the entire framework is destabilized.

.. _Model-View-Controller: http://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller

On startup, the InstrumentManager will scan the program directory for valid
controllers. For each controller that is found, a scan will be initiated and the
found resources indexed. Once all resources are indexed, InstrumentManager
attempts to load models for each of them based on the Vendor and Product
identifier returned from the controller. 