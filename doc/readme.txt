Contributing to Documentation
=============================

Documentation is generated using Sphinx. Source files should
be added to doc/source. Invoke the Sphinx build script by calling:

doc/make html

The make.bat file simulates using Make on windows. You can also use:

doc/make clean 

to clean up existing documents and force a rebuild. The build script will
automatically compile the documentation and bundle it for distribution.

Using Documenation
==================

Open doc/build/html/index.html