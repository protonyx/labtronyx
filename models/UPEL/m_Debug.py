from . import m_Generic

class m_Debug(m_Generic):
    """
    UPEL Debugging Model
    
    Offers direct access to ICP functions that are normally abstracted
    """
    
    # Model device type
    deviceType = 'Debug'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_UPEL']
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validVIDs = ['UPEL']
    validPIDs = ['BDPC_BR1', 'BDPC_BR2']
    
    #===========================================================================
    # Register Operations
    #===========================================================================
    
    def readRegisterValue(self, index, subindex):
        """
        Get a cached register value from the ICP device
        """
        return self.__instr.readReg(index, subindex)
    
    def writeRegisterValue(self, index, subindex, value):
        return self.__instr.writeReg(index, subindex, value)