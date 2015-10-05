from labtronyx.bases import Base_Driver
from labtronyx.common.errors import *

import struct
import time


class m_BDPC_Base(object):
    """
    Common model for all BDPC devices
    """
    
    # Model device type
    deviceType = 'Bidirectional Power Supply'

    
    sensors = {
        'PrimaryVoltage': 1,
        'SecondaryVoltage': 2,
        'PrimaryCurrent': 3,
        'SecondaryCurrent': 4,
        'ZVSCurrentA': 5,
        'ZVSCurrentB': 6,
        'ZVSCurrentC': 7,
        'ZVSCurrentD': 8
        }
    
    # Bit Fields for REG_CONTROL
    options = {
        0: 'switching',
        1: 'require_external_enable',
        2: 'master_mode',
        3: 'slave_mode',
        4: 'latch_param_reg',
        5: 'latch_diagnostic_reg',
        6: 'open_main_loop',
        7: 'open_aux_loops',
        8: 'manual_dead_time',
        9: 'fixed_gain',
        10: 'manual_fet_control',
        11: 'manual_input_voltage'
        }
    
    option_descriptions = {
        'switching': 'Switching Enabled',
        'require_external_enable': 'External Enable',
        'master_mode': 'Master',
        'slave_mode': 'Slave',
        'latch_param_reg': 'Latch Parameters',
        'latch_diagnostic_reg': 'Latch Diagnostics',
        'open_main_loop': 'Open Loop',
        'open_aux_loops': 'Open ZVS',
        'manual_dead_time': 'Adj. Dead Time',
        'fixed_gain': 'Adj. Loop Gain',
        'manual_fet_control': 'Control FETs',
        'manual_input_voltage': 'Adj. Input Voltage'
        }
    
    # Bit fields for REG_STATUS
    status = {
        0: 'soft_start',
        1: 'switching',
        2: 'feedback_control',
        3: 'ZVS_compensator',
        4: 'secondary_overvoltage',
        5: 'primary_overvoltage'
        }
    
    status_descriptions = {
        'soft_start': 'Soft Start',
        'switching': 'Switching',
        'feedback_control': 'Feedback Control',
        'ZVS_compensator': 'ZVS Compensating',
        'secondary_overvoltage': 'Secondary Overvoltage',
        'primary_overvoltage': 'Primary Overvoltage'
        }
    
    def getProperties(self):
        prop = Base_Driver.getProperties(self)
        
        prop['numSensors'] = len(self.sensors)
        
        # Add any additional properties here
        return prop
    
        # Model device type

    #===========================================================================
    # Options
    #===========================================================================
    
    def setOption(self, **kwargs):
        raise NotImplementedError
                
    def getOption(self, **kwargs):
        raise NotImplementedError
    
    def getOptionFields(self):
        return self.options
    
    def getOptionDescriptions(self):
        return self.option_descriptions
    
    #===========================================================================
    # Sensors
    #===========================================================================
    def getSensors(self):
        return self.sensors
    
    def setSensorGain(self, sensor, gain):
        raise NotImplementedError
    
    def getSensorGain(self, sensor):
        raise NotImplementedError
    
    def setSensorOffset(self, sensor, offset):
        raise NotImplementedError
    
    def getSensorOffset(self, sensor):
        raise NotImplementedError
    
    def getSensorValue(self, sensor):
        raise NotImplementedError
    
    def getSensorValue_ext(self, sensor, module):
        pass
    
    def getSensorRawValue(self, sensor):
        raise NotImplementedError
    
    def getSensorUnits(self, sensor):
        raise NotImplementedError
    
    def getSensorDescription(self, sensor):
        raise NotImplementedError
    
    #===========================================================================
    # Parameters
    #===========================================================================
    
    def getVoltageReference(self):
        raise NotImplementedError
    
    def setVoltageReference(self, set_v):
        raise NotImplementedError
    
    def getCurrentReference(self):
        raise NotImplementedError
    
    def setCurrentReference(self, set_i):
        raise NotImplementedError
    
    def getPowerReference(self):
        raise NotImplementedError
    
    def setPowerReference(self, set_p):
        raise NotImplementedError
    
    def setPowerCommand(self, command):
        raise NotImplementedError
    
    def setPhaseShift(self, angle):
        raise NotImplementedError
    
    def getPhaseShift(self):
        raise NotImplementedError
    
    def setPhaseAngle(self, leg, angle):
        raise NotImplementedError
    
    def setDeadTime(self, leg, nanoseconds):
        raise NotImplementedError
    
    def setGain(self, gain):
        raise NotImplementedError
    
    #===========================================================================
    # Diagnostics
    #===========================================================================
    def getStatus(self):
        raise NotImplementedError
		
    def getStatusFields(self):
        return self.status
    
    def getStatusDescriptions(self):
        return self.status_descriptions
        
    def getConversionRatioMeasured(self):
        raise NotImplementedError
		
    def getPowerCommand(self):
        raise NotImplementedError
		
    def getPhaseAngle(self):
        raise NotImplementedError
	
    def getGain(self):
        raise NotImplementedError
		
    def getMMCMode(self):
        raise NotImplementedError

    #===========================================================================
    # Composite Data
    #===========================================================================
    
    def getPrimaryPower(self):
        pv = self.getSensorValue(1)
        pi = self.getSensorValue(3)
        
        return pv*pi
    
    def getSecondaryPower(self):
        sv = self.getSensorValue(2)
        si = self.getSensorValue(4)
        
        return sv*si
    
    def getConversionRatioCalc(self):
        pv = self.getSensorValue(1) 
        sv = self.getSensorValue(2)
        
        return float(sv) / float(pv)
    
    def getEfficiency(self):
        pp = self.getPrimaryPower()
        sp = self.getSecondaryPower()
        
        return float(sp) / float(pp)

    
