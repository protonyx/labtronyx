"""
.. codeauthor:: Kevin Kennedy <protonyx@users.noreply.github.com>

Driver
------

The BK Precision 9110 Series DC Power Sources use the default USB Test and
Measurement driver and should be recognized without problems when plugged in.
If the device is not recognized, it is likely because there is a problem with
the VISA driver installation.

The XLN Series DC Sources use a Silicon Labs `CP210x USB to UART Bridge`. This
requires a third party driver that must be downloaded from the BK Precision
website before connecting the device.

That driver can be downloaded from
`here <https://bkpmedia.s3.amazonaws.com/downloads/software/CP210X_USB_Driver.zip>`_

Remote Interface
----------------

The XLN series DC sources feature a remote web interface using the Ethernet
connection, that can be accessed by typing in the instrument IP address into a
Java-enabled web browser.

.. note:

   The default admin password is 123456
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


class d_911X(Base_Driver):
    """
    Driver for BK Precision 9110 Series DC Power Sources
    """
    
    info = {
        # Device Manufacturer
        'deviceVendor':         'BK Precision',
        # List of compatible device models
        'deviceModel':          ['9115', '9116'],
        # Device type    
        'deviceType':           'DC Power Supply',      
        
        # List of compatible resource types
        'validResourceTypes':   ['VISA']
    }

    @classmethod
    def VISA_validResource(cls, identity):
        vendors = ['BK Precision', 'BK PRECISION']
        models = ['BK9115', 'BK9116']
        return identity[0] in vendors and identity[1] in models
    
    def open(self):
        self.setRemoteControl()
    
    def close(self):
        self.setLocalControl()
        
    def getProperties(self):
        prop = Base_Driver.getProperties(self)
        
        prop['protectionModes'] = ['Voltage']
        prop['terminalSense'] = ['Voltage', 'Current', 'Power']
        prop['controlModes'] = ['Voltage', 'Current']
        
        return prop
    
    def setRemoteControl(self):
        """
        Sets the instrument in remote control mode
        """
        self.instr.write("SYST:REM")
        
    def setLocalControl(self):
        """
        Sets the instrument in local control mode
        """
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
        
        Parameters must be between 0 - 65.535 seconds
        
        note::
        
           This command is not supported by the device
        
        :param rise: Rise time (in seconds)
        :type rise: float
        :param fall: Fall time (in seconds)
        :type fall: float
        """
        # TODO: This doesn't work
        self.instr.write("RISE %f" % float(rise))
        self.instr.write("FALL %f" % float(fall))
        
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
        
    def setProtection(self, voltage=None):
        """
        Enable the protection circuitry. If any of the parameters is zero, that
        protection is disabled.
        
        :param voltage: OVP Setting (in Volts)
        :type voltage: float
        """
        # Voltage
        if voltage is not None:
            self.instr.write("VOLT:PROT:STAT ON")
            self.instr.write("VOLT:PROT %f" % float(voltage))
            
        else:
            self.instr.write("VOLT:PROT:STAT OFF")
            
    def getProtection(self):
        """
        Get the protection set points
        
        :returns: dict with keys ['Voltage']
        """
        ret = {}
        
        ret['Voltage'] = self.instr.query('VOLT:PROT?')
        
        return ret
            
    def setProtectionDelay(self, delay):
        """
        Set the OVP (Over-Voltage Protection) circuitry delay. Can be used
        to set the delay (in seconds) before the OVP kicks in.
        
        Delay must be between 0.001 - 0.6
        
        :param delay: OVP delay (in seconds)
        :type delay: float
        """
        if delay >= 0.001 and delay < 0.6:
            self.instr.write("VOLT:PROT:DELAY %f" % float(delay))
            
        else:
            ValueError("Value not in range")
    
    def getProtectionState(self):
        """
        This command is used to query the executing state of OVP (Over-Voltage
        Protection). If 1, this indicates the OVP circuit has been triggered
        and must be cleared using `clearProtectionState` before normal operation 
        can continue.
        
        note..
        
           This operation is not supported by the device
        
        :returns: int
        """
        # TODO: This doesn't work
        return int(self.instr.query("VOLT:PROT:TRIG?"))
        
    def clearProtectionState(self):
        """
        This command is used to clear the OVP (Over-Voltage Protection) state.
        Before sending this command, please increase the upper limitation of
        OVP or reduce the output voltage
        """
        self.instr.write("PROT:CLE")


