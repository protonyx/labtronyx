import threading
from .. import m_Generic

class m_BDPC_Base(m_Generic):
    """
    Common model for all BDPC devices
    """
    
    # Model device type
    deviceType = 'Bidirectional Power Supply'

    
    sensors = {
        'PrimaryVoltage': 1,
        'SecondaryVoltage': 2,
        'PrimaryCurrent': 3,
        'SecondaryCurrent': 4,
        'ZVSCurrentA': 5,
        'ZVSCurrentB': 6,
        'ZVSCurrentC': 7,
        'ZVSCurrentD': 8
        }
    
    options = {
        'switching_enabled': 1,
        'parameter_latch': 100
        }
    
    def getProperties(self):
        prop = m_Generic.getProperties(self)
        
        prop['numSensors'] = len(self.sensors)
        
        # Add any additional properties here
        return prop
    
        # Model device type

    #===========================================================================
    # Options
    #===========================================================================
    
    def setOption(self, **kwargs):
        for arg in kwargs:
            if arg in self.control_bits:
                bit_number = self.control_bits.get(arg)
    
    #===========================================================================
    # Sensors
    #===========================================================================
    
    def setSensorGain(self, sensor, gain):
        raise NotImplementedError

    #===========================================================================
    # Parameters
    #===========================================================================
    
    def getVoltageReference(self):
        raise NotImplementedError
    
    def setVoltageReference(self, set_v):
        raise NotImplementedError
    
    def getCurrentReference(self):
        raise NotImplementedError
    
    def setCurrentReference(self, set_i):
        raise NotImplementedError
    
    def getPowerReference(self):
        raise NotImplementedError
    
    def setPowerReference(self, set_p):
        raise NotImplementedError
    
    #===========================================================================
    # Diagnostics
    #===========================================================================
    
    

    #===========================================================================
    # Composite Data
    #===========================================================================
    
    def getPrimaryPower(self):
        pv = self.getSensorValue(1)
        pi = self.getSensorValue(3)
        
        return pv*pi
    
    def getSecondaryPower(self):
        sv = self.getSensorValue(2)
        si = self.getSensorValue(4)
        
        return sv*si
    
    def getConversionRatio(self):
        pv = self.getSensorValue(1) 
        sv = self.getSensorValue(2)
        
        return float(sv) / float(pv)
    
    def getEfficiency(self):
        pp = self.getPrimaryPower()
        sp = self.getSecondaryPower()
        
        return float(sp) / float(pp)
    
