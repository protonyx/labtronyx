from Base_Driver import Base_Driver

class m_911X(Base_Driver):
    
    info = {
        # Model revision author
        'author':               'KKENNEDY',
        # Model version
        'version':              '1.0',
        # Revision date of Model version
        'date':                 '2015-01-31',
        # Device Manufacturer
        'deviceVendor':         'BK Precision',
        # List of compatible device models
        'deviceModel':          ['9115', '9116'],
        # Device type    
        'deviceType':           'Power Supply',      
        
        # List of compatible resource types
        'validResourceTypes':   ['VISA'],  
        
        #=======================================================================
        # VISA Attributes        
        #=======================================================================
        # Compatible VISA Manufacturers
        'VISA_compatibleManufacturers': ['BK Precision'],
        # Compatible VISA Models
        'VISA_compatibleModels':        ['BK9115', 'BK9116']
    }
    
    def _onLoad(self):
        self.instr = self.getResource()
        
        self.setRemoteControl()
    
    def _onUnload(self):
        self.setLocalControl()
    
    def setRemoteControl(self):
        self.instr.write("SYST:REM")
        
    def setLocalControl(self):
        self.instr.write("SYST:LOC")
        
    def disableFrontPanel(self):
        """
        Disables the front panel of the instrument. To re-enable the front
        panel, call `setLocalControl`
        """
        self.instr.write("SYST:RWL")
    
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
        
    def getError(self):
        """
        Read any pending error codes with accompanying information
        
        :returns: str
        """
        return self.instr.query("SYST:ERR?")
        
    def trigger(self):
        """
        Create a trigger signal for the instrument. This command has no effect
        if the instrument is not using `BUS` as the trigger source.
        """
        self.instr.write("*TRG")
        
    def setTriggerSource(self, source):
        """
        Set the trigger source for the instrument. Manual trigger requires
        pressing the `Trigger` button on the front panel. Bus trigger requires
        a trigger command to be sent.
          
        :param source: Trigger Source ("BUS" or "MANUAL")
        :type source: str
        """
        self.instr.write("TRIG:SOUR %s" % str(source))
        
    def setVoltage(self, voltage):
        """
        Set the output voltage level
        
        :param voltage: Voltage (in Volts)
        :type voltage: float
        """
        self.instr.write("VOLT %f" % float(voltage))
        
    def getVoltage(self):
        """
        Get the output voltage level
        
        :returns: float
        """
        return float(self.instr.query("VOLT?"))
        
    def setTriggeredVoltage(self, voltage):
        """
        Set the programmed output voltage level after a trigger has occurred.
        
        :param voltage: Voltage (in Volts)
        :type voltage: float
        """
        self.instr.write("VOLT:TRIG %f" % float(voltage))
        
    def getTriggeredVoltage(self):
        """
        Get the programmed output voltage level after a trigger has occurred.
        
        :returns: float
        """
        return float(self.instr.query("VOLT:TRIG?"))
    
    def setVoltageSlewRate(self, rise, fall):
        """
        Set the voltage rising and falling time of the power supply. Units are 
        seconds.
        
        :param rise: Rise time (in seconds)
        :type rise: float
        :param fall: Fall time (in seconds)
        :type fall: float
        """
        self.instr.write("RISE %f" % float(rise))
        self.instr.write("FALL %f" % float(fall))
        
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
    
    def setTriggeredCurrent(self, current):
        """
        Set the programmed output current level after a trigger has occurred.
        
        :param current: Current (in Amps)
        :type current: float
        """
        self.instr.write("CURR:TRIG %f" % float(current))
    
    def getTriggeredCurrent(self):
        """
        Get the programmed output current level after a trigger has occurred.
        
        :returns: float
        """
        return float(self.instr.query("CURR:TRIG?"))
        
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
    
    def setVoltageRange(self, lower, upper):
        """
        Set the lower and upper limitation of the output voltage
        
        :param lower: Lower limit (in Volts)
        :type lower: float
        :param upper: Upper limit (in Volts)
        :type upper: float
        """
        self.instr.write("VOLT:LIM %f" % float(lower))
        self.instr.write("VOLT:RANG %f" % float(upper))
        
    def enableOVP(self, voltage, delay):
        """
        Enable the OVP (Over-Voltage Protection) circuitry. `delay` can be used
        to set the delay (in seconds) before the OVP kicks in.
        
        :param voltage: OVP Setting (in Volts)
        :type voltage: float
        :param delay: OVP delay (in seconds)
        :type delay: float
        """
        self.instr.write("VOLT:PROT %f" % float(voltage))
        self.instr.write("VOLT:PROT:DELAY %f" % float(delay))
        self.instr.write("VOLT:PROT:STAT ON")
        
    def disableOVP(self):
        """
        Disable the OVP (Over-Voltage Protection) circuitry.
        """
        self.instr.write("VOLT:PROT:STAT OFF")
        
    def getOVPState(self):
        """
        This command is used to query the executing state of OVP (Over-Voltage
        Protection). If 1, this indicates the OVP circuit has been triggered
        and must be cleared using `clearOVP` before normal operation can
        continue.
        
        :returns: int
        """
        return int(self.instr.query("VOLT:PROT:TRIG?"))
        
    def clearOVP(self):
        """
        This command is used to clear the OVP (Over-Voltage Protection) state.
        Before sending this command, please increase the upper limitation of
        OVP or reduce the output voltage
        """
        self.instr.write("PROT:CLE")
    
    