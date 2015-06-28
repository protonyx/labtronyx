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

The InstrumentManager class uses a slightly modified `Presentation-Abstraction-Control`_ 
architectural pattern, which separates the low-level system calls for 
communication from the instrument drivers. By using this design approach, core 
program functionality is isolated into smaller chunks in order to keep errors 
from propagating throughout the entire program.

.. _Presentation-Abstraction-Control: http://en.wikipedia.org/wiki/Presentation%E2%80%93abstraction%E2%80%93control

On startup, the InstrumentManager will scan the program directory for valid
interfaces. For each interface that is found, a scan will be initiated and the
found resources indexed. Once all resources are indexed, InstrumentManager
attempts to load drivers for each of them automatically. If a suitable driver
cannot be found, the user must specify which driver to load. 