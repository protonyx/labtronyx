import struct
import time

import models

class m_BMS(models.m_Base):
    """
    Model for the AMPED 2.2 BMS Converter
    """
    
    # Model device type
    deviceType = 'DC-DC Converter'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_Serial']
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validVIDs = ['']
    validPIDs = ['']
    
    commands = {
        'calibrate':    0xAF,
        'enableSampling': 0xB4,
        'disableSampling': 0x5F,
        'identify':     0xAA,
        'shutdown_wdt': 0xBD,
        'resetStatus':  0xBB,
        'setMode_openloop': 0x2B,
        'setMode_closedloop': 0xB7
        }
    
    def _onLoad(self):
        self.instr = self.controller._getInstrument(self.resID)
        
        # Configure the COM Port
        self.instr.baudrate = 1500000
        self.instr.timeout = 0.5
        self.instr.bytesize = 8
        self.instr.parity = 'N'
        self.instr.stopbits = 1
        
        self.instr.open()
        
        self.status = 0
    
    def _onUnload(self):
        self.instr.close()
    
    def getProperties(self):
        prop = models.m_Base.getProperties(self)
        
        # Add any additional properties here
        return prop
    
    def getStatus(self):
        return self.status
    
    def sendCommand(self, address, cmd, data=''):
        """
        Send a command
        
        :returns: bool, True if successful, False otherwise
        """
        self.sendCommand_noAck(address, cmd, data)
        
        try:
            # Verify the acknowledgement
            rx = self.instr.read(10)
            
            if (len(rx) == 10 and tx == rx[0:8]):
                
                self.status = struct.unpack('xxxxxxxxH', rx)
                
                time.sleep(0.2)
                
                return True
            
            else:
                return False
            
        except:
            self.logger.exception('Failed to receive response')
            return False
        
    def sendCommand_noAck(self, address, cmd, data=''):
        """
        Send a command, does not expect an acknowledgement frame
        
        :returns: bool, True if successful, False otherwise
        """
        
        try:
            fmt = 'BBBBi'
            tx = struct.pack(fmt, address, address, cmd, cmd, data)
            tx_full = str(tx) + str(data)
            
            self.instr.write(tx_full)
            self.instr.flush()
            
            return True
            
        except:
            self.logger.exception('Failed to send command')
            return False
        
    def identify(self):
        cmd = self.commands.get('identify', 0xAA)
        self.sendCommand_noAck(0xFA, cmd, 0)
        
        try:
            conv.write(tx)
            conv.flush()
            
            rx = self.instr.read(10)
            #rx = conv.read(512)
            
            if (len(rx) == 10):
                
                self.status = struct.unpack('xBxBxxxx', address, command)
                
                if (command == cmd):
                    return address
            
            else:
                return False
            
        except:
            self.logger.exception('Failed during identify')
    
    def resetStatus(self, address):
        cmd = self.commands.get('resetStatus', 0xBB)
        self.sendCommand(address, cmd)
    
    def calibrate(self, address, data1=1, data2=1):
        cmd = self.commands.get('calibrate', 0xAF)
        
        fmt = 'BB'
        data = struct.pack(fmt, data1, data2)
        
        self.sendCommand(address, cmd, data)
        
        # Read additional 4 bytes after ack
        rx = conv.read(4)
    
    def shutoff_wdt(self, address):
        cmd = self.commands.get('shutdown_wdt', 0xBD)
        self.sendCommand(address, cmd)
    
    def setMode_openloop(self, address):
        cmd = self.commands.get('setMode_openloop', 0x2B)
        self.sendCommand(address, cmd)
            
    def setMode_closedloop(self, address):
        cmd = self.commands.get('setMode_closedloop', 0xB7)
        self.sendCommand(address, cmd)
    
    def set_phaseAngle(self, address, phase):
        cmd = self.commands.get('set_phaseAngle', 0x46)
        
        fmt = 'xH'
        data = struct.pack(fmt, phase)
        
        self.sendCommand(address, cmd, data)
    
    def set_vRef(self, address, vref):
        cmd = self.commands.get('set_vRef', 0xB9)
        
        fmt = 'H'
        data = struct.pack(fmt, vref)
        
        self.sendCommand(address, cmd, data)
    
            
    def enableSampling(self, address):
        cmd = self.commands.get('enableSampling', 0xB4)
        self.sendCommand(address, cmd)
    
    def disableSampling(self, address):
        cmd = self.commands.get('disableSampling', 0x5F)
        self.sendCommand(address, cmd)
    
    def getData(self, address):
        ret = (0,0,0,0,0)
        
        cmd = self.commands.get('getData', 0x8C)
        self.sendCommand_noAck(address, cmd)
        
        try:
            rx = conv.read(10)
            
            fmt = '>HHHHH' #note the big endian ">" in the format code - this is required if you don't want funky data
            phase, vout, vin, iin, status = struct.unpack(fmt, rx)
            
            ret = (phase, vout, vin, iin, status)
        
        except:
            self.logger.exception('Failed during getData')
            
        return ret
    
    def enableSwitching(self, address):
        """
        Enable Switching.
        
        Tries 3 times to start switching since this seems to be so buggy
        
        :returns: True if switching started, False otherwise
        """
        for x in range(3):
            try:
                _,_,_,_,status = conv_getData(address)
        
                if ((status & 0xFF08 == 0) and (status & 0x2 == 0x2)):
                    
                    cmd = self.commands.get('enableSwitching', 0x73)
                    
                    fmt = 'BBB'
                    initial_phase = 0x00
                    data = struct.pack(fmt, address, address, cmd, cmd, initial_phase, initial_phase, initial_phase)
        
                    if self.sendCommand(address, cmd, data):
                        return True
                
                else:
                    self.logger.debug("Failed attempt %i to start switching, not ready", x)
                    
            except:
                pass
            
        return False
    
    def disableSwitching(self, address):
        cmd = self.commands.get('disableSwitching', 0x64)
        self.sendCommand(address, cmd)
    
