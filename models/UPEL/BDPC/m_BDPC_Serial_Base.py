import threading
from . import m_BDPC_Base

class m_BDPC_Serial_Base(m_BDPC_Base):
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_Serial']
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validVIDs = ['']
    validPIDs = ['']
    
    pkt_struct = struct.Struct("BBBHHB")
    
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
        'AVGQ_A': 0x35,
        'AVGQ_B': 0x36,
        'AVGQ_C': 0x37,
        'AVGQ_D': 0x38
        }
        
    def _onLoad(self):
        self.instr = self.controller._getInstrument(self.resID)
        
        # Configure the COM Port
        self.instr.baudrate = 115200
        self.instr.timeout = 0.5
        self.instr.bytesize = 8
        self.instr.parity = 'E'
        self.instr.stopbits = 1
        
        self.instr.open()
        
    def _onUnload(self):
        self.instr.close()
        
    def _SRC_pack(self, address, data):
        return self.pkt_struct.pack(0x24, address, address, data, data, 0x1E)
    
    def _SRC_unpack(self, packet):
        assert len(packet) == self.pkt_struct.size
        
        _, addr1, addr2, data1, data2, _ = self.pkt_struct.unpack(packet)
        
        assert addr1 == addr2
        assert data1 == data2
        
        return (addr1, data1)
        
    def _SRC_read_register(self, address):
        addr = address & 0x7F
        
        packet = self._SRC_pack(addr, 0)
        
        self.instr.write(packet)
        recv_pkt = self.instr.read(self.pkt_struct.size)
        
        return self._SRC_unpack(recv_pkt)
    
    def _SRC_write_register(self, address, data):
        addr = address | 0x80
        
        packet = self._SRC_pack(addr, data)
        
        self.instr.write(packet)
        recv_pkt = self.instr.read(self.pkt_struct.size)
        
        return self._SRC_unpack(recv_pkt)
    
    def getVoltage(self):
        address = self.registers.get('VLIMIT')
        return self._SRC_read_register(address)
    
    def setVoltage(self, set_v):
        address = self.registers.get('VLIMIT')
        return self._SRC_write_register(address, set_v);
    
    def getCurrent(self):
        address = self.registers.get('ILIMIT')
        return self._SRC_read_register(address)
    
    def setCurrent(self, set_i):
        address = self.registers.get('ILIMIT')
        return self._SRC_write_register(address, set_i);
    
    def getPower(self):
        address = self.registers.get('PLIMIT')
        return self._SRC_read_register(address)
    
    def setPower(self, set_p):
        address = self.registers.get('PLIMIT')
        return self._SRC_write_register(address, set_p);