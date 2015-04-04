Installation
============

Windows
-------

Installing Python
^^^^^^^^^^^^^^^^^

1. Download the latest version of Python 2.7 from the
`official Python website <http://python.org>`_ . The Python installer for
Windows is an MSI package. 

2. To run the installer, double-click on the downloaded file.

3. Check the option for `Install for all users` and click `Next`.

.. image:: media/install_win_step1.png

4. Select a destination directory to install Python. The default location at 
`C:\\Python27\\` is sufficient. Click `Next`.

5. Install all features by clicking on the icon next to **Python** and selecting
**Entire feature will be installed on the local hard drive**. Click `Next`.

.. image:: media/install_win_step2.png

6. Wait while the installer finished. You may be prompted by Windows UAC to
allow the installer Administrator access. Click `Yes` to this prompt.

Additional instructions and help can be found at http://python.org

Installing Labtronyx
^^^^^^^^^^^^^^^^^^^^

For Windows computers, Labtronyx is installed by running the setup file.

TODO: Add more instructions here

Mac OSX
-------

Instructions to be added later

Ubuntu Linux
------------

Instructions to be added later

Installing Labtronyx
^^^^^^^^^^^^^^^^^^^^

For all other operating systems, Labtronyx is installed using Python setuptools:

1. Open a terminal window and browse to the location of the zip archive.

2. Take note of the filename of the zip archive

3. Execute the following commands

.. code-block:: console

   unzip <filename of zip archive>
   python setup.py install

Installing Dependencies
-----------------------

NI-VISA
^^^^^^^

The latest version of NI-VISA can be downloaded at 
`www.ni.com/visa <http://www.ni.com/visa>`_ . At the time of writing, the latest
version of NI-VISA was `14.0.2 <http://www.ni.com/download/ni-visa-14.0.2/5075/en/>`_ .

Install NI-VISA using the instructions and ReadMe file included with the
installer. NI-VISA is compatible with Windows, Mac and Linux.

Python Libraries
^^^^^^^^^^^^^^^^

Labtronyx requires a number of libraries in order to function properly:

   * PyVISA
   * PySerial
   * Numpy

These libraries should be installed automatically when Labtronyx is installed.
If an error occurs during startup of the Labtronyx application, you can install 
these libraries by opening a terminal window (`Command Prompt` in Windows) and 
typing:

.. code-block:: console

   pip install pyvisa
   pip install pyserial
   pip install numpy