class Base_ICP(m_BDPC_Base):

    states = {
        0x01: ('Running', 'Start'),
        0x02: ('Stopped', 'Stop'),
        0x80: ('Ready', 'Initialize'),
        0x81: ('Reset', 'Reset') }

    state_transitions = {
        0x01: [0x02, 0x80, 0x81],
        0x02: [0x80, 0x81],
        0x80: [0x01, 0x81],
        0x81: [0x80]}

    registers = {
        'SensorGain': 0x2110,
        'SensorOffset': 0x2111,
        'SensorDescription': 0x2120,
        'SensorUnits': 0x2121,
        'SensorData': 0x2122,
        'SensorDataRaw': 0x2123,
        # Main Controller
        'FeedbackLoopGain': 0x2210,
        'PowerCommand': 0x2211,
        'MMCParameters': 0x2220,
        'MMCDiagnostics': 0x2222,
#         This StatusReg function will return only the value of the status register to use here
        'StatusReg': 0x2000
        }

    #===========================================================================
    # Operation
    #===========================================================================

    def getStates(self):
        return self.states

    def getStateTransitions(self):
        return self.state_transitions

    def getState(self):
        return self.instr.getState()

    def setState(self, new_state):
        return self.instr.setState(new_state)

    def getErrors(self):
        return int(self.instr.readReg(0x1001, 0x01, 'int16'))

    def getStatus(self):
        return int(self.instr.readReg(0x1002, 0x1, 'int16'))

    #===========================================================================
    # Maybe obsolete functions
    #===========================================================================

    def update_startup(self):
        """
        Called on startup to get the following values:

            * Sensor types for all sensors
            * MMC Parameters (P/V/I)
        """
        for x in range(1,self.numSensors+1):
            address = self.registers.get('SensorDescription')
            self.instr.register_config_cache(address, x)
            self.instr.register_read_queue(address, x, 'string')

            address = self.registers.get('SensorUnits')
            self.instr.register_config_cache(address, x)
            self.instr.register_read_queue(address, x, 'string')

            # Cache sensor data
            address = self.registers.get('SensorData')
            self.instr.register_config_cache(address, x)


    def update(self):
        """
        Update the following values:

            * Sensor Values
            * Control Angles (Phi AB/AD/DC)
        """
        for x in range(1, self.numSensors+1):
            address = self.registers.get('SensorData')
            self.instr.register_read_queue(address, x, 'float')

    #===========================================================================
    # Sensors
    #===========================================================================

    def setCalibration(self, sensor, gain, offset):
        pass

    def getCalibration(self, sensor):
        pass

    def getSensorValue(self, sensor):
        address = self.registers.get('SensorData')
        return float(self.instr.register_read(address, sensor, 'float'))

    def getSensorType(self, sensor):
        ret = {}

        address = self.registers.get('SensorDescription')
        try:
            ret['description'] = self.instr.register_read(address, sensor, 'string')
        except:
            ret['description'] = 'Unknown'

        address = self.registers.get('SensorUnits')
        try:
            ret['units'] = self.instr.register_read(address, sensor, 'string')
        except:
            ret['units'] = '?'

        return ret

    #===========================================================================
    # Parameters
    #===========================================================================

    def commitParameters(self):
        address = self.registers.get('MMCParameters')
        #return self.instr.register_write(address, 0x4, 1, 'int8');
        # Implement this in the bridge

    def getVoltage(self):
        address = self.registers.get('MMCParameters')
        return self.instr.register_read(address, 0x01, 'float')

    def setVoltage(self, set_v):
        address = self.registers.get('MMCParameters')
        return self.instr.register_write(address, 0x1, set_v, 'float');

    def getCurrent(self):
        address = self.registers.get('MMCParameters')
        return self.instr.register_read(address, 0x02, 'float')

    def setCurrent(self, set_i):
        address = self.registers.get('MMCParameters')
        return self.instr.register_write(address, 0x2, set_i, 'float');

    def getPower(self):
        address = self.registers.get('MMCParameters')
        return self.instr.register_read(address, 0x03, 'float')

    def setPower(self, set_p):
        address = self.registers.get('MMCParameters')
        return self.instr.register_write(address, 0x3, set_p, 'float');

    def getSensorValue(self, sensor):
        return self._getRegisterValue(0x2122, sensor)


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

    def open(self):
        # Configure the COM Port
        self.configure(baudrate=115200,
                                timeout=0.25,
                                bytesize=8,
                                parity='E',
                                stopbits=1)

        # Attempt to get the status
        self.getStatus()

    def close(self):
        pass

    def getProperties(self):
        return {
            'deviceVendor':     'UPEL',
            'deviceModel':      'BDPC Serial'
        }

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
        self.write_raw(packet)
        self.logger.debug("SRC TX: %s", packet.encode('hex'))

    def _SRC_read_packet(self):
        """
        Scans the serial buffer for an SRC packet. Must be called multiple times
        if multiple packets are in the serial buffer

        :returns: tuple (address, data) if found, None otherwise
        """
        while (self.inWaiting() > 0):
            # Read the next byte in the serial buffer
            buf = self.read_raw(1)
            # Check if the byte is a START_SYNC
            if (buf == chr(0x24)):
                bytesWaiting = self.inWaiting()
                if (bytesWaiting >= (self.pkt_struct.size - 1)):
                    # Retrieve the rest of the packet
                    buf = buf + self.read_raw(self.pkt_struct.size - 1)

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
                    buf = buf + self.read_raw(self.inWaiting())
                    self.logger.error("SRC RX Incomplete Packet: %s", buf.encode('hex'))

        return None

    def read_register(self, address):
        if self.getResourceStatus() != common.status.error:
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
            self.setResourceStatus(common.status.error)

            raise RuntimeError()

        else:
            raise RuntimeError()

    def write_register(self, address, data):
        if self.getResourceStatus() != common.status.error:
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
            self.setResourceStatus(common.status.unresponsive)

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
        gain_a = self.read_register(address_a)

        address_b = self.registers.get('GAINB_RO')
        gain_b = self.read_register(address_b)

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


