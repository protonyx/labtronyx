from Base_Applet import Base_Applet

import Tkinter as Tk

from widgets import *

class source(Base_Applet):
    
    info = {
        # View revision author
        'author':               'KKENNEDY',
        # View version
        'version':              '1.0',
        # Revision date of View version
        'date':                 '2015-03-11',    
        
        # List of compatible models
        'validDrivers':          ['BK_Precision.Source.m_911X',
                                  'BK_Precision.Source.m_XLN',
                                  'Chroma.Source.m_620XXP',
                                  'Regatron.m_GSS']
    }
    
    def run(self):
        self.wm_title("DC Source")
        
        self.instr = self.getInstrument()
        prop = self.instr.getProperties()
        
        # Driver info
        self.w_info = vw_info.vw_DriverInfo(self, self.instr)
        self.w_info.grid(row=0, column=0, columnspan=2)
        
        #=======================================================================
        # Configuration
        #=======================================================================
        self.f_conf = Tk.LabelFrame(self, text="Configuration")
        
        # Power
        self.w_power_on = vw_state.vw_Trigger(self.f_conf,
                                          cb_func=self.instr.powerOn,
                                          label="Power On",
                                          button_label="Power On")
        self.w_power_on.pack()
        self.w_power_off = vw_state.vw_Trigger(self.f_conf,
                                          cb_func=self.instr.powerOff,
                                          label="Power Off",
                                          button_label="Power Off")
        self.w_power_off.pack()
        
        # Voltage
        if 'Voltage' in prop.get('controlModes', []):
            self.w_voltage = vw_entry.vw_Text(self.f_conf,
                                           get_cb=self.instr.getVoltage,
                                           set_cb=self.instr.setVoltage,
                                           label='Voltage')
            self.w_voltage.pack()
        
        # Current
        if 'Current' in prop.get('controlModes', []):
            self.w_current = vw_entry.vw_Text(self.f_conf,
                                           get_cb=self.instr.getCurrent,
                                           set_cb=self.instr.setCurrent,
                                           label='Current')
            self.w_current.pack()
        
        # Power
        if 'Power' in prop.get('controlModes', []):
            self.w_power = vw_entry.vw_Text(self.f_conf,
                                           get_cb=self.instr.getPower,
                                           set_cb=self.instr.setPower,
                                           label='Power')
            self.w_power.pack()
        
        self.f_conf.grid(row=1, column=0)
        
        #=======================================================================
        # Protection
        #=======================================================================
        self.f_prot = Tk.LabelFrame(self, text="Protection")
        
        # Over Voltage
        if 'Voltage' in prop.get('protectionModes', []):
            self.w_prot_v = vw_entry.vw_Text(self.f_prot, 
                                          get_cb=lambda: self.instr.getProtection().get('Voltage'),
                                          set_cb=lambda voltage: self.instr.setProtection(voltage=voltage),
                                          label="Voltage")
            self.w_prot_v.pack()
            
        # Over Current
        if 'Current' in prop.get('protectionModes', []):
            self.w_prot_i = vw_entry.vw_Text(self.f_prot, 
                                          get_cb=lambda: self.instr.getProtection().get('Current'),
                                          set_cb=lambda current: self.instr.setProtection(current=current),
                                          label="Current")
            self.w_prot_i.pack()
            
        # Over Current
        if 'Power' in prop.get('protectionModes', []):
            self.w_prot_p = vw_entry.vw_Text(self.f_prot, 
                                          get_cb=lambda: self.instr.getProtection().get('Power'),
                                          set_cb=lambda power: self.instr.setProtection(power=power),
                                          label="Power")
            self.w_prot_p.pack()
        
        self.f_prot.grid(row=2, column=0)
        
        #=======================================================================
        # Data
        #=======================================================================
        self.f_data = Tk.LabelFrame(self, text="Data")
        
        # Voltage
        if 'Voltage' in prop.get('terminalSense', []):
            self.w_data_v = vw_entry.vw_LCD(self.f_data, 
                                          get_cb=self.instr.getTerminalVoltage,
                                          label="Voltage",
                                          update_interval=1000)
            self.w_data_v.pack()
        
        # Current
        if 'Current' in prop.get('terminalSense', []):
            self.w_data_i = vw_entry.vw_LCD(self.f_data, 
                                          get_cb=self.instr.getTerminalCurrent,
                                          label="Current",
                                          update_interval=1000)
            self.w_data_i.pack()
            
        # Power
        if 'Power' in prop.get('terminalSense', []):
            self.w_data_p = vw_entry.vw_LCD(self.f_data, 
                                          get_cb=self.instr.getTerminalPower,
                                          label="Power",
                                          update_interval=1000)
            self.w_data_p.pack()
        
        
        self.f_data.grid(row=1, column=1)
