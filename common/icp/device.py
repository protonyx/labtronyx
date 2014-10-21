import struct
import time
import threading

try:
    import numpy
except:
    pass

from errors import *
from packets import *

class UPEL_ICP_Device(object):
    """
    Instrument class for ICP devices. Used by Models to communicate with ICP
    devices over the network. 
    """
    
    incomingPackets = {}
    
    #===========================================================================
    # Registers
    #===========================================================================
    
    data_types_pack = {
        'int8': lambda data: struct.pack('!b', int(data)),
        'int16': lambda data: struct.pack('!h', int(data)),
        'int32': lambda data: struct.pack('!i', int(data)),
        'int64': lambda data: struct.pack('!q', int(data)),
        'float': lambda data: struct.pack('!f', float(data)),
        'double': lambda data: struct.pack('!d', float(data)) }
    
    data_types_unpack = {
        'int8': lambda data: struct.unpack('!b', data)[0],
        'int16': lambda data: struct.unpack('!h', data)[0],
        'int32': lambda data: struct.unpack('!i', data)[0],
        'int64': lambda data: struct.unpack('!q', data)[0],
        'float': lambda data: struct.unpack('!f', data)[0],
        'double': lambda data: struct.unpack('!d', data)[0] }
    
    reg_outgoing = {} # { PacketID: (address, subindex) }
    
    accumulators = {}
    acc_config = {}
    reg_cache = {}
    
    
    def __init__(self, address, packetQueue):
        """
        :param address: IPv4 Address
        :type address: str
        :param packetQueue: Outgoing Packet Queue
        :type packetQueue: Queue.Queue
        """
        self.address = address
        self.queue = packetQueue
        
        self.acc_thread = None
        
    def _processTimeout(self, packetID):
        """
        Called by the controller thread when a sent packet is considered
        expired
        """
        self.incomingPackets[packetID]= ICP_Timeout
        
    def _processResponse(self, pkt):
        """
        Called by the controller thread when a response packet is
        received that originated from this instrument.
        """
        packetID = pkt.PACKET_ID
        
        if isinstance(pkt, RegisterPacket):
            # Check if the register should be cached or accumulated
            try:
                address, subindex, data_type = self.reg_outgoing.pop(packetID)
                key = (address, subindex)
                
                if key in self.reg_cache.keys():
                    self.reg_cache[key] = pkt.get(data_type)
                    
                if key in self.accumulators.keys():
                    # TODO: add new value to accumulator
                    acc = self.accumulators.get(key)
                    acc.push(pkt.get(data_type))
                    
            except:
                pass
        
        self.incomingPackets[packetID] = pkt
        
    def _getResponse(self, packetID, block=False):
        """
        Get a response packet from the incoming packet queue. Non-blocking
        unless block is set to True.
        
        :param packetID: PacketID of desired packet
        :type packetID: int
        :param block: Block until packet is received or timeout occurs
        :type block: bool
        :returns: UPEL_ICP_Packet object or None if no response
        """
        if block:
            while (True):
                ret = self._getResponse(packetID)
                
                if ret is not None:
                    return ret
            
        else:
            try:
                pkt = self.incomingPackets.pop(packetID)
            
                if isinstance(pkt, ICP_Timeout):
                    raise pkt
                
                elif isinstance(pkt, ErrorPacket):
                    raise ICP_DeviceError(pkt)
                
                else:
                    return pkt
                
            except KeyError:
                return None
        
    #===========================================================================
    # def _getResponse(self, timeout):
    #     try:
    #         pkt = self.packetQueue.get(True, timeout)
    #         
    #         if isinstance(pkt, ErrorPacket):
    #             raise ICP_DeviceError(pkt);
    #         
    #         return str(pkt.getPayload())
    #         
    #     except Queue.Empty:
    #         raise ICP_Timeout
    #===========================================================================
    
    #===========================================================================
    # Accumulator Thread
    #===========================================================================
    
    def __accumulator_thread(self):
        """
        Asynchronous thread that automatically polls registers that are marked
        for accumulation
        """
        next_sample = {}
        
        while (len(self.acc_config) > 0):
            for reg, acc_config in self.acc_config.items():
                # Check if it is time to get a new sample
                if time.time() > next_sample.get(reg, 0.0):
                    address, subindex = reg
                    _, sample_time, data_type = acc_config
                    
                    # Queue a register read, the ICP thread will handle the data when it comes back
                    self.register_read_queue(address, subindex, data_type)
                    
                    # Increment the next sample time
                    next_sample[reg] = next_sample.get(reg, time.time()) + sample_time
                    
            # TODO: Calculate the time to the next sample and sleep until then
        
        # Clear reference to this thread before exiting
        self.acc_thread = None
        
    #===========================================================================
    # Device State
    #===========================================================================
    
    def getState(self):
        """
        Query the ICP Device for the current state.
        
        :returns: int
        """
        packet = StateChangePacket(0)
        packet.setDestination(self.address)

        try:
            packetID = self.queue(packet, 10.0)
            
            pkt = self._getResponse(packetID, block=True)
            return pkt.getState()
            
        except ICP_Timeout:
            return None
        
    def setState(self, new_state):
        packet = StateChangePacket(new_state)
        packet.setDestination(self.address)
        
        try:
            packetID = self.queue(packet, 10.0)
            
            pkt = self._getResponse(packetID, block=True)
            return pkt.getState()
            
        except ICP_Timeout:
            return None
    
    #===========================================================================
    # Register Operations
    #===========================================================================
    
    def register_config_cache(self, address, subindex):
        """
        Configure a register to reg_cache the value. Used for static values that change infrequently
        
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        """
        key = (address, subindex)
        self.reg_cache[key] = ''
                
    def register_config_accumulate(self, address, subindex, depth, sample_time, data_type):
        """
        Configure a register to accumulate values. Used to get sampled waveforms.
        
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        :param depth: Number of samples
        :type depth: int
        :param sample_time: Sample Time (sec)
        :type sample_time: float
        """
        key = (address, subindex)
        self.reg_cache[key] = ''
        self.acc_config[key] = (depth, sample_time, data_type)
        
        # Create a new accumulator object
        self.accumulators[key] = UPEL_ICP_Accumulator(depth, data_type)
        
        # Start the accumulator thread
        if self.acc_thread is None:
            self.acc_thread = threading.Thread(target=self.__accumulator_thread)
            self.acc_thread.start()
        
    def register_config_clear(self, address, subindex):
        """
        Clears register configuration if a register is set to cache or accumulate data.
        
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        """
        key = (address, subindex)
        
        try:
            self.accumulators.pop(key)
            self.acc_config.pop(key)
            self.reg_cache.pop(key)
        except:
            pass
        
    def register_accumulator_get(self, address, subindex):
        """
        Return accumulated data for registers configured.
        
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        """
        try:
            acc = self.accumulators.get((address, subindex))
        
            return acc.get()
        except:
            return None
    
    def register_write(self, address, subindex, data, data_type):
        """
        Write a value to a register. Blocking operation.
        
        :warning::
        
            Binary data cannot be encoded for network transmission from a Model.
            Models should use the appropriate writeReg function for the desired
            data type to avoid raising exceptions or corrupting data.
            
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        :param data: Data to write
        :type data: variable
        :param data_type: Data type
        :type data_type: str
        """
        try:
            packetID = self.register_write_queue(address, subindex, data, data_type)
        
            data = self._getResponse(packetID, block=True)
                    
            if data is not None:
                return data.get(data_type)
                
        except ICP_Timeout:
            return None
    
    def register_write_queue(self, address, subindex, data, data_type):
        """
        Queue a write operation to a register. Returns packet ID for the sent
        packet. If there are no packet IDs currently available, this call
        blocks until one is available. Otherwise, this call returns immediately.
        
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        :param data: Data to write
        :type data: variable
        :param data_type: Data type
        :type data_type: str
        :returns: packetID
        """
            
        packet = RegisterWritePacket(address, subindex, data, data_type)
        packet.setDestination(self.address)
        
        try:
            packetID = self.queue(packet, 10.0)
        
            self.reg_outgoing[packetID] = (address, subindex, data_type)
        
            return packetID
        
        except:
            raise
                
    def register_read_queue(self, address, subindex, data_type):
        """
        Queue a read operation to a register. Returns packet ID for the sent
        packet. If there are no packet IDs currently available, this call
        blocks until one is available. Otherwise, this call returns immediately.
        
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        :param data_type: Data type
        :type data_type: str
        :returns: packetID
        """
        packet = RegisterReadPacket(address, subindex)
        packet.setDestination(self.address)
        
        try:
            packetID = self.queue(packet, 10.0)
        
            self.reg_outgoing[packetID] = (address, subindex, data_type)
        
            return packetID
        
        except:
            raise
    
    def register_read(self, address, subindex, data_type):
        """
        Read a value from a register. Blocks until data returns. If cached data
        exists, it will be returned. A cache update can be forced by directly
        calling register_read_queue().
        
        :warning::
        
            Binary data cannot be encoded for network transmission from a Model.
            Models should use the appropriate readReg function for the desired
            data type to avoid raising exceptions. 
        
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        :param data_type: Data type
        :type data_type: str
        :returns: str
        """
        key = (address, subindex)
        
        if key in self.reg_cache.keys():
            # Cached & Accumulated registers should get values from the reg_cache
            return self.reg_cache.get(key, None)
            
        else:
            try:
                packetID = self.register_read_queue(address, subindex, data_type)
            
                data = self._getResponse(packetID, block=True)
                        
                if data is not None:
                    return data.get(data_type)
                    
            except ICP_Timeout:
                return None
    
    #===========================================================================
    # Process Data Operations
    #===========================================================================
    
    def readProc(self, address):
        pass
    
    
class UPEL_ICP_Accumulator(object):
    """
    Wrapper class for register accumulators. Wrapped object depends on data type
    of register::
    
        * int - Numpy array
        * string - Python list
        
    Accumulators are inherantly circular buffers. New data is pushed onto the 
    right side of the array, pushing all of the data left
    """
    
    def __init__(self, depth, data_type):
        pass
    
    def push(self, value):
        pass
    
    def get(self):
        pass