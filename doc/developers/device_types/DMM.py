
class m_DMM_Template(object):
    """
    Object Template for Digital Multimeters
    """
    
    deviceType = 'Digital Multimeter'
    
    def setFunction(self, func):
        raise NotImplementedError
    
    def getFunction(self):
        raise NotImplementedError
    
    def getAllFunctions(self):
        raise NotImplementedError
    
    def getMeasurement(self):
        raise NotImplementedError
    
    