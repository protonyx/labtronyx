Remote Procedure Call (RPC) Library
===================================

The RPC Library leverages JSON-RPC 2.0 and the :mod:`socket` library to allow
function calls using TCP/IP Packets. This library is used heavily in
InstrumentControl and InstrumentManager.

RpcBase
-------

.. autoclass:: common.rpc.RpcBase
   :members:

RpcClient
---------

.. autoclass:: common.rpc.RpcClient
   :members:
   :private-members: