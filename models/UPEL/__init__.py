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
    
    # Model device type
    deviceType = 'Generic'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_UPEL']
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validVIDs = ['UPEL']
    validPIDs = ['Generic']
    
    regCache = {}
    
    def _onLoad(self):
        self.instr = self.controller._getDevice(self.resID)
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        prop = models.m_Base.getProperties(self)
        
        # Add any additional properties here
        return prop
    
    #===========================================================================
    # Operation
    #===========================================================================
    
    def getOperationState(self):
        return self.instr.getState()
    
    def setOperationState(self, new_state):
        return self.instr.setState(new_state)
    
    def getValidNextState(self):
        """
        Given the current operation state, return the next valid state transition
        """
        state = self.getOperationState()
        
    
    def getErrors(self):
        return self.getRegisterValue(0x1001, 0x00)
    