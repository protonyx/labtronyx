import models

class m_Generic(models.m_Base):
    
    # Model device type
    deviceType = 'Generic'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_UPEL']
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validVIDs = ['UPEL']
    validPIDs = ['Generic']
    
    def _onLoad(self):
        self.__instr = self.controller._getDevice(self.resID)
        
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        prop = models.m_Base.getProperties(self)
        
        # Add any additional properties here
        return prop
    
    def getErrors(self):
        return self.__instr.readReg(0x1001, 0x00)
    