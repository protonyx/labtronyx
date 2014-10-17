import threading
from .. import m_Generic

class m_BDPC(m_Generic):
    """
    Common model for all BDPC devices
    """
    
    # Model device type
    deviceType = 'Source'
    
    registers = {
        'SensorGain': 0x2110,
        'SensorOffset': 0x2111,
        'SensorDescription': 0x2120,
        'SensorUnits': 0x2121,
        'SensorData': 0x2122,
        'SensorDataRaw': 0x2123,
        # Main Controller
        'FeedbackLoopGain': 0x2210,
        'PowerCommand': 0x2211,
        'MMCParameters': 0x2220,
        'MMCDiagnostics': 0x2222
        }
    
    numSensors = 4
    
    def _onLoad(self):
        m_Generic._onLoad(self)
        
        # Spawn a thread to update static values from device
        t = threading.Thread(target=self.update_startup)
        t.start()
    
    def getProperties(self):
        prop = m_Generic.getProperties(self)
        
        prop['numSensors'] = self.numSensors
        
        # Add any additional properties here
        return prop
    
    def update_startup(self):
        """
        Called on startup to get the following values:
        
            * Sensor types for all sensors
            * MMC Parameters (P/V/I)
        """
        for x in range(1,self.numSensors+1):
            address = self.registers.get('SensorDescription')
            self.instr.register_config_cache(address, x)
            self.instr.register_read_queue(address, x, 'string')
            
            address = self.registers.get('SensorUnits')
            self.instr.register_config_cache(address, x)
            self.instr.register_read_queue(address, x, 'string')
            
            
            
    def autoupdate_start(self, depth=100, sample_time=1.0):
        """
        
        """
        for x in range(1,self.numSensors+1):
            address = self.registers.get('SensorData')
            self.instr.register_config_accumulate(address, x, 'float', depth, sample_time)
        
        
    def autoupdate_stop(self):
        """
        
        """
        for x in range(1,self.numSensors+1):
            address = self.registers.get('SensorData')
            self.instr.register_config_clear(address, x)
    
    def update(self):
        """
        Update the following values:
        
            * Sensor Values
            * Control Angles (Phi AB/AD/DC)
        """
        for x in range(1, self.numSensors+1):
            address = self.registers.get('SensorData')
            self.instr.register_read_queue(address, x, 'float')
    
    
    #===========================================================================
    # Parameters
    #===========================================================================
    
    def getVoltage(self):
        address = self.registers.get('MMCParameters')
        return self.instr.register_read(address, 0x01, 'float')
    
    def setVoltage(self, set_v):
        address = self.registers.get('MMCParameters')
        return self.instr.register_write(address, 0x1, set_v, 'float');
    
    def getCurrent(self):
        address = self.registers.get('MMCParameters')
        return self.instr.register_read(address, 0x02, 'float')
    
    def setCurrent(self, set_i):
        address = self.registers.get('MMCParameters')
        return self.instr.register_write(address, 0x2, set_i, 'float');
    
    def getPower(self):
        address = self.registers.get('MMCParameters')
        return self.instr.register_read(address, 0x03, 'float')
    
    def setPower(self, set_p):
        address = self.registers.get('MMCParameters')
        return self.instr.register_write(address, 0x3, set_p, 'float');
    
    #===========================================================================
    # Diagnostics
    #===========================================================================
    
    
    
    #===========================================================================
    # Sensor Data
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
    
    def getSensorValue(self, sensor):
        address = self.registers.get('SensorData')
        return self.instr.register_read(address, sensor, 'float')
    
    def getSensorType(self, sensor):
        ret = {}
        
        address = self.registers.get('SensorDescription')
        try:
            ret['description'] = self.instr.register_read(address, sensor, 'string')
        except:
            ret['description'] = 'Unknown'
            
        address = self.registers.get('SensorUnits')
        try:
            ret['units'] = self.instr.register_read(address, sensor, 'string')
        except:
            ret['units'] = '?'
        
        return ret