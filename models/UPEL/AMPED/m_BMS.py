import struct

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
    
    def _onLoad(self):
        self.instr = self.controller._getInstrument(self.resID)
        
        # Configure the COM Port
        self.instr.baudrate = 1500000
        self.instr.timeout = 0.5
        self.instr.bytesize = 8
        self.instr.parity = 'N'
        self.instr.stopbits = 1
        
        self.instr.open()
    
    def _onUnload(self):
        self.instr.close()
    
    def getProperties(self):
        prop = models.m_Base.getProperties(self)
        
        # Add any additional properties here
        return prop
    
    def sendCommand(self, address):
        # TODO: Waiting for standardized communication standard
        pass
    
    def resetStatus(self, address):
        try:
            fmt = 'BBBB'
            cmd = 0xBB
            tx = struct.pack(fmt, address, address, cmd, cmd)
    
            self.logger.debug("resetStatus Tx: 0x%X", tx)
            
            self.instr.write(tx)
            self.instr.flush()
            
            rx = self.instr.read(4)
    
            self.logger.debug("resetStatus Rx: 0x%X", rx)
            
        except:
            self.logger.exception('Failed during resetStatus')
    
    def calibrate(self, address, data1=1, data2=1):
        try:
            fmt = 'BBBBBB'
            cmd = 0xAF
            tx = struct.pack(fmt, address, address, cmd, cmd, data1, data2)
    
            self.logger.debug("calibrate Tx: 0x%X", tx)
            
            conv.write(tx)
            conv.flush()
            
            rx = conv.read(8)
    
            self.logger.debug("calibrate Rx: 0x%X", rx)
        
        except:
            self.logger.exception('Failed during calibrate')
    
    def shutoff_wdt(self, address):
        try:
            fmt = 'BBBB'
            cmd = 0xBD
            tx = struct.pack(fmt, address, address, cmd, cmd)
    
            self.logger.debug("shutoff_wdt Tx: 0x%X", tx)
            
            conv.write(tx)
            conv.flush()
            
            rx = conv.read(4)
    
            self.logger.debug("shutoff_wdt Rx: 0x%X", rx)
        
        except:
            self.logger.exception('Failed during shutoff_wdt')
    
    def setMode_openloop(self, address):
        try:
            fmt = 'BBBB'
            cmd = 0x2B
            tx = struct.pack(fmt, address, address, cmd, cmd)
    
            self.logger.debug("setMode_openloop Tx: 0x%X", tx)
            
            conv.write(tx)
            conv.flush()
            
            rx = conv.read(4)
    
            self.logger.debug("setMode_openloop Rx: 0x%X", rx)
        
        except:
            self.logger.exception('Failed during setMode_openloop')
            
    def setMode_closedloop(self, address):
        try:
            fmt = 'BBBB'
            cmd = 0xB7
            tx = struct.pack(fmt, address, address, cmd, cmd)
    
            self.logger.debug("setMode_closedloop Tx: 0x%X", tx)
            
            conv.write(tx)
            conv.flush()
            
            rx = conv.read(4)
    
            self.logger.debug("setMode_closedloop Rx: 0x%X", rx)
        
        except:
            self.logger.exception('Failed during setMode_closedloop')
    
    def set_phaseAngle(self, address, phase):
        try:
            fmt = 'BBBBxH'
            cmd = 0x46
            tx = struct.pack(fmt, address, address, cmd, cmd, phase)
    
            self.logger.debug("set_phaseAngle Tx: 0x%X", tx)
            
            conv.write(tx)
            conv.flush()
            
            rx = conv.read(4)
    
            self.logger.debug("set_phaseAngle Rx: 0x%X", rx)
        
        except:
            self.logger.exception('Failed during set_phaseAngle')
    
    
    def set_vRef(self, address, vref):
        try:
            fmt = 'BBBBH'
            cmd = 0xB9
            
            tx = struct.pack(fmt, address, address, cmd, cmd, vref)
    
            self.logger.debug("set_vRef Tx: 0x%X", tx)
            
            conv.write(tx)
            conv.flush()
            
            rx = conv.read(4)
    
            self.logger.debug("set_vRef Rx: 0x%X", rx)
        
        except:
            self.logger.exception('Failed during set_vRef')
    
            
    def enableSampling(self, address):
        try:
            fmt = 'BBBB'
            cmd = 0xB4
            tx = struct.pack(fmt, address, address, cmd, cmd)
    
            self.logger.debug("enableSampling Tx: 0x%X", tx)
            
            conv.write(tx)
            conv.flush()
            
            rx = conv.read(4)
    
            self.logger.debug("enableSampling Rx: 0x%X", rx)
        
        except:
            self.logger.exception('Failed during enableSampling')
    
    def disableSampling(self, address):
        try:
            fmt = 'BBBB'
            cmd = 0x5F
            tx = struct.pack(fmt, address, address, cmd, cmd)
    
            self.logger.debug("disableSampling Tx: 0x%X", tx)
            
            conv.write(tx)
            conv.flush()
            
            rx = conv.read(4)
    
            self.logger.debug("disableSampling Rx: 0x%X", rx)
        
        except:
            self.logger.exception('Failed during disableSampling')
    
    def getData(self, address):
        ret = (0,0,0,0,0)
        try:
            fmt = 'BBBB'
            cmd = 0x8C
            tx = struct.pack(fmt, address, address, cmd, cmd)
    
            self.logger.debug("getData Tx: 0x%X", tx)
            
            conv.write(tx)
            conv.flush()
            
            rx = conv.read(10)
            
            fmt = '>HHHHH' #note the big endian ">" in the format code - this is required if you don't want funky data
            phase, vout, vin, iin, status = struct.unpack(fmt, rx)
            
            ret = (phase, vout, vin, iin, status)
            
            self.logger.debug("getData Rx: 0x%X", rx)
        
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
                
                    fmt = 'BBBBBBB'
                    cmd = 0x73
                    initial_phase = 0x00
                    tx = struct.pack(fmt, address, address, cmd, cmd, initial_phase, initial_phase, initial_phase)
        
                    self.logger.debug("enableSwitching Tx: 0x%X", tx)
                    
                    conv.write(tx)
                    conv.flush()
                    
                    rx = conv.read(4)
        
                    self.logger.debug("enableSwitching Rx: 0x%X", rx)
        
                    return True
                
                else:
                    self.logger.debug("Failed attempt %i to start switching, not ready", x)
                    
            except:
                pass
            
        return False
    
    def disableSwitching(self, address):
        try:
            fmt = 'BBBB'
            cmd = 0x64
            tx = struct.pack(fmt, address, address, cmd, cmd)
    
            self.logger.debug("disableSwitching Tx: 0x%X", tx)
            
            conv.write(tx)
            conv.flush()
            
            rx = conv.read(4)
    
            self.logger.debug("disableSwitching Rx: 0x%X", rx)
        
        except:
            self.logger.exception('Failed during disableSwitching')
    
    def identify(self):
        returnaddress_a = 0xFF
        cmd_a = 0xFF
        cmd_b = 0xFF
        
        try:
            fmt = 'BBBB'
            cmd = 0xAA
            address = 0xFF
            tx = struct.pack(fmt, address, address, cmd, cmd)
    
            self.logger.debug("identify Tx: 0x%X", tx)
            
            conv.write(tx)
            conv.flush()
            
            rx = conv.read(512)
    
            self.logger.debug("identify Rx: 0x%X", rx)
            
            # TODO: Iterate through all received bytes to interpret data
    
            #fmt = 'BBBB'
            #returnedaddress_a, returnedaddress_b, cmd_a, cmd_b = struct.unpack(fmt, rx)
    
            return returnedaddress_a
            
        except:
            self.logger.exception('Failed during identify')