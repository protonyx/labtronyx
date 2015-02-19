InstrumentManager Developer Guide
==================================

This section of the documentation is dedicated to providing the necessary 
resources for developers to expand the capabilities of this framework to new
lab instruments and protocols.

Contents
--------

.. toctree::
   :maxdepth: 2
   
   dev_manager
   dev_controller
   dev_model
   dev_view
   dev_test

Coding Conventions
------------------

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
	
