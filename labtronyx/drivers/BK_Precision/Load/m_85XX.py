"""
.. codeauthor:: Kevin Kennedy <kennedy.kevin@gmail.com>

Connection Instructions
-----------------------

The BK Precision 8500 Series DC Loads must be connected to a PC through a
USB-to-Serial adapter. BK Precision also recommends using an RS-232-to-TTL
isolated pass-through to protect the serial interface on the instrument.

These devices also use a custom communication protocol that does not support
enumeration. In order to use the device, this driver must be loaded to the
proper serial port before use. Once the driver is loaded, the device will be
placed into `Remote Control` mode.

Driver
------

You may need to install a driver for the USB-to-Serial adapter. Follow the
instructions from the device vendor's website.

BK Precision provides a device for communicating with this class of DC load:
`IT-132 USB-to-Serial Adapter`. The driver for this device can be found
`here <https://bkpmedia.s3.amazonaws.com/downloads/software/ITE132_driver.zip>`_

API
---
"""
from Base_Driver import Base_Driver

class m_85XX(Base_Driver):
    """
    Driver for BK Precision 8500 Series DC Loads
    """
    
    info = {
        # Device Manufacturer
        'deviceVendor':         'BK Precision',
        # List of compatible device models
        'deviceModel':          ['8500', '8502', 
                                 '8510', '8512', '8514', '8518', 
                                 '8520', '8522', '8524', '8526'],
        # Device type    
        'deviceType':           'DC Electronic Load',      
        
        # List of compatible resource types
        'validResourceTypes':   ['Serial']
    }

    address = 0
    debug = 0  # Set to 1 to see dumps of commands and responses
    length_packet = 26  # Number of bytes in a packet
    convert_current = 1e4  # Convert current in A to 0.1 mA
    convert_voltage = 1e3  # Convert voltage in V to mV
    convert_power   = 1e3  # Convert power in W to mW
    convert_resistance = 1e3  # Convert resistance in ohm to mohm
    to_ms = 1000           # Converts seconds to ms
    # Number of settings storage registers
    lowest_register  = 1
    highest_register = 25
    # Values for setting modes of CC, CV, CW, or CR
    modes = {"cc":0, "cv":1, "cw":2, "cr":3}
    
    trigger_sources = {
        "IMMEDIATE":0, 
        "EXTERNAL":1, 
        "BUS":2}
    
    def _onLoad(self):
        self.instr = self.getResource()
        
        self.instr.open()
        
        # Configure the COM Port
        self.instr.configure(bytesize=8,
                             parity='N',
                             stopbits=1,
                             timeout=0.5)
        
        self.setRemoteControl()
    
    def _onUnload(self):
        self.setLocalControl()
        
        self.instr.close()
        
    def getProperties(self):
        prop = Base_Driver.getProperties(self)
        
        prop['deviceVendor'] = 'BK Precision'
        
        prodInfo = self._GetProductInformation()
        prop['deviceModel'] = prodInfo[0]
        prop['deviceSerial'] = prodInfo[1]
        prop['deviceFirmware'] = prodInfo[2]
        
        prop['validModes'] = self.modes
        prop['validTriggerSources'] = self.trigger_sources
        prop['controlModes'] = ['Voltage', 'Current', 'Power', 'Resistance']
        prop['terminalSense'] = ['Voltage', 'Current', 'Power']
            
        return prop
    
    def _CommandProperlyFormed(self, cmd):
        '''Return 1 if a command is properly formed; otherwise, return 0.
        '''
        commands = (
            0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29,
            0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x32, 0x33,
            0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D,
            0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47,
            0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F, 0x50, 0x51,
            0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x5B,
            0x5C, 0x5D, 0x5E, 0x5F, 0x60, 0x61, 0x62, 0x63, 0x64, 0x65,
            0x66, 0x67, 0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x12
        )
        # Must be proper length
        if len(cmd) != self.length_packet:
            out("Command length = " + str(len(cmd)) + "-- should be " + \
                str(self.length_packet) + nl)
            return 0
        # First character must be 0xaa
        if ord(cmd[0]) != 0xaa:
            out("First byte should be 0xaa" + nl)
            return 0
        # Second character (address) must not be 0xff
        if ord(cmd[1]) == 0xff:
            out("Second byte cannot be 0xff" + nl)
            return 0
        # Third character must be valid command
        byte3 = "%02X" % ord(cmd[2])
        if ord(cmd[2]) not in commands:
            out("Third byte not a valid command:  %s\n" % byte3)
            return 0
        # Calculate checksum and validate it
        checksum = self._CalculateChecksum(cmd)
        if checksum != ord(cmd[-1]):
            out("Incorrect checksum" + nl)
            return 0
        return 1
    
    def _CalculateChecksum(self, cmd):
        '''Return the sum of the bytes in cmd modulo 256.
        '''
        assert((len(cmd) == self.length_packet - 1) or (len(cmd) == self.length_packet))
        checksum = 0
        for i in xrange(self.length_packet - 1):
            checksum += ord(cmd[i])
        checksum %= 256
        return checksum
    
    def _StartCommand(self, byte):
        return chr(0xaa) + chr(self.address) + chr(byte)
    
    def _SendCommand(self, command):
        '''Sends the command to the serial stream and returns the 26 byte
        response.
        '''
        assert(len(command) == self.length_packet)
        
        self.instr.write_raw(command)
        response = self.instr.read_raw(self.length_packet)
        
        assert(len(response) == self.length_packet)
        return response
    
    def _ResponseStatus(self, response):
        '''Return a message string about what the response meant.  The
        empty string means the response was OK.
        '''
        responses = {
            0x90 : "Wrong checksum",
            0xA0 : "Incorrect parameter value",
            0xB0 : "Command cannot be carried out",
            0xC0 : "Invalid command",
            0x80 : "",
        }
        assert(len(response) == self.length_packet)
        assert(ord(response[2]) == 0x12)
        return responses[ord(response[3])]
    
    def _CodeInteger(self, value, num_bytes=4):
        '''Construct a little endian string for the indicated value.  Two
        and 4 byte integers are the only ones allowed.
        '''
        assert(num_bytes == 1 or num_bytes == 2 or num_bytes == 4)
        value = int(value)  # Make sure it's an integer
        s  = chr(value & 0xff)
        if num_bytes >= 2:
            s += chr((value & (0xff << 8)) >> 8)
            if num_bytes == 4:
                s += chr((value & (0xff << 16)) >> 16)
                s += chr((value & (0xff << 24)) >> 24)
                assert(len(s) == 4)
        return s
    
    def _DecodeInteger(self, str):
        '''Construct an integer from the little endian string. 1, 2, and 4 byte 
        strings are the only ones allowed.
        '''
        assert(len(str) == 1 or len(str) == 2 or len(str) == 4)
        n  = ord(str[0])
        if len(str) >= 2:
            n += (ord(str[1]) << 8)
            if len(str) == 4:
                n += (ord(str[2]) << 16)
                n += (ord(str[3]) << 24)
        return n
    
    def _GetReserved(self, num_used):
        '''Construct a string of nul characters of such length to pad a
        command to one less than the packet size (leaves room for the 
        checksum byte.
        '''
        num = self.length_packet - num_used - 1
        assert(num > 0)
        return chr(0)*num
    
    def _PrintCommandAndResponse(self, cmd, response, cmd_name):
        '''Print the command and its response if debugging is on.
        '''
        assert(cmd_name)
        if self.debug:
            out(cmd_name + " command:" + nl)
            self.DumpCommand(cmd)
            out(cmd_name + " response:" + nl)
            self.DumpCommand(response)
            
    def _GetCommand(self, command, value, num_bytes=4):
        '''Construct the command with an integer value of 0, 1, 2, or 
        4 bytes.
        '''
        cmd = self._StartCommand(command)
        if num_bytes > 0:
            r = num_bytes + 3
            cmd += self._CodeInteger(value)[:num_bytes] + self._Reserved(r)
        else:
            cmd += self._Reserved(0)
        cmd += chr(self._CalculateChecksum(cmd))
        assert(self._CommandProperlyFormed(cmd))
        return cmd
    
    def _GetData(self, data, num_bytes=4):
        '''Extract the little endian integer from the data and return it.
        '''
        assert(len(data) == self.length_packet)
        if num_bytes == 1:
            return ord(data[3])
        elif num_bytes == 2:
            return self._DecodeInteger(data[3:5])
        elif num_bytes == 4:
            return self._DecodeInteger(data[3:7])
        else:
            raise Exception("Bad number of bytes:  %d" % num_bytes)
        
    def _Reserved(self, num_used):
        assert(num_used >= 3 and num_used < self.length_packet - 1)
        return chr(0)*(self.length_packet - num_used - 1)
    
    def _SendIntegerToLoad(self, byte, value, msg, num_bytes=4):
        '''Send the indicated command along with value encoded as an integer
        of the specified size.  Return the instrument's response status.
        '''
        cmd = self._GetCommand(byte, int(value), num_bytes)
        response = self._SendCommand(cmd)
        self._PrintCommandAndResponse(cmd, response, msg)
        return self._ResponseStatus(response)
    
    def _GetIntegerFromLoad(self, cmd_byte, msg, num_bytes=4):
        '''Construct a command from the byte in cmd_byte, send it, get
        the response, then decode the response into an integer with the
        number of bytes in num_bytes.  msg is the debugging string for
        the printout.  Return the integer.
        '''
        assert(num_bytes == 1 or num_bytes == 2 or num_bytes == 4)
        cmd = self._StartCommand(cmd_byte)
        cmd += self._Reserved(3)
        cmd += chr(self._CalculateChecksum(cmd))
        assert(self._CommandProperlyFormed(cmd))
        response = self._SendCommand(cmd)
        self._PrintCommandAndResponse(cmd, response, msg)
        return self._DecodeInteger(response[3:3 + num_bytes])
    
    # Returns model number, serial number, and firmware version number
    def _GetProductInformation(self):
        """
        Returns model number, serial number, and firmware version
        """
        cmd = self._StartCommand(0x6A)
        cmd += self._Reserved(3)
        cmd += chr(self._CalculateChecksum(cmd))
        assert(self._CommandProperlyFormed(cmd))
        response = self._SendCommand(cmd)
        self._PrintCommandAndResponse(cmd, response, "Get product info")
        model = response[3:8]
        fw = hex(ord(response[9]))[2:] + "."
        fw += hex(ord(response[8]))[2:] 
        serial_number = response[10:20]
        
        return (str(model), str(serial_number), str(fw))
    
    def powerOn(self):
        """
        Turns the load on
        """
        msg = "Turn load on"
        on = 1
        return self._SendIntegerToLoad(0x21, on, msg, num_bytes=1)
    
    def powerOff(self):
        """
        Turns the load off
        """
        msg = "Turn load off"
        off = 0
        return self._SendIntegerToLoad(0x21, off, msg, num_bytes=1)
    
    def setRemoteControl(self):
        """
        Sets the load to remote control
        """
        msg = "Set remote control"
        remote = 1
        return self._SendIntegerToLoad(0x20, remote, msg, num_bytes=1)
    
    def setLocalControl(self):
        """
        Sets the load to local control
        """
        msg = "Set local control"
        local = 0
        return self._SendIntegerToLoad(0x20, local, msg, num_bytes=1)
    
    def setMaxCurrent(self, current):
        """
        Sets the maximum current the load will sink
        
        :param current: Current in Amps
        :type current: float
        """
        msg = "Set max current"
        return self._SendIntegerToLoad(0x24, current*self.convert_current, msg, num_bytes=4)
    
    def getMaxCurrent(self):
        """
        Returns the maximum current the load will sink
        
        :returns: float
        """
        msg = "Set max current"
        return self._GetIntegerFromLoad(0x25, msg, num_bytes=4)/self.convert_current
    
    def setMaxVoltage(self, voltage):
        """
        Sets the maximum voltage the load will allow
        
        :param voltage: Voltage in Volts
        :type voltage: float
        """
        msg = "Set max voltage"
        return self._SendIntegerToLoad(0x22, voltage*self.convert_voltage, msg, num_bytes=4)
    
    def getMaxVoltage(self):
        """
        Gets the maximum voltage the load will allow
        
        :returns: float
        """
        msg = "Get max voltage"
        return self._GetIntegerFromLoad(0x23, msg, num_bytes=4)/self.convert_voltage
    
    def setMaxPower(self, power):
        """
        Sets the maximum power the load will allow
        
        :param power: Power in Watts
        :type power: float
        """
        msg = "Set max power"
        return self._SendIntegerToLoad(0x26, power*self.convert_power, msg, num_bytes=4)
    
    def getMaxPower(self):
        """
        Gets the maximum power the load will allow
        
        :returns: float
        """
        msg = "Get max power"
        return self._GetIntegerFromLoad(0x27, msg, num_bytes=4)/self.convert_power
    
    def setMode(self, mode):
        """
        Sets the operating mode
        
        Possible values:
        
          * `cc`: Constant Current
          * `cv`: Constant Voltage
          * `cp`: Constant Power
          * `cr`: Constant Resistance
          
        :param mode: Operating mode
        :type mode: str
        :raises: Exception
        """
        if mode.lower() not in self.modes:
            raise Exception("Unknown mode")
        msg = "Set mode"
        return self._SendIntegerToLoad(0x28, self.modes[mode.lower()], msg, num_bytes=1)
    
    def getMode(self):
        """
        Gets the operating mode
        
        Possible values:
        
          * `cc`: Constant Current
          * `cv`: Constant Voltage
          * `cw`: Constant Power
          * `cr`: Constant Resistance
        
        :returns: str
        """
        msg = "Get mode"
        mode = self._GetIntegerFromLoad(0x29, msg, num_bytes=1)
        modes_inv = {0:"cc", 1:"cv", 2:"cw", 3:"cr"}
        return modes_inv[mode]
    
    def setCurrent(self, current):
        """
        Sets the constant current mode's current level
        
        :param current: Current in Amps
        :type current: float
        """
        msg = "Set CC current"
        return self._SendIntegerToLoad(0x2A, float(current)*self.convert_current, msg, num_bytes=4)
    
    def getCurrent(self):
        """
        Gets the constant current mode's current level
        
        :returns: float
        """
        msg = "Get CC current"
        return self._GetIntegerFromLoad(0x2B, msg, num_bytes=4)/self.convert_current
    
    def setVoltage(self, voltage):
        """
        Sets the constant voltage mode's voltage level
        
        :param voltage: Voltage in Volts
        :type voltage: float
        """
        msg = "Set CV voltage"
        return self._SendIntegerToLoad(0x2C, float(voltage)*self.convert_voltage, msg, num_bytes=4)
    
    def getVoltage(self):
        """
        Gets the constant voltage mode's voltage level
        
        :returns: float
        """
        msg = "Get CV voltage"
        return self._GetIntegerFromLoad(0x2D, msg, num_bytes=4)/self.convert_voltage
    
    def setPower(self, power):
        """
        Sets the constant power mode's power level
        
        :param power: Power in Watts
        :type power: float
        """
        msg = "Set CW power"
        return self._SendIntegerToLoad(0x2E, float(power)*self.convert_power, msg, num_bytes=4)
    
    def getPower(self):
        """
        Gets the constant power mode's power level
        
        :returns: float
        """
        msg = "Get CW power"
        return self._GetIntegerFromLoad(0x2F, msg, num_bytes=4)/self.convert_power
    
    def setResistance(self, resistance):
        """
        Sets the constant resistance mode's resistance level
        
        :param resistance: Resistance in Ohms
        :type resistance: str
        """
        msg = "Set CR resistance"
        return self._SendIntegerToLoad(0x30, float(resistance)*self.convert_resistance, msg, num_bytes=4)
    
    def getResistance(self):
        """
        Gets the constant resistance mode's resistance level
        
        :returns: float
        """
        msg = "Get CR resistance"
        return self._GetIntegerFromLoad(0x31, msg, num_bytes=4)/self.convert_resistance
    
    def setTransient(self, A, A_time_s, B, B_time_s, operation="continuous"):
        """
        Sets up the transient operation mode.  
        
        :param A: Amplitude B
        :type A: float
        :param A_time_s: Width of A (in seconds)
        :type A_time_s: float
        :param B: Amplitude of B
        :type B: float
        :param B: Width of B (in seconds)
        :type B_time_s: float
        :param operation: Transient Mode (one of "continuous", "pulse", "toggled")
        :type operation: str
        """
        if mode.lower() not in self.modes:
            raise Exception("Unknown mode")
        opcodes = {"cc":0x32, "cv":0x34, "cw":0x36, "cr":0x38}
        mode = self.GetMode()
        if mode.lower() == "cc":
            const = self.convert_current
        elif mode.lower() == "cv":
            const = self.convert_voltage
        elif mode.lower() == "cw":
            const = self.convert_power
        else:
            const = self.convert_resistance
        cmd = self._StartCommand(opcodes[mode.lower()])
        cmd += self._CodeInteger(A*const, num_bytes=4)
        cmd += self._CodeInteger(A_time_s*self.to_ms, num_bytes=2)
        cmd += self._CodeInteger(B*const, num_bytes=4)
        cmd += self._CodeInteger(B_time_s*self.to_ms, num_bytes=2)
        transient_operations = {"continuous":0, "pulse":1, "toggled":2}
        cmd += self._CodeInteger(transient_operations[operation.lower()], num_bytes=1)
        cmd += self._Reserved(16)
        cmd += chr(self._CalculateChecksum(cmd))
        assert(self._CommandProperlyFormed(cmd))
        response = self._SendCommand(cmd)
        self._PrintCommandAndResponse(cmd, response, "Set %s transient" % mode)
        return self._ResponseStatus(response)
    
    def getTransient(self, mode):
        """
        Gets the transient mode settings
        
        :returns: tuple (Amplitude A, Width A, Amplitude B, Width B, Mode)
        """
        if mode.lower() not in self.modes:
            raise Exception("Unknown mode")
        opcodes = {"cc":0x33, "cv":0x35, "cw":0x37, "cr":0x39}
        cmd = self._StartCommand(opcodes[mode.lower()])
        cmd += self._Reserved(3)
        cmd += chr(self._CalculateChecksum(cmd))
        assert(self._CommandProperlyFormed(cmd))
        response = self._SendCommand(cmd)
        self._PrintCommandAndResponse(cmd, response, "Get %s transient" % mode)
        A = self._DecodeInteger(response[3:7])
        A_timer_ms = self._DecodeInteger(response[7:9])
        B = self._DecodeInteger(response[9:13])
        B_timer_ms = self._DecodeInteger(response[13:15])
        operation = self._DecodeInteger(response[15])
        time_const = 1e3
        transient_operations_inv = {0:"continuous", 1:"pulse", 2:"toggled"}
        if mode.lower() == "cc":
            return (A/self.convert_current, A_timer_ms/time_const,
                    B/self.convert_current, B_timer_ms/time_const,
                    transient_operations_inv[operation])
        elif mode.lower() == "cv":
            return (A/self.convert_voltage, A_timer_ms/time_const,
                    B/self.convert_voltage, B_timer_ms/time_const,
                    transient_operations_inv[operation])
        elif mode.lower() == "cw":
            return (A/self.convert_power, A_timer_ms/time_const,
                    B/self.convert_power, B_timer_ms/time_const,
                    transient_operations_inv[operation])
        else:
            return (A/self.convert_resistance, A_timer_ms/time_const, 
                    B/self.convert_resistance, B_timer_ms/time_const,
                    transient_operations_inv[operation])
            
    def setBatteryTestVoltage(self, min_voltage):
        """
        Sets the battery test voltage
        
        :param min_voltage: Minimum Voltage (volts)
        :type min_voltage: float
        """
        msg = "Set battery test voltage"
        return self._SendIntegerToLoad(0x4E, min_voltage*self.convert_voltage, msg, num_bytes=4)
    
    def getBatteryTestVoltage(self):
        """
        Gets the battery test voltage
        
        :returns: float
        """
        msg = "Get battery test voltage"
        return self._GetIntegerFromLoad(0x4F, msg, num_bytes=4)/self.convert_voltage
    
    def setLoadOnTimer(self, time_in_s):
        """
        Sets the time in seconds that the load will be on
        
        :param time_in_s: Time (in seconds)
        :type time_in_s: int
        """
        msg = "Set load on timer"
        return self._SendIntegerToLoad(0x50, time_in_s, msg, num_bytes=2)
    
    def getLoadOnTimer(self):
        """
        Gets the time in seconds that the load will be on
        
        :returns: int
        """
        msg = "Get load on timer"
        return self._GetIntegerFromLoad(0x51, msg, num_bytes=2)
    
    def setLoadOnTimerState(self, enabled=0):
        """
        Enables or disables the LOAD ON timer state
        
        :param enabled: Timer State (0: Disabled, 1: Enabled)
        :type enabled: int
        """
        msg = "Set load on timer state"
        return self._SendIntegerToLoad(0x50, enabled, msg, num_bytes=1)
    
    def getLoadOnTimerState(self):
        """
        Gets the LOAD ON timer state
        
        :returns: int
        """
        msg = "Get load on timer"
        state = self._GetIntegerFromLoad(0x53, msg, num_bytes=1)
        return state
    
    def enableLocalControl(self):
        """
        Enable local control of the load
        """
        msg = "Enable local control"
        enabled = 1
        return self._SendIntegerToLoad(0x55, enabled, msg, num_bytes=1)
    
    def disableLocalControl(self):
        """
        Disable local control of the load. User will be unable to control load
        functions using the front panel.
        """
        msg = "Disable local control"
        disabled = 0
        return self._SendIntegerToLoad(0x55, disabled, msg, num_bytes=1)
    
    def enableRemoteSense(self, enabled=0):
        """
        Enable remote sensing
        """
        msg = "Set remote sense"
        return self._SendIntegerToLoad(0x56, 1, msg, num_bytes=1)
    
    def disableRemoteSense(self):
        """
        Disable remote sensing
        """
        msg = "Enable remote sense"
        return self._SendIntegerToLoad(0x56, 0, msg, num_bytes=1)
    
    def getRemoteSense(self):
        """
        Get the state of remote sensing
        
        :returns: int (0: Disabled, 1: Enabled)
        """
        msg = "Get remote sense"
        return self._GetIntegerFromLoad(0x57, msg, num_bytes=1)
    
    def setTriggerSource(self, source="IMMEDIATE"):
        """
        Set how the instrument will be triggered:
          
          * "IMMEDIATE" means triggered from the front panel.
          * "EXTERNAL" means triggered by a TTL signal on the rear panel.
          * "BUS" means a software trigger (see `Trigger()`).
        
        :param source: Source ("immediate", "external" or "bus")
        :type source: str
        :raises: ValueError
        """
        if source in self.trigger_sources:
            msg = "Set trigger type"
            return self._SendIntegerToLoad(0x54, self.trigger_sources.get(source), msg, num_bytes=1)
        else:
            raise ValueError("Trigger type %s not recognized" % source)
        
    
    def getTriggerSource(self):
        """
        Get how the instrument will be triggered
        
        :returns: str
        """
        msg = "Get trigger source"
        trig = self._GetIntegerFromLoad(0x59, msg, num_bytes=1)
        
        for key, value in self.trigger_sources.items():
            if trig == value:
                return key
            
        return 'Unknown'
    
    def trigger(self):
        """
        Provide a software trigger.  This is only of use when the trigger
        mode is set to "bus".
        """
        cmd = self._StartCommand(0x5A)
        cmd += self._Reserved(3)
        cmd += chr(self._CalculateChecksum(cmd))
        assert(self._CommandProperlyFormed(cmd))
        response = self._SendCommand(cmd)
        self._PrintCommandAndResponse(cmd, response, "Trigger load (trigger = bus)")
        return self._ResponseStatus(response)
    
    def saveSettings(self, register=0):
        "Save instrument settings to a register"
        assert(self.lowest_register <= register <= self.highest_register)
        msg = "Save to register %d" % register
        return self._SendIntegerToLoad(0x5B, register, msg, num_bytes=1)
    
    def recallSettings(self, register=0):
        "Restore instrument settings from a register"
        assert(self.lowest_register <= register <= self.highest_register)
        cmd = self._GetCommand(0x5C, register, num_bytes=1)
        response = self._SendCommand(cmd)
        self._PrintCommandAndResponse(cmd, response, "Recall register %d" % register)
        return self._ResponseStatus(response)
    
    def setFunction(self, function="fixed"):
        """
        Set the function (type of operation) of the load.
        
        :param function: Function ("fixed", "short", "transient", "list" or "battery")
        :type function: str
        """
        msg = "Set function to %s" % function
        functions = {"fixed":0, "short":1, "transient":2, "list":3, "battery":4}
        return self._SendIntegerToLoad(0x5D, functions[function], msg, num_bytes=1)
    
    def getFunction(self):
        """
        Get the function (type of operation) of the load
        
        :returns: str
        """
        msg = "Get function"
        fn = self._GetIntegerFromLoad(0x5E, msg, num_bytes=1)
        functions_inv = {0:"fixed", 1:"short", 2:"transient", 3:"list", 4:"battery"}
        return functions_inv[fn]
    
    def getInputValues(self):
        """
        Returns voltage in V, current in A, and power in W, op_state byte,
        and demand_state byte.
        
        :returns: list: [voltage, current, power, op_state, demand_state]
        """
        cmd = self._StartCommand(0x5F)
        cmd += self._Reserved(3)
        cmd += chr(self._CalculateChecksum(cmd))
        assert(self._CommandProperlyFormed(cmd))
        response = self._SendCommand(cmd)
        self._PrintCommandAndResponse(cmd, response, "Get input values")
        voltage = self._DecodeInteger(response[3:7])/self.convert_voltage
        current = self._DecodeInteger(response[7:11])/self.convert_current
        power   = self._DecodeInteger(response[11:15])/self.convert_power
        op_state = hex(self._DecodeInteger(response[15]))
        demand_state = hex(self._DecodeInteger(response[16:18]))
        return [voltage, current, power, op_state, demand_state]
    
    def getTerminalVoltage(self):
        """
        Returns the terminal voltage in Volts
        
        :returns: float
        """
        return float(self.getInputValues()[0])
    
    def getTerminalCurrent(self):
        """
        Returns the terminal current in Amps
        
        :returns: float
        """
        return float(self.getInputValues()[1])
    
    def getTerminalPower(self):
        """
        Returns the terminal power in Watts
        
        :returns: float
        """
        return float(self.getInputValues()[2])
    


