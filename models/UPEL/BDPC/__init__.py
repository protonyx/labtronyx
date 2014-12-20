import threading
from .. import m_Generic

__all__ = ['Base_ICP', 'Base_Serial']

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
        'switching': 0,
        'require_external_enable': 1,
        'master_mode': 2,
        'slave_mode': 3,
        'latch_param_reg': 4,
        'latch_diagnostic_reg': 5,
        'open_main_loop': 6,
        'open_aux_loops': 7,
        'manual_dead_time': 8,
        'fixed_gain': 9,
        'manual_fet_control': 10,
        'manual_input_voltage': 11
        }
    
    status = {
        'soft_start': 0,
        'switching': 1,
        'feedback_control': 2,
        'ZVS_compensator': 3,
        'secondary_overvoltage': 4,
        'primary_overvoltage': 5
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
        raise NotImplementedError
                
    def getOption(self):
        raise NotImplementedError
    
    #===========================================================================
    # Sensors
    #===========================================================================
    def getSensors(self):
        raise NotImplementedError
    
    def setSensorGain(self, sensor, gain):
        raise NotImplementedError
    
    def getSensorGain(self, sensor):
        raise NotImplementedError
    
    def setSensorOffset(self, sensor, offset):
        raise NotImplementedError
    
    def getSensorOffset(self, sensor):
        raise NotImplementedError
    
    def getSensorValue(self, sensor):
        raise NotImplementedError
    
    def getSensorValue_ext(self, sensor, module):
        pass
    
    def getSensorRawValue(self, sensor):
        raise NotImplementedError
    
    def getSensorUnits(self, sensor):
        raise NotImplementedError
    
    def getSensorDescription(self, sensor):
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
    
    def setPowerCommand(self, command):
        raise NotImplementedError
    
    def setPhaseShift(self, angle):
        raise NotImplementedError
    
    def getPhaseShift(self):
        raise NotImplementedError
    
    def setPhaseAngle(self, leg, angle):
        raise NotImplementedError
    
    def setDeadTime(self, leg, nanoseconds):
        raise NotImplementedError
    
    def setGain(self, gain):
        raise NotImplementedError
    
    #===========================================================================
    # Diagnostics
    #===========================================================================
    def getStatus(self):
		raise NotImplementedError
		
    def getConversionRatioMeasured(self):
		raise NotImplementedError
		
    def getPowerCommand(self):
		raise NotImplementedError
		
    def getPhaseAngle(self):
		raise NotImplementedError
	
    def getGain(self):
		raise NotImplementedError
		
    def getMMCMode(self):
		raise NotImplementedError    

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
    
    def getConversionRatioCalc(self):
        pv = self.getSensorValue(1) 
        sv = self.getSensorValue(2)
        
        return float(sv) / float(pv)
    
    def getEfficiency(self):
        pp = self.getPrimaryPower()
        sp = self.getSecondaryPower()
        
        return float(sp) / float(pp)
    
