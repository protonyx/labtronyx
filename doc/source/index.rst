.. InstrumentControl documentation master file, created by
   sphinx-quickstart on Sat Jul 26 10:59:33 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Lab Instrument Control and Automation Framework
===============================================

The InstrumentControl project is a comprehensive solution for lab instrument 
control and automation. With an easy-to-use and fully documented API, 
InstrumentControl is all you need to develop robust scripts and applications 
to automate testing involving lab instruments. With this framework, you will 
no longer have to worry about interfaces and protocols. Instruments are 
abstracted as simple Python objects, no matter where they are on the network.

This project is a work in progress. Due to the nature of lab instruments, 
drivers must be developed to fully utilize the features unique to each 
instrument. Therefore, this framework cannot possibly hope to have a 
comprehensive list of drivers for every device on the market. This 
documentation includes everything a developer would need to write drivers for 
new instruments. Developers are encouraged to contribute their drivers to the 
project.


User Guide
==========

Learn how to use the graphical interface portion of InstrumentControl. 

.. toctree::
   :maxdepth: 2
   
   intro
   using_application
   tests
   
Supported Devices and Interfaces
================================

.. toctree::
   :maxdepth: 2
   
   supported_instruments
   supported_interfaces
   
Programmer Guide
================

In-depth guide to the scripting capabilities of InstrumentControl. Assumes an
intermediate understanding of programming in Python.

.. toctree::
   :maxdepth: 2

   using_script
   resources
   models
   tests
   api
   common
   
Developer Guide
===============

Guide to the inner workings of the InstrumentControl framework. Learn how to
create Models, Controllers, Views and Tests.

.. toctree::
   :maxdepth: 3
   
   dev/dev_index  

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

