from models import m_Base

class m_Tektronix(m_Base):
    """
    All Tektronix devices are VISA devices
    
    All Tektronix models that inherit from models.Tektronix will inherit all of the low-level VISA functions
    """
    
    validVIDs = ['Tektronix']

    def _onLoad(self):
        self.__identity = None
        self.controller = self.getControllerObject()
        
        try:
            # All Tektronix models use c_VISA
            self.__instr = self.controller.openResourceObject(self.resID)
            
            # Bring VISA Instrument functions into this context
            self.write = self.__instr.write
            self.read = self.__instr.read
            self.read_values = self.__instr.read_values
            self.read_raw = self.__instr.read_raw
            self.ask = self.__instr.ask
            self.ask_for_values = self.__instr.ask_for_values
            
            resp = self.ask("*IDN?")
            self.__identity = resp.strip().split(',')
            
        except:
            self.logger.exception("Internal error while instantiating Tektronix model")
            
    def getProperties(self):
        ret = m_Base.getProperties(self)
        ret['deviceVendor'] = 'Tektronix'
        if self.__identity is not None:
            ret['deviceModel'] = self.__identity[1]
            ret['deviceSerial'] = self.__identity[2]
            ret['deviceFirmware'] = self.__identity[3]
            
        return ret
        