class m_BDPC_BR2(Base_Driver, Base_ICP):
    """

    """

    info = {
        # Device Manufacturer
        'deviceVendor':         'UPEL',
        # List of compatible device models
        'deviceModel':          ['BDPC 2kW Dual-SRC6'],
        # Device type
        'deviceType':           'DC-DC Converter',

        # List of compatible resource types
        'validResourceTypes':   ['ICP']
    }

    def getProperties(self):
        return {
            'deviceVendor':     self.info['deviceVendor'],
            'deviceModel':      'BDPC Dual 2kW'
        }


class m_BDPC_BR32(Base_Driver, Base_Serial):
    """

    """

    info = {
        # Device Manufacturer
        'deviceVendor':         'UPEL',
        # List of compatible device models
        'deviceModel':          ['BDPC 32kW'],
        # Device type
        'deviceType':           'DC-DC Converter',

        # List of compatible resource types
        'validResourceTypes':   ['Serial']
    }

    def open(self):
        # Set the controller into passthrough mode
        #self.write("mode 2\n")
        pass

    def close(self):
        # Set the controller into debug mode
        #magic = struct.pack('BB', 0x24, 0x1E)
        #self.write(magic)
        pass

    def _SRC_comm_reset(self):
        self.logger.warning("Reset SRC Communication Link")
        magic = struct.pack('BB', 0x24, 0x1E)
        self.write(magic)
        time.sleep(0.1)
        self.write("mode 2\n")

    def getProperties(self):
        return {
            'deviceVendor':     self.info['deviceVendor'],
            'deviceModel':      'BDPC 32kW'
        }


class m_BDPC_SRC6(Base_Driver, Base_Serial):
    """

    """

    info = {
        # Device Manufacturer
        'deviceVendor':         'UPEL',
        # List of compatible device models
        'deviceModel':          ['BDPC 1kW SRC6'],
        # Device type
        'deviceType':           'DC-DC Converter',

        # List of compatible resource types
        'validResourceTypes':   ['Serial']
    }

    def getProperties(self):
        return {
            'deviceVendor':     self.info['deviceVendor'],
            'deviceModel':      'BDPC Dual 2kW'
        }
