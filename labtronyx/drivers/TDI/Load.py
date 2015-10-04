"""
.. codeauthor:: Kevin Kennedy <protonyx@users.noreply.github.com>

"""
from labtronyx.bases import Base_Driver
from labtronyx.common.errors import *

info = {
    # Plugin author
    'author':               'KKENNEDY',
    # Plugin version
    'version':              '1.0',
    # Last Revision Date
    'date':                 '2015-10-04',
}


class d_XBL(Base_Driver):
    """
    Driver for TDI XBL Series DC Electronic Loads

    Remote Interface
    ----------------

    These loads feature a Ethernet connection that hosts a web-based interface from
    which you can control the load much like you would if you were sitting in front
    of it.
    """
    
    info = {
        # Device Manufacturer
        'deviceVendor':         'TDI',
        # List of compatible device models
        'deviceModel':          ['XBL-50-150-800', 'XBL-100-120-800',
                                 'XBL-400-120-800', 'XBL-600-40-800',
                                 'XBL-50-400-2000', 'XBL-100-300-2000',
                                 'XBL-400-300-2000', 'XBL-600-100-2000',
                                 'XBL-50-1000-4000', 'XBL-100-600-4000',
                                 'XBL-400-600-4000', 'XBL-600-200-4000',
                                 'XBL-100-600-6000', 'XBL-400-600-6000',
                                 'XBL-600-200-6000'],
        # Device type    
        'deviceType':           'DC Electronic Load',      
        
        # List of compatible resource types
        'validResourceTypes':   ['Serial']
    }
    
    modes = {
        'Constant Current': 'CI',
        'Constant Voltage': 'CV',
        'Constant Power': 'CW',
        'Constant Resistance': 'CR'}
    
    def open(self):
        # Turn off text mode (mangles queries)
        self.instr.write("TEXT OFF")
        
        # Turn off keyboard sounds
        self.instr.write("KEYOFF")
    
    def close(self):
        pass
        
    def getProperties(self):
        ret = Base_Driver.getProperties(self)
        
        ret['deviceVendor'] = 'TDI'
        
        ret['deviceModel'] = self.query("MDL?")
        ret['deviceSerial'] = self.query("SERNO?")
        ret['deviceFirmware'] = self.query("VER?")
            
        return ret
    
    def powerOn(self):
        """
        Turns the load on
        """
        self.write("LOAD ON")
    
    def powerOff(self):
        """
        Turns the load off
        """
        self.write("LOAD OFF")
        
    def setMaster(self):
        """
        Set load into master mode
        """
        self.write("MASTER")
        
    def setSlave(self):
        """
        Set load into slave mode
        """
        self.write("SLAVE")
    
    def setMaxCurrent(self, current):
        """
        Sets the maximum current the load will sink
        
        :param current: Current in Amps
        :type current: float
        """
        self.write("IL %s" % str(current))
    
    def getMaxCurrent(self):
        """
        Returns the maximum current the load will sink
        
        :returns: float
        """
        return float(self.query("IL?"))
    
    def setMaxVoltage(self, voltage):
        """
        Sets the maximum voltage the load will allow
        
        :param voltage: Voltage in Volts
        :type voltage: float
        """
        return self.write("VL %s" % str(voltage))
    
    def getMaxVoltage(self):
        """
        Gets the maximum voltage the load will allow
        
        :returns: float
        """
        return float(self.query("VL?"))
    
    def setMaxPower(self, power):
        """
        Sets the maximum power the load will allow
        
        :param power: Power in Watts
        :type power: float
        """
        self.write("PL %s" % str(power))
    
    def getMaxPower(self):
        """
        Gets the maximum power the load will allow
        
        :returns: float
        """
        return float(self.query("PL?"))
    
    def setCurrent(self, current):
        """
        Sets the constant current mode's current level
        
        :param current: Current in Amps
        :type current: float
        """
        self.write("CI %s" % str(current))
    
    def getCurrent(self):
        """
        Gets the constant current mode's current level
        
        :returns: float
        """
        return float(self.query("CI?"))
    
    def setVoltage(self, voltage):
        """
        Sets the constant voltage mode's voltage level
        
        :param voltage: Voltage in Volts
        :type voltage: float
        """
        self.write("CV %s" % str(voltage))
    
    def getVoltage(self):
        """
        Gets the constant voltage mode's voltage level
        
        :returns: float
        """
        return float(self.query("CV?"))
    
    def setPower(self, power):
        """
        Sets the constant power mode's power level
        
        :param power: Power in Watts
        :type power: float
        """
        self.write("CP %s" % str(power))
    
    def getPower(self):
        """
        Gets the constant power mode's power level
        
        :returns: float
        """
        return float(self.query("CP?"))
    
    def setResistance(self, resistance):
        """
        Sets the constant resistance mode's resistance level
        
        :param resistance: Resistance in Ohms
        :type resistance: str
        """
        self.write("CR %s" % str(resistance))
    
    def getResistance(self):
        """
        Gets the constant resistance mode's resistance level
        
        :returns: float
        """
        return float(self.query("CR?"))
    
    def configureSlewRate(self, rate):
        """
        Set the slew rate for a zero to full-scale transision.
        
        :param rate: Rise and Fall time (in microseconds)
        :type rate: float
        """
        if rate > 10.0 and rate <= 4000.0:
            self.write("SF")
        elif rate > 4000.0:
            self.write("SS")
        self.write("SR %s" % str(rate))
    
    def configurePulsing(self, freq, duty, mode, base, peak):
        """
        Mode can be one of:
        
          * `cc`: Constant Current
          * `cv`: Constant Voltage
          * `cw`: Constant Power
          * `cr`: Constant Resistance
        """
        if mode.lower() == 'cc':
            self.write("I1 %s" % base)
            self.write("I2 %s" % peak)
        elif mode.lower() == 'cv':
            self.write("V1 %s" % base)
            self.write("V2 %s" % peak)
        elif mode.lower() == 'cw':
            self.write("P1 %s" % base)
            self.write("P2 %s" % peak)
        elif mode.lower() == 'cr':
            self.write("R1 %s" % base)
            self.write("R2 %s" % peak)
        else:
            raise Exception("Invalid mode")
        # Frequency
        self.write("FQ %s" % float(freq))
        
        # Duty
        self.write("DU %s" % float(duty))
        
        # Enable pulsing
        self.write("SW ON")
        
    def enableLocalControl(self):
        """
        Enable local control of the load
        """
        self.write("LOCK OFF")
    
    def disableLocalControl(self):
        """
        Disable local control of the load. User will be unable to control load
        functions using the front panel.
        """
        self.write("LOCK ON")
        
    def getTerminalVoltage(self):
        """
        Returns the terminal voltage in Volts
        
        :returns: float
        """
        return float(self.query("V?"))
    
    def getTerminalCurrent(self):
        """
        Returns the terminal current in Amps
        
        :returns: float
        """
        return float(self.query("I?"))
    
    def getTerminalPower(self):
        """
        Returns the terminal power in Watts
        
        :returns: float
        """
        return float(self.query("P?"))
    