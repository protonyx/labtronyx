from . import m_MultimeterBase

class m_2831E(m_MultimeterBase):
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validVIDs = ['Unknown']
    validPIDs = ['2831E  Multimeter']
    
    def getProperties(self):
        ret = m_MultimeterBase.getProperties(self)
        
        ret['deviceVendor'] = 'BK Precision'
        if self._identity is not None:
            ret['deviceModel'] = "2831E" #self.__identity[0]
            ret['deviceSerial'] = self._identity[2]
            ret['deviceFirmware'] = self._identity[1]
            
        return ret

    
