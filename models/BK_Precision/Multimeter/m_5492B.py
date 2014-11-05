from . import m_MultimeterBase

class m_5492B(m_MultimeterBase):
    
    # Model device type
    deviceType = 'Multimeter'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_VISA', 'c_Serial']
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validVIDs = ['Unknown']
    validPIDs = ['5492B Digital Multimeter']
    
    def getProperties(self):
        ret = m_MultimeterBase.getProperties(self)
        
        ret['deviceVendor'] = 'BK Precision'
        if self._identity is not None:
            ret['deviceModel'] = "5492B" #self.__identity[0]
            ret['deviceSerial'] = self._identity[2]
            ret['deviceFirmware'] = self._identity[1]
            
        return ret
    
