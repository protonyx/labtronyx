:Author: John Millikin
:Copyright: This document has been placed in the public domain.

Overview
========

This is yet another library for reading/writing json. The goal is to
be API compatible with `simplejson
<http://pypi.python.org/pypi/simplejson>`_, except that it is written
purely in C and is thus 5x-20x faster for both encoding and decoding,
depending on the data.

This is a fork of the `jsonlib <https://launchpad.net/jsonlib>`_
project by the folks over at `Freebase <https://www.freebase.com>`_ who
have data coming from a variety of internal sources in different
encodings and formats, not all of which could simply be represented by
strict JSON.

Thus, the intent of this fork is to be more lenient in its
encoding and decoding (as simplejson is) allowing things like
NaN/-NaN/Infinity, automatic handling of unicode, and more. The first
release of jsonlib2 was version 1.4, which was forked from jsonlib
1.3.10.

.. contents::

Usage
=====

jsonlib2 has two functions of interest, ``read`` and ``write``. It also
defines some exception: ``ReadError``, ``WriteError``, and
``UnknownSerializerError``.

For compatibility with the standard library, ``read`` is aliased to
``loads`` and ``write`` is aliased to ``dumps``. They do not have the
same set of advanced parameters, but may be used interchangeably for
simple invocations.

Deserialization
---------------

To deserialize a JSON expression, call the ``jsonlib2.read`` function with
an instance of ``str`` or ``unicode``. ::

	>>> import jsonlib2
	>>> jsonlib2.read ('["Hello world!"]')
	[u'Hello world!']

Floating-point values
~~~~~~~~~~~~~~~~~~~~~

By default, ``jsonlib2`` will parse values such as "1.1" into an instance of
``decimal.Decimal``. To use the built-in value type ``float`` instead, set
the ``use_float`` parameter to ``True``. Please note that this may cause a
loss of precision when parsing some values. ::

	>>> jsonlib2.read ('[1.5]', use_float = True)
	[1.5]
	>>> jsonlib2.read ('[1.1]', use_float = True)
	[1.1000000000000001]
	>>> jsonlib2.read ('[3.14159265358979323846]', use_float = True)
	[3.1415926535897931]

Serialization
-------------

Serialization has more options, but they are set to reasonable defaults.
The simplest use is to call ``jsonlib2.write`` with a Python value. ::

	>>> import jsonlib2
	>>> jsonlib2.write (['Hello world!'])
	'["Hello world!"]'

Pretty-Printing
~~~~~~~~~~~~~~~

To "pretty-print" the output, pass a value for the ``indent`` parameter. ::

	>>> print jsonlib2.write (['Hello world!'], indent = '    ')
	[
	    "Hello world!"
	]
	>>> 
	
Mapping Key Sorting
~~~~~~~~~~~~~~~~~~~

By default, mapping keys are serialized in whatever order they are
stored by Python. To force a consistent ordering (for example, in doctests)
use the ``sort_keys`` parameter. ::

	>>> jsonlib2.write ({'e': 'Hello', 'm': 'World!'})
	'{"m":"World!","e":"Hello"}'
	>>> jsonlib2.write ({'e': 'Hello', 'm': 'World!'}, sort_keys = True)
	'{"e":"Hello","m":"World!"}'

Encoding and Unicode
~~~~~~~~~~~~~~~~~~~~

By default, the output is encoded in UTF-8. If you require a different
encoding, pass the name of a Python codec as the ``encoding`` parameter. ::

	>>> jsonlib2.write (['Hello world!'], encoding = 'utf-16-be')
	'\x00[\x00"\x00H\x00e\x00l\x00l\x00o\x00 \x00w\x00o\x00r\x00l\x00d\x00!\x00"\x00]'

To retrieve an unencoded ``unicode`` instance, pass ``None`` for the
encoding. ::

	>>> jsonlib2.write (['Hello world!'], encoding = None)
	u'["Hello world!"]'

By default, non-ASCII codepoints are forbidden in the output. To include
higher codepoints in the output, set ``ensure_ascii`` to ``False``. ::

	>>> jsonlib2.write ([u'Hello \u266a'], encoding = None)
	u'["Hello \\u266a"]'
	>>> jsonlib2.write ([u'Hello \u266a'], encoding = None, ensure_ascii = False)
	u'["Hello \u266a"]'

Mapping Key Coercion
~~~~~~~~~~~~~~~~~~~~

