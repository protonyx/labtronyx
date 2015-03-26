UPEL Instrument Control Protocol (ICP)
======================================

Dependencies
------------

None

Detailed Operation
------------------

The UPEL ICP thread manages communication in and out of the network socket
on port 7968.

Message Queue
^^^^^^^^^^^^^

Packets to send out to remote devices are queued in the message queue and sent
one at a time. Queuing a message requires:

  * IP Address
  * TTL (Time to Live)
  * Response Queue
  * ICP Packet Object

The response packet object will be loaded into the response queue.

Routing Map
^^^^^^^^^^^

When a message is sent, it is assigned an ID within the packet header. If a
response is expected from an outgoing packet, an entry is made in the map
table to associate the packet ID of the response packet with the object that
sent the original packet.

The Arbiter will periodically scan the routing map for old entries. If an
entry has exceeded the TTL window, a signal is sent to the originating
object that a timeout condition has occurred. 

The Packet ID is an 8-bit value, so there are 256 possible ID codes. A 
Packet ID of 0x00 is reserved for "notification" packet where a response is 
not expected, and thus will never create an entry in the routing map, giving 
a maximum of 255 possible entries in the routing map.

The routing map has the format: { PacketID: Address }

Execution Strategy
^^^^^^^^^^^^^^^^^^

The arbiter will alternate between servicing the message queue, processing 
any data in the __socket buffer, and checking the status of entries in the 
routing map. If none of those tasks requires attention, the thread will 
sleep for a small time interval to limit loading the processor excessively.

Interface
---------

.. autoclass:: labtronyx.interfaces.i_UPEL.i_UPEL
   :members:
   :inherited-members:
   
Resources
---------

.. autoclass:: labtronyx.interfaces.i_UPEL.r_UPEL
   :members:
   :inherited-members:
   