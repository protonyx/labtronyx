
from . import errors
from . import packets

packet_types = {
    0x00: packets.DiscoveryPacket,
    0x01: packets.EnumerationPacket,
    0x02: packets.HeartbeatPacket,
    0x03: packets.StateChangePacket,
    0x0F: packets.ErrorPacket,
    0x80: packets.ResponsePacket,
    0x81: packets.CommandPacket,
    0x82: packets.RegisterReadPacket,
    0x83: packets.RegisterWritePacket,
    0x88: packets.SerialDescriptorPacket,
    0x89: packets.CANDescriptorPacket
}