class d_XLN(Base_Driver):
    """
    Driver for BK Precision XLN Series DC Sources
    """

    info = {
        # Device Manufacturer
        'deviceVendor':         'BK Precision',
        # List of compatible device models
        'deviceModel':          ['XLN3640', 'XLN6024', 'XLN8018', 'XLN10014',
                                 'XLN15010', 'XLN30052', 'XLN60026'],
        # Device type
        'deviceType':           'DC Power Supply',

        # List of compatible resource types
        'validResourceTypes':   ['VISA']
    }

    @classmethod
    def VISA_validResource(cls, identity):
        vendors = ['B&K Precision', 'B&K PRECISION']
        return identity[0] in vendors and identity[1] in cls.info['deviceModel']

    def open(self):
        self.configure(baudrate=57600,
                             bytesize=8,
                             parity='N',
                             stopbits=1)

        self.setRemoteControl()

        self.identify()

    def close(self):
        pass

    def getProperties(self):
        return {
            'protectionModes': ['Voltage', 'Current', 'Power'],
            'terminalSense':   ['Voltage', 'Current', 'Power']
        }

    def setRemoteControl(self):
        """
        Enable Remote Control Mode
        """
        self.write("SYS:REM USB")

    def disableFrontPanel(self):
        """
        Disables the front panel of the instrument. To re-enable the front
        panel, call `enableFrontPanel`
        """
        self.write("SYS:KEY:LOCK 1")

    def enableFrontPanel(self):
        """
        Enables the front panel of the instrument.
        """
        self.write("SYS:KEY:LOCK 0")

    def powerOn(self):
        """
        Enables the instrument to power the output
        """
        self.write("OUT ON")

    def powerOff(self):
        """
        Disables the output power connections.
        """
        self.write("OUT OFF")

    def getError(self):
        """
        Read any pending error codes with accompanying information

        :returns: str
        """
        return self.query("SYS:ERR?")

    def setVoltage(self, voltage):
        """
        Set the output voltage level

        :param voltage: Voltage (in Volts)
        :type voltage: float
        """
        self.write("VOLT %f" % float(voltage))

    def getVoltage(self):
        """
        Get the output voltage level

        :returns: float
        """
        return float(self.query("VOLT?"))

    def setMaxVoltage(self, voltage):
        """
        Set the voltage limit

        :param voltage: Voltage (in Volts)
        :type voltage: float
        """
        self.write("OUT:LIM:VOLT %f" % float(voltage))

    def getMaxVoltage(self):
        """
        Get the voltage limit

        :returns: float
        """
        return float(self.query("OUT:LIM:VOLT?"))

    def setSlewRate(self, voltage, current):
        """
        Set the voltage and current rise/fall time of the power supply. Units are
        seconds.

        :param voltage: Voltage Slew rate (in seconds)
        :type voltage: float
        :param current: Current Slew rate (in seconds)
        :type current: float
        """
        self.write("OUT:SR:VOLT %f" % float(voltage))
        self.write("OUT:SR:CURR %f" % float(current))

    def setCurrent(self, current):
        """
        Set the output current level

        :param current: Current (in Amps)
        :type current: float
        """
        self.write("CURR %f" % float(current))

    def getCurrent(self):
        """
        Get the output current level

        :returns: float
        """
        return float(self.query("CURR?"))

    def setMaxCurrent(self, current):
        """
        Set the current limit

        :param current: Current (in Amps)
        :type current: float
        """
        self.write("OUT:LIM:CURR %f" % float(current))

    def getTerminalVoltage(self):
        """
        Get the measured voltage from the terminals of the instrument

        :returns: float
        """
        return float(self.query("MEAS:VOLT?"))

    def getTerminalCurrent(self):
        """
        Get the measured current from the terminals of the instrument

        :returns: float
        """
        return float(self.query("MEAS:CURR?"))

    def getTerminalPower(self):
        """
        Get the measured power from the terminals of the instrument

        :returns: float
        """
        return float(self.query("MEAS:POW?"))

    def setVoltageRange(self, lower, upper):
        """
        Set the lower and upper limitation of the output voltage

        :param lower: Lower limit (in Volts)
        :type lower: float
        :param upper: Upper limit (in Volts)
        :type upper: float
        """
        self.write("VOLT:LIM %f" % float(lower))
        self.write("VOLT:RANG %f" % float(upper))

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
                self.write("PROT:OVP:LEV %f" % float(voltage))
                self.write("PROT:OVP 1")
            else:
                self.write("PROT:OVP 0")

        # Current
        if current is not None:
            if current > 0.0:
                self.write("PROT:OCP:LEV %f" % float(current))
                self.write("PROT:OCP 1")
            else:
                self.write("PROT:OCP 0")

        # Power
        if power is not None:
            if power > 0.0:
                self.write("PROT:OPP:LEV %f" % float(power))
                self.write("PROT:OPP 1")
            else:
                self.write("PROT:OPP 0")

    def getProtection(self):
        """
        Get the protection set points

        :returns: dict with keys ['Voltage', 'Current', 'Power']
        """
        ret = {}

        ret['Voltage'] = self.query('PROT:OVP:LEV?')
        ret['Current'] = self.query('PROT:OCP:LEV?')
        ret['Power']   = self.query('PROT:OPP:LEV?')

        return ret

    def disableProtection(self):
        """
        Disable the protection circuitry.
        """
        self.write("PROT:OVP 0")
        self.write("PROT:OCP 0")
        self.write("PROT:OPP 0")

    def getProtectionState(self):
        """
        This command is used to query the executing state of the protection
        circuitry. If 1, this indicates the protection circuit has been
        triggered and must be cleared using `clearProtection` before normal
        operation can continue.

        :returns: int
        """
        return int(self.query("PROT?"))

    def clearProtection(self):
        """
        This command is used to clear the protection state.
        Before sending this command, please increase the upper limitation of
        OVP/OCP or reduce the output voltage/current
        """
        self.write("PROT:CLE")


    