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
        self.__instr = self.controller._getDevice(self.resID)
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        prop = models.m_Base.getProperties(self)
        
        # Add any additional properties here
        return prop
    
    def readRegisterValue(self, index, subindex):
        """
        Get a cached register value from the ICP device
        """
        return self.__instr.readReg(index, subindex)
    
    def writeRegisterValue(self, index, subindex, value):
        return self.__instr.writeReg(index, subindex, value)
    
    def getErrors(self):
        return self.getRegisterValue(0x1001, 0x00)
    