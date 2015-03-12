import threading
import struct 
import time

from . import m_BDPC_Base

import common.status

class Base_Serial(m_BDPC_Base):
    
    pkt_struct = struct.Struct("BBBBBBBB")
    
    registers = {
        'CONTROL': 0x00,
        'PLIMIT': 0x01,
        'VLIMIT': 0x02,
        'ILIMIT': 0x03,
        'VPRI_OS': 0x04,
        'VSEC_OS': 0x05,
        'IPRI_OS': 0x06,
        'ISEC_OS': 0x07,
        'MPS': 0x08,
        'PCMD': 0x09,
        'ACMD_A': 0x0A,
        'ACMD_B': 0x0B,
        'ACMD_C': 0x0C,
        'ACMD_D': 0x0D,
        'TDM': 0x0E,
        'TDA_A': 0x0F,
        'TDA_B': 0x10,
        'TDA_C': 0x11,
        'TDA_D': 0x12,
        'GAINA': 0x13,
        'GAINB': 0x14,
        
        'STATUS': 0x20,
        'MVIN': 0x21,
        'MVOUT': 0x22,
        'MIOUT': 0x23,
        'MIIN': 0x24,
        'CONVRATIO': 0x25,
        'MPCMD': 0x26,
        'PHI_AB': 0x27,
        'PHI_AD': 0x28,
        'PHI_DC': 0x29,
        'PHI_AA': 0x2A,
        'REFI_P': 0x2B,
        'REFI_V': 0x2C,
        'REFI_I': 0x2D,
        'CONVREF': 0x2E,
        'GAINA_RO': 0X2F,
        'GAINB_RO': 0X30,
        'PHI_AUXA': 0X31,
        'PHI_AUXB': 0X32,
        'PHI_AUXC': 0X33,
        'PHI_AUXD': 0X34,
        'AVGQ_A': 0x35,
        'AVGQ_B': 0x36,
        'AVGQ_C': 0x37,
        'AVGQ_D': 0x38
        }
    
    phase_angle = {
       'A': 'AMCD_A',
       'B': 'AMCD_B',
       'C': 'AMCD_C',
       'D': 'AMCD_D' 
    }
    
    dead_time = {
       'M': 'TDM',
       'A': 'TDA_A',
       'B': 'TDA_B',
       'C': 'TDA_C',
       'D': 'TDA_D' 
    }
    
    # Default Sensor Gains
    sensor_gain = {
        'PrimaryVoltage': 1.0,
        'SecondaryVoltage': 1.0,
        'PrimaryCurrent': 1.0,
        'SecondaryCurrent': 1.0,
        'ZVSCurrentA': 1.0,
        'ZVSCurrentB': 1.0,
        'ZVSCurrentC': 1.0,
        'ZVSCurrentD': 1.0
        }
    
    sensor_os_regs = {
        'PrimaryVoltage': 'VPRI_OS',
        'SecondaryVoltage': 'VSEC_OS',
        'PrimaryCurrent': 'IPRI_OS',
        'SecondaryCurrent': 'ISEC_OS',
        }
    
    sensor_regs = {
        'PrimaryVoltage': 'MVIN',
        'SecondaryVoltage': 'MVOUT',
        'PrimaryCurrent': 'MIIN',
        'SecondaryCurrent': 'MIOUT',
        'ZVSCurrentA': 'AVGQ_A',
        'ZVSCurrentB': 'AVGQ_B',
        'ZVSCurrentC': 'AVGQ_C',
        'ZVSCurrentD': 'AVGQ_D'
        }
    
    sensor_description = {
        'PrimaryVoltage': 'Primary Voltage',
        'SecondaryVoltage': 'Secondary Voltage',
        'PrimaryCurrent': 'Primary Current',
        'SecondaryCurrent': 'Secondary Current',
        'ZVSCurrentA': 'ZVS Current A',
        'ZVSCurrentB': 'ZVS Current B',
        'ZVSCurrentC': 'ZVS Current C',
        'ZVSCurrentD': 'ZVS Current D'
        }
    
    sensor_units = {
        'PrimaryVoltage': 'V',
        'SecondaryVoltage': 'V',
        'PrimaryCurrent': 'A',
        'SecondaryCurrent': 'A',
        'ZVSCurrentA': 'A',
        'ZVSCurrentB': 'A',
        'ZVSCurrentC': 'A',
        'ZVSCurrentD': 'A'
        }
    
    phase_angle_reg = {
        'AB': 'PHI_AB',
        'AD': 'PHI_AD',
        'DC': 'PHI_DC',
        'AuxA': 'PHI_AUXA',
        'AuxB': 'PHI_AUXB',
        'AuxC': 'PHI_AUXC',
        'AuxD': 'PHI_AUXD'              
        }
    
    def _onLoad(self):
        self.resource = self.getResource()
        
        # Configure the COM Port
        self.resource.configure(baudrate=115200,
                                timeout=0.25,
                                bytesize=8,
                                parity='E',
                                stopbits=1)
        
        # Attempt to get the status
        self.getStatus()
        
    def _onUnload(self):
        self.resource.close()
        
    def getProperties(self):
        prop = m_BDPC_Base.getProperties(self)
        
        prop['deviceVendor'] = 'UPEL'
        prop['deviceModel'] = 'BDPC Serial'
        
        return prop
     
     #==========================================================================
     # Helper Functions   
     #==========================================================================
     
    def _SRC_pack(self, address, data):
        """
        Will throw a TypeError if data is not an int
        
        :param address: Register Address
        :type address: int
        :param data: Data
        :type data: int
        :returns: SRC_Packet
        """
        data = int(data)
        data_h = (data >> 8) & 0xFF
        data_l = data & 0xFF
        return self.pkt_struct.pack(0x24, address, address, data_h, data_l, data_h, data_l, 0x1E)
    
    def _SRC_unpack(self, packet):
        """
        :param packet: SRC_Packet
        :returns: tuple (address, data)
        """
        assert len(packet) == self.pkt_struct.size
        
        start_sync, addr1, addr2, data_h1, data_l1, data_h2, data_l2, end_sync = self.pkt_struct.unpack(packet)
        
        data1 = (data_h1 << 8) | data_l1
        data2 = (data_h2 << 8) | data_l2
        
        assert start_sync == 0x24
        assert end_sync == 0x1E
        assert addr1 == addr2
        assert data1 == data2
        
        return ((addr1 & 0x7F), data1)
    
    def _SRC_write_packet(self, addr, data):
        """
        Send a formatted SRC packet
        
        :param address: Register Address
        :type address: int
        :param data: Data
        :type data: int
        """
        packet = self._SRC_pack(addr, data)
        self.resource.write(packet)
        self.logger.debug("SRC TX: %s", packet.encode('hex'))
    
    def _SRC_read_packet(self):
        """
        Scans the serial buffer for an SRC packet. Must be called multiple times
        if multiple packets are in the serial buffer
        
        :returns: tuple (address, data) if found, None otherwise
        """
        
        while (self.resource.inWaiting() > 0):
            # Read the next byte in the serial buffer
            buf = self.resource.read(1)
            # Check if the byte is a START_SYNC
            if (buf == chr(0x24)):
                bytesWaiting = self.resource.inWaiting()
                if (bytesWaiting >= (self.pkt_struct.size - 1)):
                    # Retrieve the rest of the packet
                    buf = buf + self.resource.read(self.pkt_struct.size - 1)
                    
                    # Is there an END_SYNC at the end of the packet?
                    if buf[-1] == chr(0x1E):
                        # Attempt to unpack the packet
                        try:
                            address, data = self._SRC_unpack(buf)
                            
                            self.logger.debug("SRC RX Packet: %s", buf.encode('hex'))
                            
                            # Check for an error packet
                            # TODO: What should happen if we receive an error packet?
                            if address == 0xFF:
                                pass
                            
                            return (address, data)
                    
                        except:
                            # Something was wrong with the packet
                            self.logger.error("SRC RX Invalid Packet: %s", buf.encode('hex'))
                        
                        # Keep searching for a valid packet
                else:
                    # START_SYNC but not full packet in the queue
                    buf = buf + self.resource.read(self.resource.inWaiting())
                    self.logger.error("SRC RX Incomplete Packet: %s", buf.encode('hex'))
                    
        return None
        
    def read_register(self, address):
        if self.resource.getResourceStatus() != common.status.error:
            address = address & 0x7F
            
            for attempt in range(3):
                self._SRC_write_packet(address, 0)
                time.sleep(0.1)
                
                recv = self._SRC_read_packet()
                if recv is not None:
                    addr, data = recv
                    
                    if addr == address:
                        return data
                    else:
                        self.logger.error("SRC RX address did not match TX address, retrying")
                    
                # Attempt failed, try again
            
            # Retries failed
            self.logger.error("Unable to read register %s", address)
            
            # Flag the resource as unresponsive
            self.resource.setResourceStatus(common.status.error)
            
            raise RuntimeError()
            
        else:
            raise RuntimeError()
    
    def write_register(self, address, data):
        if self.resource.getResourceStatus() != common.status.error:
            address_write = int(address) | 0x80
            data = int(data)
            
            for attempt in range(3):
                self._SRC_write_packet(address_write, data)
                time.sleep(0.1)
                
                recv = self._SRC_read_packet()
                if recv is not None:
                    addr, data_ret = recv
                    
                    if addr == address and data_ret == data:
                        return data_ret
                    else:
                        self.logger.error("SRC RX did not match TX, retrying")
                    
                # Attempt failed, try again
                
            # Retries failed
            self.logger.error("Unable to write register %s", address)    
            
            # Flag the resource as unresponsive
            self.resource.setResourceStatus(common.status.unresponsive)
            
            raise RuntimeError()
            
        else:
            raise RuntimeError()
    
    def convert_twoscomp(self, num, total_bits):
        if ( (num&(1<<(total_bits-1))) != 0):
            num = num - (1<<total_bits)
            
        return num
    
    #===========================================================================
    # Options
    #===========================================================================
    
    def setOption(self, **kwargs):
        address = self.registers.get('CONTROL')
        control_reg = self.read_register(address)
        
        for field_tag in kwargs:
            if field_tag in self.options.values():
                try:
                    bit_number = [k for k,v in self.options.items() if v == field_tag][0]
                    val = kwargs.get(field_tag)
            
                    mask = 0x1 << bit_number
            
                    if val:
                        control_reg = control_reg | mask
                    else:
                        control_reg = control_reg & ~mask
                except:
                    # field_tag was not found in options dictionary
                    pass
        
        self.write_register(address, control_reg)
                
    def getOption(self):
        address = self.registers.get('CONTROL')
        control_reg = self.read_register(address)
        
        temp_dict = {}
        
        for bit, field_tag in self.options.items():
            mask = 0x1 << bit
            val = control_reg & mask
            if val > 0:
                temp_dict[field_tag] = 1
            else:
                temp_dict[field_tag] = 0
        
        return temp_dict
        
    #===========================================================================
    # Sensors
    #===========================================================================
    
    def setSensorGain(self, sensor, gain):
        self.sensor_gain[sensor] = gain
    
    def getSensorGain(self, sensor):
        return self.sensor_gain[sensor]
    
    def setSensorOffset(self, sensor, offset):
        sensor_reg = self.sensor_os_regs.get(sensor)
        address = self.registers.get(sensor_reg)
        return self.write_register(address,offset)
    
    def getSensorOffset(self, sensor):
        sensor_reg = self.sensor_regs.get(sensor)
        address = self.registers.get(sensor_reg)
        return self.read_register(address)
    
    def getSensorValue(self, sensor):
        sensor_reg = self.sensor_regs.get(sensor)
        address = self.registers.get(sensor_reg)
        value = self.read_register(address)
        
        gain = self.sensor_gain.get(sensor)
        
        return gain * value
    
    # Helper functions
    
    def getInputVoltage(self):
        return self.getSensorValue('PrimaryVoltage')
    
    def getInputCurrent(self):
        return self.getSensorValue('PrimaryCurrent')
        
    def getOutputVoltage(self):
        return self.getSensorValue('SecondaryVoltage')
        
    def getOutputCurrent(self):
        return self.getSensorValue('SecondaryCurrent')
    
    def getSensorRawValue(self, sensor):
        sensor_reg = self.sensor_regs.get(sensor)
        address = self.registers.get(sensor_reg)
        return self.read_register(address)
        
    def getSensorUnits(self, sensor):
        return self.sensor_units.get(sensor)
    
    def getSensorDescription(self, sensor):
        return self.sensor_description.get(sensor)
    
    #===========================================================================
    # Parameters
    #===========================================================================
    def getVoltageReference(self):
        address = self.registers.get('VLIMIT')
        set_v = self.read_register(address)
        return (float(set_v) / float(self.getSensorGain('SecondaryVoltage')))
    
    def setVoltageReference(self, set_v):
        address = self.registers.get('VLIMIT')
        set_v = int(float(set_v) * self.getSensorGain('SecondaryVoltage'))
        return self.write_register(address, set_v);
    
    def getCurrentReference(self):
        address = self.registers.get('ILIMIT')
        set_i = self.read_register(address)
        return (float(set_i) / float(self.getSensorGain('SecondaryCurrent')))

    def setCurrentReference(self, set_i):
        address = self.registers.get('ILIMIT')
        set_i = int(float(set_i) * self.getSensorGain('SecondaryCurrent'))
        return self.write_register(address, set_i);
    
    def getPowerReference(self):
        address = self.registers.get('PLIMIT')
        return self.read_register(address)
    
    def setPowerReference(self, set_p):
        address = self.registers.get('PLIMIT')
        return self.write_register(address, set_p);
    
    def setPowerCommand(self, command):        
        command = command * 0x7FF
        address = self.registers.get('PCMD')
        return self.write_register(address, command)       
    
    def setPhaseShift(self, angle):
        address = self.registers.get('MPS')
        angle_converted = int(float(angle * 0x7FF) / 180)
        return self.write_register(address, angle_converted)
        
    def getPhaseShift(self):
        address = self.registers.get('MPS')
        angle = self.read_register(address)
        return float(angle * 180) / 0x7FF
        
    def setPhaseAngle(self, leg, angle):        
        reg = self.phase_angle.get(leg)
        address = self.registers.get(reg)
        angle_converted = int(float(angle * 0x7FF) / 180)
        return self.write_register(address, angle_converted)
    
    def setDeadTime(self, leg, nanoseconds):
        reg = self.dead_time.get(leg)
        address = self.registers.get(reg)
        nanoseconds_converted = int( float(nanoseconds) / 5)
        return self.write_register(address, nanoseconds_converted)
    
    def setGain(self, gain):
        address_a = self.registers.get('GAIN_A')
        address_b = self.registers.get('GAIN_B')      
        
        error_min = float(100)
        for a in xrange(0,16):
            for b in xrange(0,16):
                calc_gain = float(a) / (2 ** b)
                error = abs(calc_gain - gain)
                if error < error_min:
                    error_min = error
                    write_a = a
                    write_b = b
                    
        self.write_register(address_a, write_a)
        self.write_register(address_b, write_b)
        
    #===========================================================================
    # Diagnostics
    #===========================================================================
    def getStatus(self):
        address = self.registers.get('STATUS')
        status_reg = self.read_register(address)
        
        temp_dict = {}
        
        for bit, field_tag in self.status.items():
            mask = 0x1 << bit
            val = status_reg & mask
            if val > 0:
                temp_dict[field_tag] = 1
            else:
                temp_dict[field_tag] = 0
            
        return temp_dict 
        
    def getConversionRatioMeasured(self):
        address = self.registers.get('CONVRATIO')
        conv_ratio = self.read_register(address)
        conv_ratio_normalized = float(conv_ratio)/0xFFF        
        return conv_ratio_normalized
        
    def getPowerCommand(self):
        address = self.registers.get('MPCMD')
        pcmd = self.read_register(address)
        pcmd = self.convert_twoscomp(pcmd, total_bits=12)
        pcmd_normalized = float(pcmd) / 0x7FF        
        return pcmd_normalized
        
    def getPhaseAngle(self, **kwargs):
        ret = {}
        
        for arg in kwargs:
            if arg in self.phase_angle_reg:
                phase_reg = self.phase_angle_reg.get(arg)
                address = self.registers.get(phase_reg)
                
                angle = self.read_register(address)
                angle_converted = float(angle * 180) / 0x7FF
                
                ret[arg] = angle_converted
                
        return ret
                
    def getGain(self):
        address_a = self.registers.get('GAINA_RO')
        gain_a = self.read_register(address) 
        
        address_b = self.registers.get('GAINB_RO')
        gain_b = self.read_register(address)
        
        return float(gain_a) / (2**gain_b)
    
    def getMMCMode(self):
        address_p = self.registers.get('REFI_P')
        address_v = self.registers.get('REFI_V')
        address_i = self.registers.get('REFI_I')
        
        dict = {}
        
        dict['power'] =  self.read_register(address_p)    
        dict['voltage'] = self.read_register(address_v)
        dict['current'] = self.read_register(address_i)
        
        return min(dict)      
        
    #===========================================================================
    # Composite Data
    #===========================================================================
    
    def getPrimaryPower(self):
        pv = self.getSensorValue('PrimaryVoltage')
        pi = self.getSensorValue('PrimaryCurrent')
        
        return pv*pi
    
    def getSecondaryPower(self):
        sv = self.getSensorValue('SecondaryVoltage')
        si = self.getSensorValue('SecondaryCurrent')
        
        return sv*si
    
    def getConversionRatioCalc(self):
        pv = self.getSensorValue('PrimaryVoltage') 
        sv = self.getSensorValue('SecondaryVoltage')
        
        return float(sv) / float(pv)
    
    def getEfficiency(self):
        pp = self.getPrimaryPower()
        sp = self.getSecondaryPower()
        
        try:
            return float(sp) / float(pp)
        except ZeroDivisionError:
            return 0.0

