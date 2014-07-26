InstrumentControl can be started in two modes: script mode and interactive mode. There is no functional difference between
the two modes, but interactive mode will start everything automatically and load the main GUI.

Script Mode
===========
When InstrumentControl is instantiated, an InstrumentManager object is created and all controllers and models are loaded.
The manager object can be accessed by calling the getManager()

Interactive Mode
================