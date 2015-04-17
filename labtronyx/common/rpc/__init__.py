"""
Remote Procedure Call (RPC)
---------------------------
Remote Procedure Call (RPC) allows an object to be accessed from any networked 
machine as if it were a local object on the operator's machine. This allows 
really easy application and script development, as the communication with the 
instrument over the network is taken care of by the :mod:`common.Rpc` library.

.. _JSON-RPC: http://www.jsonrpc.org/specification

"""
from jsonrpc import *
from server import *
from client import *
from errors import *
        