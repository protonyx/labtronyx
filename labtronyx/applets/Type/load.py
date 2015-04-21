from Base_Applet import Base_Applet

import Tkinter as Tk

from widgets import *

class load(Base_Applet):
    
    info = {
        # Description
        'description':          'Generic view for DC Loads',   
        
        # List of compatible models
        'validDrivers':          ['drivers.BK_Precision.Load.m_85XX',
                                  'drivers.TDI.d_XBL']
    }
    
    def run(self):
        self.wm_title("DC Load")
        
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
        
        # Mode
        self.w_mode = vw_entry.vw_List(self.f_conf, 
                                       values=prop.get('validModes', []),
                                       get_cb=self.instr.getMode,
                                       set_cb=self.instr.setMode,
                                       label='Mode')
        self.w_mode.pack()
        
        # Trigger Source
        self.w_trig_source = vw_entry.vw_List(self.f_conf, 
                                       values=prop.get('validTriggerSources', []),
                                       get_cb=self.instr.getTriggerSource,
                                       set_cb=self.instr.setTriggerSource,
                                       label='Trigger Source')
        self.w_trig_source.pack()
        
        # Trigger
        self.w_trig = vw_state.vw_Trigger(self.f_conf,
                                          cb_func=self.instr.trigger,
                                          label="Bus Trigger",
                                          button_label="Trigger")
        self.w_trig.pack()
        
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
            
        # Resistance
        if 'Resistance' in prop.get('controlModes', []):
            self.w_res = vw_entry.vw_Text(self.f_conf,
                                           get_cb=self.instr.getResistance,
                                           set_cb=self.instr.setResistance,
                                           label='Resistance')
            self.w_res.pack()
        
        self.f_conf.grid(row=1, column=0)
        
        #=======================================================================
        # Data
        #=======================================================================
        self.f_data = Tk.LabelFrame(self, text="Data")
        
        # Voltage
        if 'Voltage' in prop.get('terminalSense', []):
            self.w_data_v = vw_entry.vw_LCD(self.f_data, 
                                          get_cb=self.instr.getTerminalVoltage,
                                          label="Voltage",
                                          units='V',
                                          update_interval=1000)
            self.w_data_v.pack()
        
        # Current
        if 'Current' in prop.get('terminalSense', []):
            self.w_data_i = vw_entry.vw_LCD(self.f_data, 
                                          get_cb=self.instr.getTerminalCurrent,
                                          label="Current",
                                          units='A',
                                          update_interval=1000)
            self.w_data_i.pack()
            
        # Power
        if 'Power' in prop.get('terminalSense', []):
            self.w_data_p = vw_entry.vw_LCD(self.f_data, 
                                          get_cb=self.instr.getTerminalPower,
                                          label="Power",
                                          units='W',
                                          update_interval=1000)
            self.w_data_p.pack()
        
        self.f_data.grid(row=1, column=1)