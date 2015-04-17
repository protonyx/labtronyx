from Base_Driver import Base_Driver

import struct
import time

class m_BMS(Base_Driver):
    """
    Model for the AMPED 2.2 BMS Converter
    """
    
    info = {
        # Device Manufacturer
        'deviceVendor':         'UPEL',
        # List of compatible device models
        'deviceModel':          ['AMPED BMS 2.1'],
        # Device type    
        'deviceType':           'DC-DC Converter',      
        
        # List of compatible resource types
        'validResourceTypes':   ['Serial']
    }
    
    commands = {
        'calibrate':    0xAF,
        'enableSampling': 0xB4,
        'disableSampling': 0x5F,
        'identify':     0xAA,
        'shutdown_wdt': 0xBD,
        'resetStatus':  0xBB,
        'enableSwitching': 0x7F,
        'enableSwitching_open': 0x73
        }
    
    def _onLoad(self):
        self.instr = self.getResource()
        
        self.instr.open()
        
        # Configure the COM Port
        self.instr.configure(baudrate=1500000,
                             timeout=0.5,
                             bytesize=8,
                             parity='N',
                             stopbits=1)
        
        self.status = 0
    
    def _onUnload(self):
        self.instr.close()
    
    def getProperties(self):
        prop = Base_Driver.getProperties(self)
        
    	prop['deviceModel'] = self.info.get('deviceModel')[0]
        
        # Add any additional properties here
        return prop
    
    def getLastStatus(self):
        """
        The the status of the last transfer
        
        :returns: Status code
        """
        return self.status
    
    def sendCommand(self, address, cmd, data=0):
        """
        Send a command
        
        :returns: bool, True if successful, False otherwise
        """
        self.sendCommand_noAck(address, cmd, data)
        
        try:
            # Verify the acknowledgement
            rx = self.instr.read_raw(10)
            
            if (len(rx) == 10):
                
                (address_r, command_r, status) = struct.unpack('xBxBxxxxH', rx)
                self.status = status
                
                return address_r == address and command_r == cmd
            
            else:
                self.logger.error("Identify returned an invalid number of bytes: %i", len(rx))
                return False
            
        except:
            self.logger.exception('Failed to receive response')
            return False
        
    def sendCommand_noAck(self, address, cmd, data=0):
        """
        Send a command, does not expect an acknowledgement frame
        
        :returns: bool, True if successful, False otherwise
        """
        
        try:
            fmt = 'BBBBi'
            tx = struct.pack(fmt, address, address, cmd, cmd, data)
            
            self.instr.write_raw(tx)
            
            return True
            
        except:
            self.logger.exception('Failed to send command')
            return False
        
    def identify(self):
        """
        Identify a single module connected to the RS-485 bus
        """
        cmd = self.commands.get('identify', 0xAA)
        self.sendCommand_noAck(0xFA, cmd, 0)
        
        try:
            self.instr.configure(timeout=3.0)
            
            rx = self.instr.read_raw(10)

            self.instr.configure(timeout=0.5)
            
            if (len(rx) == 10):

                self.logger.debug("IDENTIFY RX: %s", rx.encode('hex'))
                (address, command) = struct.unpack('xBxBxxxxxx', rx)
                
                if (command == cmd):
                    return address

                else:
                    return False
            
            else:
                self.logger.error("Identify returned an invalid number of bytes: %i", len(rx))
                return False
            
        except:
            self.logger.exception('Failed during identify')
    
    def resetStatus(self, address):
        """
        Reset converter status, clears any latched errors
        
        :param address: Address of converter to reset
        :type address: int
        """
        cmd = self.commands.get('resetStatus', 0xBB)
        self.sendCommand(address, cmd)
    
    def calibrate(self, address, data1=1, data2=1):
        """
        Calibrate converter
        
        :param address: Address of converter
        :type address: int
        :param data1: Calibration 1
        :type data1: int
        :param data2: Calibration 2
        :type data2: int
        """
        cmd = self.commands.get('calibrate', 0xAF)

        data = (data1 << 8) | (data2)
        
        self.sendCommand(address, cmd, data)
    
    def shutoff_wdt(self, address):
        """
        Disable the watchdog timer
        
        :param address: Address of converter
        :type address: int
        """
        cmd = self.commands.get('shutdown_wdt', 0xBD)
        self.sendCommand(address, cmd)
    
    def set_phaseAngle(self, address, phase):
        """
        Set the open-loop phase angle
        
        :param address: Address of converter
        :type address: int
        :param phase: Phase command, 16-bit resolution
        :type phase: int
        """
        cmd = self.commands.get('set_phaseAngle', 0x46)
        
        data = phase & 0xFFFF
        
        self.sendCommand(address, cmd, data)
    
    def set_vRef(self, address, vref):
        """
        Set the closed-loop voltage reference
        
        :param address: Address of converter
        :type address: int
        :param vref: Regulation voltage, 16-bit resolution
        :type vref: int
        """
        cmd = self.commands.get('set_vRef', 0xB9)
        
        data = vref & 0xFFFF
        
        self.sendCommand(address, cmd, data)
            
    def enableSampling(self, address):
        """
        Enable sensor sampling
        
        :param address: Address of converter
        :type address: int
        """
        cmd = self.commands.get('enableSampling', 0xB4)
        self.sendCommand(address, cmd)
    
    def disableSampling(self, address):
        """
        Disable sensor sampling
        
        :param address: Address of converter
        :type address: int
        """
        cmd = self.commands.get('disableSampling', 0x5F)
        self.sendCommand(address, cmd)
    
    def getData(self, address):
        """
        Get sensor data
        
        :param address: Address of converter
        :type address: int
        :returns: tuple (phase, vout, vin, iin, status)
        """
        ret = (0,0,0,0,0)
        
        cmd = self.commands.get('getData', 0x8C)
        self.sendCommand_noAck(address, cmd)
        
        try:
            rx = self.instr.read(10)
            
            fmt = '>HHHHH' #note the big endian ">" in the format code - this is required if you don't want funky data
            phase, vout, vin, iin, status = struct.unpack(fmt, rx)
            
            ret = (phase, vout, vin, iin, status)
            self.status = status
        
        except:
            self.logger.exception('Failed during getData')
            
        return ret
    
    def enableSwitching(self, address):
        """
        Enable Switching.
        
        Tries 3 times to start switching since this seems to be so buggy
        
        :param address: Address of converter
        :type address: int
        :returns: True if switching started, False otherwise
        """
        for x in range(3):
            try:
                _,_,_,_,status = self.getData(address)
        
                if ((status & 0xFF08 == 0) and (status & 0x2 == 0x2)):
                    
                    cmd = self.commands.get('enableSwitching', 0x7F)
                    
                    initial_phase = 0x00
                    data = (initial_phase << 16) | (initial_phase << 8) | initial_phase
        
                    if self.sendCommand(address, cmd, data):
                        return True
                
                else:
                    self.logger.debug("Failed attempt %i to start switching, not ready", x)
                    
            except:
                pass
            
        return False

    def enableSwitching_open(self, address):
        """
        Enable Switching in open loop mode
        
        Tries 3 times to start switching since this seems to be so buggy
        
        :param address: Address of converter
        :type address: int
        :returns: True if switching started, False otherwise
        """
        for x in range(3):
            try:
                _,_,_,_,status = self.getData(address)
        
                if ((status & 0xFF08 == 0) and (status & 0x2 == 0x2)):
                    
                    cmd = self.commands.get('enableSwitching_open', 0x73)
                    
                    initial_phase = 0x00
                    data = (initial_phase << 16) | (initial_phase << 8) | initial_phase
        
                    if self.sendCommand(address, cmd, data):
                        return True
                
                else:
                    self.logger.debug("Failed attempt %i to start switching, not ready", x)
                    
            except:
                pass
            
        return False

    def close_loop(self, address):
        """
        Enter closed-loop mode
        
        :param address: Address of converter
        :type address: int
        """
        cmd = self.commands.get('close_loop', 0xB7)
        self.sendCommand(address, cmd)
    
    def disableSwitching(self, address):
        """
        Disable switching
        
        :param address: Address of converter
        :type address: int
        """
        cmd = self.commands.get('disableSwitching', 0x64)
        self.sendCommand(address, cmd)
    
