Common Library
==============

This file will contain documentation for common library modules.

Remote Procedure Call (RPC) Library
-----------------------------------

The RPC Library leverages JSON-RPC 2.0 and the :mod:`socket` library to allow
function calls using TCP/IP Packets. This library is used heavily in
InstrumentControl and InstrumentManager.

JSON-RPC
^^^^^^^^

.. autoclass:: labtronyx.common.rpc.jsonrpc.JsonRpcPacket
   :members:

RpcServer
^^^^^^^^^

.. autoclass:: labtronyx.common.rpc.server.RpcServer
   :members:

RpcClient
^^^^^^^^^

.. autoclass:: labtronyx.common.rpc.client.RpcClient
   :members:
   :private-members: