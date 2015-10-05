Labtronyx Instrumentation Control Framework |build-status| |coverage| |codacy|
==============================================================================

The Labtronyx project is a framework for controlling laboratory instruments. It
provides an easy-to-use interface to a wide variety of instruments. It also 
facilitates automation scripts with a robust and well-documented API. Lastly,
it is flexible and extensible as to interface with any kind of instrument.

|license|

Documentation
-------------

Documentation is written in RestructuredText and compiled using Sphinx. It is also hosted at `docs`_.

.. _docs: http://labtronyx.readthedocs.org/en/latest/index.html

Building documentation requires Sphinx. To build documentation::

   python setup.py build_sphinx

Running Tests
-------------

Labtronyx includes a test suite that can be run using::

   python setup.py nosetests

Authors
-------

Kevin Kennedy (protonyx)

Changes
-------

See CHANGES

.. |build-status| image:: https://travis-ci.org/protonyx/labtronyx.svg?branch=master
   :target: https://travis-ci.org/protonyx/labtronyx
   :alt: Build status

.. |coverage| image:: https://coveralls.io/repos/protonyx/labtronyx/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/protonyx/labtronyx?branch=master
   :alt: Coveralls

.. |codacy| image:: https://www.codacy.com/project/badge/bd48cd184e04411395bae8362584cd6f
   :target: https://www.codacy.com/app/protonyx/labtronyx
   :alt: Codacy

.. |license| image:: https://img.shields.io/github/license/protonyx/labtronyx.svg
   :target: https://www.github.com/protonyx/labtronyx