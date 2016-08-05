Installation
============

Installing Python
-----------------

Download the latest version of Python 2.7 from the `official Python website <http://python.org>`_ .
Follow the directions on the Python website and the downloaded installer.

Additional instructions and help can be found at http://python.org

Installing Labtronyx
--------------------

From PIP
^^^^^^^^

Labtronyx is released as a package to the Python Package Index, and can be installed using pip:

.. code-block:: console

   pip install labtronyx

This will also install all of the necessary dependencies automatically. If you are running an earlier version of python,
you will need to install Pip before you will be able to install Labtronyx.

   * `Pip install instructions <http://pip.readthedocs.org/en/stable/installing/>`_

From Source
^^^^^^^^^^^

1. Clone the Labtronyx repository or unzip the source archive file.

2. Open a terminal window and browse to the location of the extracted files.

3. Execute the following command:

.. code-block:: console

   python setup.py install

The proper dependent packages will also be installed.

Numpy on Windows
^^^^^^^^^^^^^^^^

Numpy is a mathematics library for Python that provides optimized math functions used by many of the drivers in
Labtronyx. When installing Labtronyx on Windows, it may be necessary to download additional programs to install Numpy
correctly. This is only necessary when the installation above fails. There are two options:

1. Download the pre-compiled Numpy windows superpack distribution for your version of Python from
   the Numpy SourceForge page `here <http://sourceforge.net/projects/numpy/>`_.

   e.g. numpy-1.9.2-win32-superpack-python2.7.exe

2. Download the `Microsoft Visual C++ Compiler for Python 2.7 <http://aka.ms/vcpython27>`_. Install the package from
   pip: pip install numpy

Interface Dependencies
----------------------

Below are instructions to install dependent programs to enable to use of certain `Interfaces`.

VISA
^^^^

Using the VISA Interface requires a VISA server to be installed before Labtronyx can use any VISA resource. Any VISA
compatible server should work fine, but NI-VISA was found to be the most stable during development. The latest version
of NI-VISA can be downloaded from `nivisa`_ .

.. _nivisa: http://www.ni.com/visa

Install NI-VISA using the instructions and ReadMe file included with the installer. NI-VISA is compatible with Windows,
Mac and Linux.