Because JSON objects must have string keys, strings will be 'coerced'
to strings. You can override this with the ``coerce_keys`` parameter,
whcih will raise exception when non-string keys are encountered in a
mapping. ::

	>>> jsonlib2.write ({True: 1})
	'{"true":1}'
	>>> jsonlib2.write ({True: 1}, coerce_keys = False)
	Traceback (most recent call last):
	WriteError: Only strings may be used as object keys.

Serializing Other Types
~~~~~~~~~~~~~~~~~~~~~~~

If the object implements the iterator or mapping protocol, it will be
handled automatically. If the object is intended for use as a basic value,
it should subclass one of the supported basic values.

String-like objects that do not inherit from ``str``, ``unicode``, or
``UserString.UserString`` will likely be serialized as a list. This will
not be changed. If iterating them returns an instance of the same type, the
serializer might crash. This (hopefully) will be changed.

To serialize a type not known to jsonlib2, use the ``default`` parameter
to ``write``::

	>>> from datetime import date
	>>> def default_handler (value):
	...     if isinstance (value, date): return str (value)
	...     raise jsonlib2.UnknownSerializerError
	>>> jsonlib2.write ([date (2000, 1, 1)], default = default_handler)
	'["2000-01-01"]'

Streaming Serializer
~~~~~~~~~~~~~~~~~~~~

When serializing large objects, the use of an in-memory buffer may cause
too much memory to be used. For these situations, use the ``dump`` function
to write objects to a file-like object::

	>>> import sys
	>>> jsonlib2.dump (["Written to stdout"], sys.stdout)
	["Written to stdout"]
	>>> 

Exceptions
-----------

ReadError
~~~~~~~~~

Raised by ``read`` if an error was encountered parsing the expression. Will
contain the line, column, and character position of the error.

Note that this will report the *character*, not the *byte*, of the character
that caused the error.

WriteError
~~~~~~~~~~

Raised by ``write`` or ``dump`` if an error was encountered serializing
the passed value.

UnknownSerializerError
~~~~~~~~~~~~~~~~~~~~~~

A subclass of ``WriteError`` that is raised when a value cannot be
serialized. See the ``default`` parameter to ``write``.

Change Log
==========

1.5.1
-----
* Fixed problem compiling on Python before version 2.6, as reported by 
  Carlo Barrettara and others

1.5
---
* Major API change - add lots of support for simplejson keywords
* dropped use of Decimal module, and thus the ``use_float`` parameter
  in ``load``. In ``dump``, use ``default``.
* in ``load``, added parsing support for Infinity, -Infinity, NaN
* in ``load``, added support for ``parse_float``, ``parse_int``,
  ``parse_constant``
* in ``dump``, ``allow_non_numbers`` became ``allow_nan``
* in ``dump``, ``allow_nan`` (formerly ``allow_non_numbers``) is now
  True by default
* in ``dump``, ``on_unknown`` became ``default``
* in ``dump``, ``ascii_only`` became ``ensure_ascii``
* in ``dump``, ``coerce_keys`` is now True by default
* Removed JSON-strict restriction, allowing both ``load`` and ``dump``
  to deal with objects that are not lists or dictionaries at the root
  level.

1.4.2
-----
* Memory leak fix

1.4.1
-----
* Added ``escape_slash`` parameter to ``write()`` to stop escaping the
  '/' character

1.4
---
* First release as jsonlib2

1.3.10
------
* Implemented the ``use_float`` parameter to ``read()``.

1.3.9
-----
* Fixed a crash on some platforms when passing a non-string object for
  indentation.

1.3.8
-----
* Fixed memory leak when auto-decoding bytestrings.
* Fixed potential memory leak when using ``on_unknown`` handlers that
  return invalid objects.

1.3.7
-----
* Fixed error reporting positions of syntax errors that occur immediately
  after a newline.
* Add ``loads()`` and ``dumps()`` as aliases to ``read()`` and ``write()``,
  respectively, for compatibility with the new ``json`` standard library
  module.
* Small fixes to the test suite to clear spurious errors caused by
  differences between the behavior of ``repr()`` on instances of
  ``decimal.Decimal`` and ``UnicodeDecodeError``.

1.3.6
-----
* If an unterminated object or array is encountered, report its start
  location properly.
* Improved reporting of unknown escape codes.
* Raise an exception when parsing a root value that is not an array
  or object.
