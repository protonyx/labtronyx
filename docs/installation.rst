Installation
============

Installing Python
-----------------

Download the latest version of Python 2.7 from the `official Python website <http://python.org>`_ .
Follow the directions on the Python website and the downloaded installer.

Additional instructions and help can be found at http://python.org

Installing Labtronyx
--------------------

Using Pip
^^^^^^^^^

Labtronyx can be installed using pip with the command::

   pip install labtronyx

From Source
^^^^^^^^^^^

1. Unzip the archive file.

2. Open a terminal window and browse to the location of the extracted files.

3. Execute the following command:

.. code-block:: console

   python setup.py install

The proper dependent packages will also be installed.

Notes
-----

Numpy on Windows
^^^^^^^^^^^^^^^^

Numpy is a mathematics library for Python that provides optimized math functions used by many of the drivers in
Labtronyx. When installing Labtronyx on Windows, it may be necessary to download additional programs to install Numpy
correctly. This is only necessary when the installation above fails. There are two options:

1. Download the pre-compiled Numpy windows superpack distribution for your version of Python from
   the Numpy SourceForge page `here <http://sourceforge.net/projects/numpy/>`_.

   e.g. numpy-1.9.2-win32-superpack-python2.7.exe

2. Download the `Microsoft Visual C++ Compiler for Python 2.7 <http://aka.ms/vcpython27>`_.

Pip
^^^

Pip is a Python Package manager that is included with Python beginning with version 2.7.9 and all version of Python 3.
If you are running an earlier version of python, you will need to install Pip before you will be able to install
Labtronyx.

   * `Pip install instructions <http://pip.readthedocs.org/en/stable/installing/>`_