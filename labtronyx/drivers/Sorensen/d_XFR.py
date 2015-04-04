"""
.. codeauthor:: Kevin Kennedy <kennedy.kevin@gmail.com>

API
---
"""
from Base_Driver import Base_Driver

class d_XFR(Base_Driver):
    """
    Driver for Sorensen XFR Series DC Power Supplies
    """
    
    info = {
        # Device Manufacturer
        'deviceVendor':         'Sorensen',
        # List of compatible device models
        'deviceModel':          ['XFR 600-4'],
        # Device type    
        'deviceType':           'DC Power Supply',      
        
        # List of compatible resource types
        'validResourceTypes':   ['VISA'],  
        
        #=======================================================================
        # VISA Attributes        
        #=======================================================================
        # Compatible VISA Manufacturers
        'VISA_compatibleManufacturers': ['Xantrex'],
        # Compatible VISA Models
        'VISA_compatibleModels':        ['XFR 600-4']
    }
    
    def _onLoad(self):
        self.instr = self.getResource()
        
        self.setRemoteControl()
    
    def _onUnload(self):
        pass
    
    def setRemoteControl(self):
        """
        Enable Remote Control Mode
        """
        self.instr.write("SYST:REM:STAT REM")
        self.instr.write("SYST:REM:PON:STAT OFF")
    
    def powerOn(self):
        """
        Enables the instrument to power the output
        """
        self.instr.write("OUTP ON")
        
    def powerOff(self):
        """
        Disables the output power connections.
        """
        self.instr.write("OUTP OFF")
        
    def trigger(self):
        """
        Trigger the instrument
        """
        self.instr.write("*TRG")
        
    def getError(self):
        """
        Read any pending error codes with accompanying information
        
        :returns: str
        """
        return self.instr.query("SYST:ERR?")
        
    def setVoltage(self, voltage):
        """
        Set the output voltage level
        
        :param voltage: Voltage (in Volts)
        :type voltage: float
        """
        self.instr.write("SOUR:VOLT %f" % float(voltage))
        
    def getVoltage(self):
        """
        Get the output voltage level
        
        :returns: float
        """
        return float(self.instr.query("SOUR:VOLT?"))
        
    def setVoltageSlewRate(self, step, interval):
        """
        Set the voltage slew rate as a function of change in the output voltage
        and a given time interval. The maximum slew rate is 1% rated 
        voltage/150us. The slew rate is saved upon power off and restored at 
        power on. Output ON/OFF and shutdown are not affected by the 
        programmable slew rate. These functions have a slew rate of 1%/20ms.
        
        The range of output voltage is 5% - 0.1% of rated voltage.
        The range of time interval is 1.5 s - 150 us.
        The negative slew rate is limited by the discharge rate of the output capacitors.

        During current share, slaves operate with their default slew rate. The 
        master operates at its programmed slew rate. Hence a programmable slew 
        rate for the system is achieved. However, this slew rate is limited by 
        the speed of the control loop. The slaves will return to their 
        programmed slew rate when they exit current share slave operation.

        The slew rate error increases as the slew rate increases.
        
        Example::
        
           Set a slew rate of 100V/10s. This slew rate is 1V/0.1s, which is
           within the acceptable range.
           
           >>> setVoltageSlewRate(1, 0.1)
           
        Note::
        
           Check both the voltage step and the interval to ensure that you get
           the required slew rate
        
        :param step: voltage-step (units of Volts)
        :type voltage: float
        :param current: time interval (seconds)
        :type current: float
        """
        self.instr.write(":VOLT:SLEW:STEP %f" % float(voltage))
        self.instr.write(":VOLT:SLEW:INT %f" % float(current))
        
    def getTerminalVoltage(self):
        """
        Get the measured voltage from the terminals of the instrument
        
        :returns: float
        """
        return float(self.instr.ask("MEAS:VOLT?"))
    
    def setCurrent(self, current):
        """
        Set the output current level
        
        :param current: Current (in Amps)
        :type current: float
        """
        self.instr.write("CURR %f" % float(current))
        
    def getCurrent(self):
        """
        Get the output current level
        
        :returns: float
        """
        return float(self.instr.query("CURR?"))
        
    def getTerminalCurrent(self):
        """
        Get the measured current from the terminals of the instrument
        
        :returns: float
        """
        return float(self.instr.ask("MEAS:CURR?"))
    
    def getTerminalPower(self):
        """
        Get the measured power from the terminals of the instrument
        
        :returns: float
        """
        return float(self.instr.ask("MEAS:POW?"))
        
    def setProtection(self, voltage=None, current=None):
        """
        Enable the protection circuitry. If any of the parameters is zero, that
        protection is disabled.
        
        :param voltage: OVP Setting (in Volts)
        :type voltage: float
        :param current: OCP Setting (in Amps)
        :type current: float
        """
        # Voltage
        if voltage is not None:
            self.instr.write("SOUR:VOLT:PROT %f" % float(voltage))
        
        # Current
        if current is not None:
            self.instr.write("SOUR:CURR:PROT %f" % float(current))
        
    def disableProtection(self):
        """
        Disable the protection circuitry.
        """
        self.setProtection(0, 0)
        
    def getProtectionState(self):
        """
        This command is used to query the executing state of the protection
        circuitry. If one of the states has tripped, the protection state can
        be reset by turning the output off and then back on.
        
        :returns: tuple (OVP, OCP)
        """
        ovp = int(self.instr.query("SOUR:VOLT:PROT:OVER:TRIP?"))
        ocp = int(self.instr.query("SOUR:CURR:PROT:OVER:TRIP?"))
        
        return (ovp, ocp)
    