* Allow instances of ``UserString`` to be used as object keys.
* Implemented the ``dump()`` function.

1.3.5
-----
* Bugfix release, corrects serialization of ``dict`` when ``PyDict_Next()``
  skips indexes.

1.3.4
-----
* Fixes an issue with reporting the column of a syntax error when the
  error is followed by a newline.
* Removed remaining Python wrapper for ``read``.

1.3.3
-----
* Support the ``on_unknown`` parameter to ``write``.
* Corrected typo in invalid whitespace detection.
* Added ``__version__`` attribute.
* Merged all code into ``jsonlib2`` and ``_jsonlib`` modules, instead of
  a package.

1.3.2
-----
* Improved the README.
* Support for reading text encoded with the ``utf-8-sig`` codec.
* Use ``codecs`` module for detecting BOMs in input data.
* Forbid non-whitespace strings from being used for indentation.

1.3.1
-----
* Removed the Python implementations of the serializer and deserializer.
* Detect and raise an exception if invalid surrogate pairs are serialized
  or deserialized.
* Detect and raise an exception if reserved codepoints are serialized or
  deserialized.
* Added support for operating in a process with multiple Python interpreters.
* Performance improvements.

1.3.0
-----
* Allow ``python setup.py test`` to work.
* Added ``encoding`` parameter to ``write``, which controls the output
  encoding. The default encoding is ``utf-8``. If the encoding is ``None``,
  a ``unicode`` string will be returned.
* Implemented ``write`` using a C extension module.

1.2.7
-----
* Improved error messages when an error is encountered deserializing an
  expression.
* Modified to work with Python 2.4.

1.2.6
-----

Thanks to Deron Meranda (author of ``demjson``) for his excellent `JSON
library comparison <http://deron.meranda.us/python/comparing_json_modules/>`_,
which revealed many areas for improvement:

* Use ``repr`` instead of ``unicode`` for serializing floating-point values,
  to avoid unnecessary rounding.
* Fixed bug that prevented plus signs in an exponent from being parsed
  correctly.
* Added support for serializing the following types:

  - ``generator``
  - ``set``
  - ``frozenset``
  - ``complex``, for values with no imaginary component.
  - ``array.array``
  - ``collections.deque``
  - ``collections.defaultdict``
  - ``UserList.UserList``
  - ``UserDict.UserDict``
  - ``UserString.UserString``

* Raise an exception if a control character is encountered in a string.
* Added support for detecting Unicode byte order marks in the auto decoder.
* Allow only arrays and objects to be serialized directly. All other types
  must be contained within an array or object.
* Stricter detection of whitespace.

Also includes some other miscellaneous fixes:

* More reliable detection of ``Infinity`` and ``NaN`` on Windows.
* Support for decoding UTF-32 on UCS2 builds of Python.
* Faster detection of self-recursive containers.

1.2.5
-----
* Return Unicode strings from ``write``, so the user can control the final
  encoding.
* Prevent ``Infinity``, ``-Infinity``, and ``NaN`` from being serialized
  because JSON does not support these values.
* Added ``coerce_keys`` parameter to ``write``. If ``True``, mapping keys
  will be coerced to strings. Defaults to ``False``.
* Added ``ascii_only`` parameter to ``write``. If ``True``, non-ASCII
  codepoints will always be escaped to a \u sequence. Defaults to ``True``.
* Real detection of self-recursive container types.
* Escape the solidus to prevent against `security issues
  <http://t3.dotgnu.info/blog/insecurity/quotes-dont-help.html>`_.

1.2.4
-----
* Fixed bug that prevented characters from being read after reading a
  Unicode escape sequence.
* Moved test cases into ``jsonlib2.tests`` subpackage.

1.2.3
-----
* Port to setuptools.
* Corrected false positive in detection of illegal leading zeroes.

1.2.2
-----
* Raise an exception if values in an object or array are not separated by
  commas.

1.2.1
-----
* Support for building on Windows.

1.2.0
-----
* Added ``sort_keys`` parameter to ``write``. This allows mapping types to
  be serialized to a predictable value, regardless of key ordering.
* Added ``indent`` to ``write``. Any string passed as this value will be
  used for indentation. If the value is not `None`, pretty-printing will
  be activated.

1.1.0
-----
* Support for reading astral Unicode codepoints on UCS2 builds of Python.

1.0.0
-----
* Initial release.
