Introduction
============

This developer guide details all of the plugin types in the Labtronyx framework, their function and basic requirements.
Developers are encouraged to read the Architecture section to gain an understanding of how the framework is structured
before developing any plugins.

Version Control
---------------

The Labtronyx project is hosted on `GitHub <https://github.com/protonyx/labtronyx>`_.

Contributing
------------

This project is a work in progress. Due to the nature of lab instruments, drivers must be developed to fully utilize
the features unique to each device. Therefore, this framework cannot possibly hope to have a comprehensive collection
of drivers for every device on the market. This documentation includes everything a developer would need to write
drivers for new interfaces, devices and instruments.

Developers wishing to contribute to the project can fork the project on GitHub and create pull requests.

Reporting Bugs
--------------

All bugs should be reported to the `GitHub issue tracker <https://github.com/protonyx/labtronyx/issues>`_.

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

The InstrumentManager class uses a slightly modified `Presentation-Abstraction-Control`_ architectural pattern, which
separates the low-level system calls from the high-level command set of each device. By using this design approach,
there is a clear separation of concerns that allows the framework to be highly modular.

.. _Presentation-Abstraction-Control: http://en.wikipedia.org/wiki/Presentation%E2%80%93abstraction%E2%80%93control

The core of the framework is the :class:`InstrumentManager` class, which is responsible for scanning all provided
directories for compatible plugins. Each Interface plugin found will be instantiated, which in turn will query the
system for any available resources.