class UPEL_ICP_Device(object):
    """
    Instrument class for ICP devices. Used by Models to communicate with ICP
    devices over the network. 
    """
    
    data_types_pack = {
        'int8': lambda data: struct.pack('b', int(data)),
        'int16': lambda data: struct.pack('h', int(data)),
        'int32': lambda data: struct.pack('i', int(data)),
        'int64': lambda data: struct.pack('q', int(data)),
        'float': lambda data: struct.pack('f', float(data)),
        'double': lambda data: struct.pack('d', float(data)) }
    
    data_types_unpack = {
        'int8': lambda data: struct.unpack('b', data)[0],
        'int16': lambda data: struct.unpack('h', data)[0],
        'int32': lambda data: struct.unpack('i', data)[0],
        'int64': lambda data: struct.unpack('q', data)[0],
        'float': lambda data: struct.unpack('f', data)[0],
        'double': lambda data: struct.unpack('d', data)[0] }
    
    def __init__(self, address, arbiter):
        """
        :param address: IPv4 Address
        :type address: str
        """
        self.address = address
        self.arbiter = arbiter
        
        self.incomingPackets = {}
        
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
        
        self.incomingPackets[packetID] = pkt
        
    def _getResponse(self, packetID, data_type):
        """
        Get 
        :returns: UPEL_ICP_Packet object or None if no response
        """
        pkt = self.incomingPackets.get(packetID, None)
        
        if isinstance(pkt, ICP_Timeout):
            raise pkt
            
        elif pkt is not None:
            self.incomingPackets.pop(packetID)
            
            if isinstance(pkt, ErrorPacket):
                raise ICP_DeviceError(pkt)
            
            else:
                unpacker = self.data_types_unpack.get(data_type, None)
                if unpacker is not None:
                    return unpacker(pkt.getPayload())
                else:
                    return pkt.getPayload()
                
        else:
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
    # Device State
    #===========================================================================
    
    def getState(self):
        packet = StateChangePacket(0)
        
        self.arbiter.queueMessage(self.address, 10.0, packet)
        
        try:
            return self._getResponse(10.0)
            
        except ICP_Timeout:
            return None
        
    def setState(self, new_state):
        packet = StateChangePacket(new_state)
        
        self.arbiter.queueMessage(self.address, 10.0, packet)
        
        try:
            return self._getResponse(10.0)
            
        except ICP_Timeout:
            return None
    
    #===========================================================================
    # Register Operations
    #===========================================================================
    
    def register_write(self, address, subindex, data, data_type):
        pass
    
    def register_write_queue(self, address, subindex, data, data_type):
        pass
    
    def queue_writeReg(self, address, subindex, data, data_type):
        """
        Queue a write operation to a register. Returns packet ID for the sent
        packet. If there are no packet IDs currently available, this call
        blocks until one is available. Otherwise, this call returns immediately.
        
        :returns: packetID
        """
        packer = self.data_types_pack.get(data_type, None)
        if packer is not None:
            data = packer(data)
            
        packet = RegisterWritePacket(address, subindex, data)
        packet.setDestination(self.address)
        
        packetID = self.arbiter.queueMessage(packet, 10.0)
        
        return packetID
    
    def writeReg(self, address, subindex, data, data_type):
        """
        Write a value to a register. Blocking operation.
        
        :warning::
        
            Binary data cannot be encoded for network transmission from a Model.
            Models should use the appropriate writeReg function for the desired
            data type to avoid raising exceptions or corrupting data.
        """
        packetID = self.queue_writeReg(address, subindex, data, data_type)
        
        if packetID is not None:
            while True:
                try:
                    data = self._getResponse(packetID, data_type)
                    
                    if data is not None:
                        return data
                
                except ICP_Timeout:
                    return None
            
    def queue_readReg(self, address, subindex, data_type):
        """
        Queue a read operation to a register. Returns packet ID for the sent
        packet. If there are no packet IDs currently available, this call
        blocks until one is available. Otherwise, this call returns immediately.
        
        :returns: packetID
        """
        packet = RegisterReadPacket(address, subindex)
        packet.setDestination(self.address)
        
        packetID = self.arbiter.queueMessage(packet, 10.0)
        
        return packetID
    
    def readReg(self, address, subindex, data_type):
        """
        Read a value from a register. Blocks until data returns.
        
        :warning::
        
            Binary data cannot be encoded for network transmission from a Model.
            Models should use the appropriate readReg function for the desired
            data type to avoid raising exceptions. 
        
        :param address: 16-bit address
        :type address: int
        :param subindex: 8-bit subindex
        :type subindex: int
        :returns: str
        """
        packetID = self.queue_readReg(address, subindex, data_type)
        
        if packetID is not None:
            while True:
                try:
                    data = self._getResponse(packetID, data_type)
                    
                    if data is not None:
                        return data
                
                except ICP_Timeout:
                    return None
    
    #===========================================================================
    # Process Data Operations
    #===========================================================================
    
    def readProc(self, address):
        pass