import models

class m_test(models.m_Base):
    
    # Model device type
    deviceType = 'Debug'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_Dummy']
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validVIDs = ['Test']
    validPIDs = ['12345']
    
    def _onLoad(self):
        pass
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        prop = models.m_Base.getProperties(self)
        
        # Add any additional properties here
        return prop
    
    def doThing(self):
        return 'Thing!'
    