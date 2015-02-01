import struct

import models

class m_Generic(models.m_Base):
    """
    Generic model for an ICP device
    
    Caching:
    
    ICP device models contain a cache of all register values. By default,
    cache data is considered expired as soon as it is collected. The result
    is that all register data is refreshed when requested.
    
    To fully utilize register caching, a cache refresh thread is started
    to routinely update register values from the device. The cache thread
    must know the following things:
    
        * Which registers to update
        * What time interval should registers be updated
        
    Class variable `instr` is available for sub-classes to interact with the
    ICP Instrument Object.
    """
    
    registers = {}
    
    states = {
        0x01: ('Running', 'Start'),
        0x02: ('Stopped', 'Stop'),
        0x80: ('Ready', 'Initialize'),
        0x81: ('Reset', 'Reset') }
    
    state_transitions = {
        0x01: [0x02, 0x80, 0x81],
        0x02: [0x80, 0x81],
        0x80: [0x01, 0x81],
        0x81: [0x80]}
    
    def _onLoad(self):
        self.controller = self.getControllerObject()
        self.instr = self.controller.openResourceObject(self.resID)
        
        self.register_cache = {}
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        prop = models.m_Base.getProperties(self)
        
        # Add any additional properties here
        return prop
    
    #===========================================================================
    # Operation
    #===========================================================================
    
    def getStates(self):
        return self.states
    
    def getStateTransitions(self):
        return self.state_transitions
    
    def getState(self):
        return self.instr.getState()
    
    def setState(self, new_state):
        return self.instr.setState(new_state)    
    
    def getErrors(self):
        return int(self.instr.readReg(0x1001, 0x01, 'int16'))
    
    def getStatus(self):
        return int(self.instr.readReg(0x1002, 0x1, 'int16'))
    
    #===========================================================================
    # Register Operations
    #===========================================================================
    
    def readRegister(self, address, subindex, data_type):
        """
        Read a register value from the ICP device.
        """
        try:
            res = self.instr.register_read(address, subindex, data_type)
            
            return res
            
        except:
            self.logger.exception('')
            return 'INVALID'
    
    def writeRegister(self, address, subindex, data_type, value):
        try:
            return self.instr.register_write(address, subindex, value, data_type)
        
        except:
            self.logger.exception('')
            return 'INVALID'