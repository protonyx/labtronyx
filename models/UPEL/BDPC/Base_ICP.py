import threading

from . import m_BDPC_Base

class Base_ICP(m_BDPC_Base):
    
    info = {
        # Model revision author
        'author':               'KKENNEDY',
        # Model version
        'version':              '1.0',
        # Revision date of Model version
        'date':                 '2015-01-31',
        # Device Manufacturer
        'deviceVendor':         'UPEL',
        # List of compatible device models
        'deviceModel':          ['BDPC'],
        # Device type    
        'deviceType':           'DC-DC Converter',      
        
        # List of compatible resource types
        'validResourceTypes':   ['UPEL']
    }
    
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
        'MMCDiagnostics': 0x2222,
#         This StatusReg function will return only the value of the status register to use here
        'StatusReg': 0x2000
        }
    
    #===========================================================================
    # Maybe obsolete functions
    #===========================================================================
    
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
            
            # Cache sensor data
            address = self.registers.get('SensorData')
            self.instr.register_config_cache(address, x)
            
    
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
    # Sensors
    #===========================================================================
    
    def setCalibration(self, sensor, gain, offset):
        pass
    
    def getCalibration(self, sensor):
        pass
    
    def getSensorValue(self, sensor):
        address = self.registers.get('SensorData')
        return float(self.instr.register_read(address, sensor, 'float'))
    
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
    
    #===========================================================================
    # Parameters
    #===========================================================================
    
    def commitParameters(self):
        address = self.registers.get('MMCParameters')
        #return self.instr.register_write(address, 0x4, 1, 'int8');
        # Implement this in the bridge
    
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

    def getSensorValue(self, sensor):
        return self._getRegisterValue(0x2122, sensor)    
