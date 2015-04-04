"""
.. codeauthor:: Kevin Kennedy <kennedy.kevin@gmail.com>

Driver
------

The XLN Series DC Sources use a Silicon Labs `CP210x USB to UART Bridge` instead
of the USB Test and Measurement profile. This requires a third party driver
that must be downloaded from the BK Precision website before connecting the
device.

Remote Interface
----------------

The XLN series DC sources feature a remote web interface using the Ethernet
connection, that can be accessed by typing in the instrument IP address into a
Java-enabled web browser.

.. note:

   The default admin password is 123456 

API
---
"""
from Base_Driver import Base_Driver

class m_XLN(Base_Driver):
    """
    Driver for BK Precision XLN Series DC Sources
    """
    
    info = {
        # Model revision author
        'author':               'KKENNEDY',
        # Model version
        'version':              '1.0',
        # Revision date of Model version
        'date':                 '2015-03-24',
        # Device Manufacturer
        'deviceVendor':         'BK Precision',
        # List of compatible device models
        'deviceModel':          ['XLN3640', 'XLN6024', 'XLN8018', 'XLN10014',
                                 'XLN15010', 'XLN30052', 'XLN60026'],
        # Device type    
        'deviceType':           'DC Power Supply',      
        
        # List of compatible resource types
        'validResourceTypes':   ['VISA'],  
        
        #=======================================================================
        # VISA Attributes        
        #=======================================================================
        # Compatible VISA Manufacturers
        'VISA_compatibleManufacturers': ['B&K Precision', 'B&K PRECISION'],
        # Compatible VISA Models
        'VISA_compatibleModels':        ['XLN3640', 'XLN6024', 'XLN8018', 
                                         'XLN10014', 'XLN15010', 'XLN30052', 
                                         'XLN60026']
    }
    
    def _onLoad(self):
        self.instr = self.getResource()
        self.instr.open()
        
        self.instr.configure(baudrate=57600,
                             bytesize=8,
                             parity='N',
                             stopbits=1)
        
        self.setRemoteControl()
        
        self.instr.identify()
    
    def _onUnload(self):
        self.instr.close()
    
    def getProperties(self):
        prop = Base_Driver.getProperties(self)
        
        prop['protectionModes'] = ['Voltage', 'Current', 'Power']
        prop['terminalSense'] = ['Voltage', 'Current', 'Power']
        
        return prop
    
    def setRemoteControl(self):
        """
        Enable Remote Control Mode
        """
        self.instr.write("SYS:REM USB")
        
    def disableFrontPanel(self):
        """
        Disables the front panel of the instrument. To re-enable the front
        panel, call `enableFrontPanel`
        """
        self.instr.write("SYS:KEY:LOCK 1")
        
    def enableFrontPanel(self):
        """
        Enables the front panel of the instrument. 
        """
        self.instr.write("SYS:KEY:LOCK 0")
    
    def powerOn(self):
        """
        Enables the instrument to power the output
        """
        self.instr.write("OUT ON")
        
    def powerOff(self):
        """
        Disables the output power connections.
        """
        self.instr.write("OUT OFF")
        
    def getError(self):
        """
        Read any pending error codes with accompanying information
        
        :returns: str
        """
        return self.instr.query("SYS:ERR?")
        
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
    
    def setMaxVoltage(self, voltage):
        """
        Set the voltage limit
        
        :param voltage: Voltage (in Volts)
        :type voltage: float
        """
        self.instr.write("OUT:LIM:VOLT %f" % float(voltage))
        
    def getMaxVoltage(self):
        """
        Get the voltage limit
        
        :returns: float
        """
        return float(self.instr.query("OUT:LIM:VOLT?"))
        
    def setSlewRate(self, voltage, current):
        """
        Set the voltage and current rise/fall time of the power supply. Units are 
        seconds.
        
        :param voltage: Voltage Slew rate (in seconds)
        :type voltage: float
        :param current: Current Slew rate (in seconds)
        :type current: float
        """
        self.instr.write("OUT:SR:VOLT %f" % float(voltage))
        self.instr.write("OUT:SR:CURR %f" % float(current))
    
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
    
    def setMaxCurrent(self, current):
        """
        Set the current limit
        
        :param current: Current (in Amps)
        :type current: float
        """
        self.instr.write("OUT:LIM:CURR %f" % float(current))
        
    def getTerminalVoltage(self):
        """
        Get the measured voltage from the terminals of the instrument
        
        :returns: float
        """
        return float(self.instr.query("MEAS:VOLT?"))
        
    def getTerminalCurrent(self):
        """
        Get the measured current from the terminals of the instrument
        
        :returns: float
        """
        return float(self.instr.query("MEAS:CURR?"))
    
    def getTerminalPower(self):
        """
        Get the measured power from the terminals of the instrument
        
        :returns: float
        """
        return float(self.instr.query("MEAS:POW?"))
    
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
        
    def setProtection(self, voltage=None, current=None, power=None):
        """
        Enable the protection circuitry. If any of the parameters is zero, that
        protection is disabled.
        
        :param voltage: OVP Setting (in Volts)
        :type voltage: float
        :param current: OCP Setting (in Amps)
        :type current: float
        :param power: OPP Setting (in Watts)
        :type power: float
        """
        # Voltage
        if voltage is not None:
            if voltage > 0.0:
                self.instr.write("PROT:OVP:LEV %f" % float(voltage))
                self.instr.write("PROT:OVP 1")
            else:
                self.instr.write("PROT:OVP 0")
        
        # Current
        if current is not None:
            if current > 0.0:
                self.instr.write("PROT:OCP:LEV %f" % float(current))
                self.instr.write("PROT:OCP 1")
            else:
                self.instr.write("PROT:OCP 0")
            
        # Power
        if power is not None:
            if power > 0.0:
                self.instr.write("PROT:OPP:LEV %f" % float(power))
                self.instr.write("PROT:OPP 1")
            else:
                self.instr.write("PROT:OPP 0")
                
    def getProtection(self):
        """
        Get the protection set points
        
        :returns: dict with keys ['Voltage', 'Current', 'Power']
        """
        ret = {}
        
        ret['Voltage'] = self.instr.query('PROT:OVP:LEV?')
        ret['Current'] = self.instr.query('PROT:OCP:LEV?')
        ret['Power']   = self.instr.query('PROT:OPP:LEV?')
        
        return ret
        
    def disableProtection(self):
        """
        Disable the protection circuitry.
        """
        self.instr.write("PROT:OVP 0")
        self.instr.write("PROT:OCP 0")
        self.instr.write("PROT:OPP 0")
        
    def getProtectionState(self):
        """
        This command is used to query the executing state of the protection
        circuitry. If 1, this indicates the protection circuit has been 
        triggered and must be cleared using `clearProtection` before normal 
        operation can continue.
        
        :returns: int
        """
        return int(self.instr.query("PROT?"))
        
    def clearProtection(self):
        """
        This command is used to clear the protection state.
        Before sending this command, please increase the upper limitation of
        OVP/OCP or reduce the output voltage/current
        """
        self.instr.write("PROT:CLE")
    
    