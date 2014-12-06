
from models import m_Base

class m_85XX(m_Base):
    
    # Model device type
    deviceType = 'DC Load'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_Serial']
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validVIDs = ['']
    validPIDs = ['']

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
    
    def _onLoad(self):
        self.instr = self.controller._getInstrument(self.resID)
        
        # Configure the COM Port
        self.instr.timeout = 0.5
        self.instr.bytesize = 8
        self.instr.parity = 'N'
        self.instr.stopbits = 1
        
        self.instr.open()
        
        self.SetRemoteControl()
    
    def _onUnload(self):
        self.instr.close()
        
    def getProperties(self):
        ret = m_Base.getProperties(self)
        
        ret['deviceVendor'] = 'BK Precision'
        
        prodInfo = self.GetProductInformation()
        ret['deviceModel'] = prodInfo[0]
        ret['deviceSerial'] = prodInfo[1]
        ret['deviceFirmware'] = prodInfo[2]
            
        return ret
        
    def setBaud(self, baudrate):
        self.instr.close()
        self.instr.baudrate = baudrate
        self.instr.open()
        
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
        self.instr.write(command)
        response = self.instr.read(self.length_packet)
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
        cmd = self._GetCommand(byte, value, num_bytes)
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
    
    def powerOn(self):
        "Turns the load on"
        msg = "Turn load on"
        on = 1
        return self._SendIntegerToLoad(0x21, on, msg, num_bytes=1)
    
    def powerOff(self):
        "Turns the load off"
        msg = "Turn load off"
        off = 0
        return self._SendIntegerToLoad(0x21, off, msg, num_bytes=1)
    
    def SetRemoteControl(self):
        "Sets the load to remote control"
        msg = "Set remote control"
        remote = 1
        return self._SendIntegerToLoad(0x20, remote, msg, num_bytes=1)
    
    def SetLocalControl(self):
        "Sets the load to local control"
        msg = "Set local control"
        local = 0
        return self._SendIntegerToLoad(0x20, local, msg, num_bytes=1)
    def SetMaxCurrent(self, current):
        "Sets the maximum current the load will sink"
        msg = "Set max current"
        return self._SendIntegerToLoad(0x24, current*self.convert_current, msg, num_bytes=4)
    def GetMaxCurrent(self):
        "Returns the maximum current the load will sink"
        msg = "Set max current"
        return self._GetIntegerFromLoad(0x25, msg, num_bytes=4)/self.convert_current
    def SetMaxVoltage(self, voltage):
        "Sets the maximum voltage the load will allow"
        msg = "Set max voltage"
        return self._SendIntegerToLoad(0x22, voltage*self.convert_voltage, msg, num_bytes=4)
    def GetMaxVoltage(self):
        "Gets the maximum voltage the load will allow"
        msg = "Get max voltage"
        return self._GetIntegerFromLoad(0x23, msg, num_bytes=4)/self.convert_voltage
    def SetMaxPower(self, power):
        "Sets the maximum power the load will allow"
        msg = "Set max power"
        return self._SendIntegerToLoad(0x26, power*self.convert_power, msg, num_bytes=4)
    def GetMaxPower(self):
        "Gets the maximum power the load will allow"
        msg = "Get max power"
        return self._GetIntegerFromLoad(0x27, msg, num_bytes=4)/self.convert_power
    def SetMode(self, mode):
        "Sets the mode (constant current, constant voltage, etc."
        if mode.lower() not in self.modes:
            raise Exception("Unknown mode")
        msg = "Set mode"
        return self._SendIntegerToLoad(0x28, self.modes[mode.lower()], msg, num_bytes=1)
    def GetMode(self):
        "Gets the mode (constant current, constant voltage, etc."
        msg = "Get mode"
        mode = self._GetIntegerFromLoad(0x29, msg, num_bytes=1)
        modes_inv = {0:"cc", 1:"cv", 2:"cw", 3:"cr"}
        return modes_inv[mode]
    def SetCCCurrent(self, current):
        "Sets the constant current mode's current level"
        msg = "Set CC current"
        return self._SendIntegerToLoad(0x2A, current*self.convert_current, msg, num_bytes=4)
    def GetCCCurrent(self):
        "Gets the constant current mode's current level"
        msg = "Get CC current"
        return self._GetIntegerFromLoad(0x2B, msg, num_bytes=4)/self.convert_current
    def SetCVVoltage(self, voltage):
        "Sets the constant voltage mode's voltage level"
        msg = "Set CV voltage"
        return self._SendIntegerToLoad(0x2C, voltage*self.convert_voltage, msg, num_bytes=4)
    def GetCVVoltage(self):
        "Gets the constant voltage mode's voltage level"
        msg = "Get CV voltage"
        return self._GetIntegerFromLoad(0x2D, msg, num_bytes=4)/self.convert_voltage
    def SetCWPower(self, power):
        "Sets the constant power mode's power level"
        msg = "Set CW power"
        return self._SendIntegerToLoad(0x2E, power*self.convert_power, msg, num_bytes=4)
    def GetCWPower(self):
        "Gets the constant power mode's power level"
        msg = "Get CW power"
        return self._GetIntegerFromLoad(0x2F, msg, num_bytes=4)/self.convert_power
    def SetCRResistance(self, resistance):
        "Sets the constant resistance mode's resistance level"
        msg = "Set CR resistance"
        return self._SendIntegerToLoad(0x30, resistance*self.convert_resistance, msg, num_bytes=4)
    def GetCRResistance(self):
        "Gets the constant resistance mode's resistance level"
        msg = "Get CR resistance"
        return self._GetIntegerFromLoad(0x31, msg, num_bytes=4)/self.convert_resistance
    def SetTransient(self, mode, A, A_time_s, B, B_time_s, operation="continuous"):
        '''Sets up the transient operation mode.  mode is one of 
        "CC", "CV", "CW", or "CR".
        '''
        if mode.lower() not in self.modes:
            raise Exception("Unknown mode")
        opcodes = {"cc":0x32, "cv":0x34, "cw":0x36, "cr":0x38}
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
        cmd += self._CodeInteger(transient_operations[operation], num_bytes=1)
        cmd += self._Reserved(16)
        cmd += chr(self._CalculateChecksum(cmd))
        assert(self._CommandProperlyFormed(cmd))
        response = self._SendCommand(cmd)
        self._PrintCommandAndResponse(cmd, response, "Set %s transient" % mode)
        return self._ResponseStatus(response)
    def GetTransient(self, mode):
        "Gets the transient mode settings"
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
            return str((A/self.convert_current, A_timer_ms/time_const,
                    B/self.convert_current, B_timer_ms/time_const,
                    transient_operations_inv[operation]))
        elif mode.lower() == "cv":
            return str((A/self.convert_voltage, A_timer_ms/time_const,
                    B/self.convert_voltage, B_timer_ms/time_const,
                    transient_operations_inv[operation]))
        elif mode.lower() == "cw":
            return str((A/self.convert_power, A_timer_ms/time_const,
                    B/self.convert_power, B_timer_ms/time_const,
                    transient_operations_inv[operation]))
        else:
            return str((A/self.convert_resistance, A_timer_ms/time_const, 
                    B/self.convert_resistance, B_timer_ms/time_const,
                    transient_operations_inv[operation]))
    def SetBatteryTestVoltage(self, min_voltage):
        "Sets the battery test voltage"
        msg = "Set battery test voltage"
        return self._SendIntegerToLoad(0x4E, min_voltage*self.convert_voltage, msg, num_bytes=4)
    def GetBatteryTestVoltage(self):
        "Gets the battery test voltage"
        msg = "Get battery test voltage"
        return self._GetIntegerFromLoad(0x4F, msg, num_bytes=4)/self.convert_voltage
    def SetLoadOnTimer(self, time_in_s):
        "Sets the time in seconds that the load will be on"
        msg = "Set load on timer"
        return self._SendIntegerToLoad(0x50, time_in_s, msg, num_bytes=2)
    def GetLoadOnTimer(self):
        "Gets the time in seconds that the load will be on"
        msg = "Get load on timer"
        return self._GetIntegerFromLoad(0x51, msg, num_bytes=2)
    def SetLoadOnTimerState(self, enabled=0):
        "Enables or disables the load on timer state"
        msg = "Set load on timer state"
        return self._SendIntegerToLoad(0x50, enabled, msg, num_bytes=1)
    def GetLoadOnTimerState(self):
        "Gets the load on timer state"
        msg = "Get load on timer"
        state = self._GetIntegerFromLoad(0x53, msg, num_bytes=1)
        if state == 0:
            return "disabled"
        else:
            return "enabled"
    def SetCommunicationAddress(self, address=0):
        '''Sets the communication address.  Note:  this feature is
        not currently supported.  The communication address should always
        be set to 0.
        '''
        msg = "Set communication address"
        return self._SendIntegerToLoad(0x54, address, msg, num_bytes=1)
    def EnableLocalControl(self):
        "Enable local control (i.e., key presses work) of the load"
        msg = "Enable local control"
        enabled = 1
        return self._SendIntegerToLoad(0x55, enabled, msg, num_bytes=1)
    def DisableLocalControl(self):
        "Disable local control of the load"
        msg = "Disable local control"
        disabled = 0
        return self._SendIntegerToLoad(0x55, disabled, msg, num_bytes=1)
    def SetRemoteSense(self, enabled=0):
        "Enable or disable remote sensing"
        msg = "Set remote sense"
        return self._SendIntegerToLoad(0x56, enabled, msg, num_bytes=1)
    def GetRemoteSense(self):
        "Get the state of remote sensing"
        msg = "Get remote sense"
        return self._GetIntegerFromLoad(0x57, msg, num_bytes=1)
    def SetTriggerSource(self, source="immediate"):
        '''Set how the instrument will be triggered.
        "immediate" means triggered from the front panel.
        "external" means triggered by a TTL signal on the rear panel.
        "bus" means a software trigger (see TriggerLoad()).
        '''
        trigger = {"immediate":0, "external":1, "bus":2}
        if source not in trigger:
            raise Exception("Trigger type %s not recognized" % source)
        msg = "Set trigger type"
        return self._SendIntegerToLoad(0x54, trigger[source], msg, num_bytes=1)
    def GetTriggerSource(self):
        "Get how the instrument will be triggered"
        msg = "Get trigger source"
        t = self._GetIntegerFromLoad(0x59, msg, num_bytes=1)
        trigger_inv = {0:"immediate", 1:"external", 2:"bus"}
        return trigger_inv[t]
    def TriggerLoad(self):
        '''Provide a software trigger.  This is only of use when the trigger
        mode is set to "bus".
        '''
        cmd = self._StartCommand(0x5A)
        cmd += self._Reserved(3)
        cmd += chr(self._CalculateChecksum(cmd))
        assert(self._CommandProperlyFormed(cmd))
        response = self._SendCommand(cmd)
        self._PrintCommandAndResponse(cmd, response, "Trigger load (trigger = bus)")
        return self._ResponseStatus(response)
    def SaveSettings(self, register=0):
        "Save instrument settings to a register"
        assert(self.lowest_register <= register <= self.highest_register)
        msg = "Save to register %d" % register
        return self._SendIntegerToLoad(0x5B, register, msg, num_bytes=1)
    def RecallSettings(self, register=0):
        "Restore instrument settings from a register"
        assert(self.lowest_register <= register <= self.highest_register)
        cmd = self._GetCommand(0x5C, register, num_bytes=1)
        response = self._SendCommand(cmd)
        self._PrintCommandAndResponse(cmd, response, "Recall register %d" % register)
        return self._ResponseStatus(response)
    def SetFunction(self, function="fixed"):
        '''Set the function (type of operation) of the load.
        function is one of "fixed", "short", "transient", or "battery".
        Note "list" is intentionally left out for now.
        '''
        msg = "Set function to %s" % function
        functions = {"fixed":0, "short":1, "transient":2, "battery":4}
        return self._SendIntegerToLoad(0x5D, functions[function], msg, num_bytes=1)
    def GetFunction(self):
        "Get the function (type of operation) of the load"
        msg = "Get function"
        fn = self._GetIntegerFromLoad(0x5E, msg, num_bytes=1)
        functions_inv = {0:"fixed", 1:"short", 2:"transient", 4:"battery"}
        return functions_inv[fn]
    def GetInputValues(self):
        '''Returns voltage in V, current in A, and power in W, op_state byte,
        and demand_state byte.
        '''
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
        s = [str(voltage) + " V", str(current) + " A", str(power) + " W", str(op_state), str(demand_state)]
        return join(s, "\t")
    
    # Returns model number, serial number, and firmware version number
    def GetProductInformation(self):
        "Returns model number, serial number, and firmware version"
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

