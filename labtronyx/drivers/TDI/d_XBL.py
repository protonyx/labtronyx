"""
.. codeauthor:: Kevin Kennedy <protonyx@users.noreply.github.com>

Remote Interface
----------------

These loads feature a Ethernet connection that hosts a web-based interface from
which you can control the load much like you would if you were sitting in front
of it.

"""
from labtronyx.bases import Base_Driver
from labtronyx.common.errors import *

class d_XBL(Base_Driver):
    """
    Driver for TDI XBL Series DC Electronic Loads
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
    
    def _onLoad(self):
        self.instr = self.getResource()
        
        # Turn off text mode (mangles queries)
        self.instr.write("TEXT OFF")
        
        # Turn off keyboard sounds
        self.instr.write("KEYOFF")
    
    def _onUnload(self):
        pass
        
    def getProperties(self):
        ret = Base_Driver.getProperties(self)
        
        ret['deviceVendor'] = 'TDI'
        
        ret['deviceModel'] = self.instr.query("MDL?")
        ret['deviceSerial'] = self.instr.query("SERNO?")
        ret['deviceFirmware'] = self.instr.query("VER?")
            
        return ret
    
    def powerOn(self):
        """
        Turns the load on
        """
        self.instr.write("LOAD ON")
    
    def powerOff(self):
        """
        Turns the load off
        """
        self.instr.write("LOAD OFF")
        
    def SetMaster(self):
        """
        Set load into master mode
        """
        self.instr.write("MASTER")
        
    def SetSlave(self):
        """
        Set load into slave mode
        """
        self.instr.write("SLAVE")
    
    def SetMaxCurrent(self, current):
        """
        Sets the maximum current the load will sink
        
        :param current: Current in Amps
        :type current: float
        """
        self.instr.write("IL %s" % str(current))
    
    def GetMaxCurrent(self):
        """
        Returns the maximum current the load will sink
        
        :returns: float
        """
        return float(self.instr.query("IL?"))
    
    def SetMaxVoltage(self, voltage):
        """
        Sets the maximum voltage the load will allow
        
        :param voltage: Voltage in Volts
        :type voltage: float
        """
        return self.instr.write("VL %s" % str(voltage))
    
    def GetMaxVoltage(self):
        """
        Gets the maximum voltage the load will allow
        
        :returns: float
        """
        return float(self.instr.query("VL?"))
    
    def SetMaxPower(self, power):
        """
        Sets the maximum power the load will allow
        
        :param power: Power in Watts
        :type power: float
        """
        self.instr.write("PL %s" % str(power))
    
    def GetMaxPower(self):
        """
        Gets the maximum power the load will allow
        
        :returns: float
        """
        return float(self.instr.query("PL?"))
    
    def SetCurrent(self, current):
        """
        Sets the constant current mode's current level
        
        :param current: Current in Amps
        :type current: float
        """
        self.instr.write("CI %s" % str(current))
    
    def GetCurrent(self):
        """
        Gets the constant current mode's current level
        
        :returns: float
        """
        return float(self.instr.query("CI?"))
    
    def SetVoltage(self, voltage):
        """
        Sets the constant voltage mode's voltage level
        
        :param voltage: Voltage in Volts
        :type voltage: float
        """
        self.instr.write("CV %s" % str(voltage))
    
    def GetVoltage(self):
        """
        Gets the constant voltage mode's voltage level
        
        :returns: float
        """
        return float(self.instr.query("CV?"))
    
    def SetPower(self, power):
        """
        Sets the constant power mode's power level
        
        :param power: Power in Watts
        :type power: float
        """
        self.instr.write("CP %s" % str(power))
    
    def GetPower(self):
        """
        Gets the constant power mode's power level
        
        :returns: float
        """
        return float(self.instr.query("CP?"))
    
    def SetResistance(self, resistance):
        """
        Sets the constant resistance mode's resistance level
        
        :param resistance: Resistance in Ohms
        :type resistance: str
        """
        self.instr.write("CR %s" % str(resistance))
    
    def GetResistance(self):
        """
        Gets the constant resistance mode's resistance level
        
        :returns: float
        """
        return float(self.instr.query("CR?"))
    
    def ConfigureSlewRate(self, rate):
        """
        Set the slew rate for a zero to full-scale transision.
        
        :param rate: Rise and Fall time (in microseconds)
        :type rate: float
        """
        if rate > 10.0 and rate <= 4000.0:
            self.instr.write("SF")
        elif rate > 4000.0:
            self.instr.write("SS")
        self.instr.write("SR %s" % str(rising))
    
    def ConfigurePulsing(self, freq, duty, mode, base, peak):
        """
        Mode can be one of:
        
          * `cc`: Constant Current
          * `cv`: Constant Voltage
          * `cw`: Constant Power
          * `cr`: Constant Resistance
        """
        if mode.lower() == 'cc':
            self.instr.write("I1 %s" % base)
            self.instr.write("I2 %s" % peak)
        elif mode.lower() == 'cv':
            self.instr.write("V1 %s" % base)
            self.instr.write("V2 %s" % peak)
        elif mode.lower() == 'cw':
            self.instr.write("P1 %s" % base)
            self.instr.write("P2 %s" % peak)
        elif mode.lower() == 'cr':
            self.instr.write("R1 %s" % base)
            self.instr.write("R2 %s" % peak)
        else:
            raise Exception("Invalid mode")
        # Frequency
        self.instr.write("FQ %s" % float(freq))
        
        # Duty
        self.instr.write("DU %s" % float(duty))
        
        # Enable pulsing
        self.instr.write("SW ON")
        
    def EnableLocalControl(self):
        """
        Enable local control of the load
        """
        self.instr.write("LOCK OFF")
    
    def DisableLocalControl(self):
        """
        Disable local control of the load. User will be unable to control load
        functions using the front panel.
        """
        self.instr.write("LOCK ON")
        
    def GetTerminalVoltage(self):
        """
        Returns the terminal voltage in Volts
        
        :returns: float
        """
        return float(self.instr.query("V?"))
    
    def GetTerminalCurrent(self):
        """
        Returns the terminal current in Amps
        
        :returns: float
        """
        return float(self.instr.query("I?"))
    
    def GetTerminalPower(self):
        """
        Returns the terminal power in Watts
        
        :returns: float
        """
        return float(self.instr.query("P?"))
    