
import views
from common.widgets import *
#import common.widgets as vw

import Tkinter as Tk

from . import *

class v_BDPC(views.v_Base):
    """
    Base BDPC View. Collects and displays the following information:
    
    Parameters:
        * Closed-Loop MMC Parameters (P/V/I)
        * Phase Shift from SYNC
    
    Operation:
        * Operation Mode (Switching On/Off)
        * Data Refresh interval

    Primary:
        * Sensors (Current, Voltage)
        * Power
        
    Secondary:
        * Sensors (Current, Voltage)
        * Power
        
    Diagnostics:
        * Efficiency
        * Conversion Ratio
    """
    
    validModels = ['models.UPEL.BDPC.m_BDPC_BR2',
                   'models.UPEL.BDPC.m_BDPC_BR32',
                   'models.UPEL.BDPC.m_BDPC']
    
    def run(self):
        # TODO: Make this work
        # self.model = self.getModelObject()
        
        # List of GUI elements to update
        self.update_elems = []
        self.wm_title("BDPC")
         
        #=======================================================================
        # Parameters
        #=======================================================================
        self.frame_param = Tk.LabelFrame(self, text="Parameters", padx=5, pady=5)
        self.param_v = vw_entry.vw_GetSetValue(self.frame_param,
                                           get_cb=self.model.getVoltageReference, 
                                           set_cb=self.model.setVoltageReference,
                                           label="Voltage", units="V")
        self.param_v.pack()
        
        self.param_i = vw_entry.vw_GetSetValue(self.frame_param,
                                        get_cb=self.model.getCurrentReference, 
                                        set_cb=self.model.setCurrentReference,
                                        label="Current", units="A")
        self.param_i.pack()
        
        self.param_p = vw_entry.vw_GetSetValue(self.frame_param,
                                        get_cb=self.model.getPowerReference, 
                                        set_cb=self.model.setPowerReference,
                                        label="Power", units="W")
        self.param_p.pack()
        
        self.param_setall = vw_state.vw_Trigger(self.frame_param,
                                          cb_func=self.cb_setAllParams,
                                          label="Set All", button_label="Set")
        self.param_setall.pack()
        
        # Switching Control
        self.ops_switching = vw_state.vw_Toggle(self.frame_param,
                                       cb_func=lambda x: self.model.setOptions(enable_switching=x),
                                       label="Switching")
        self.ops_refresh_toggle.pack()
        
        # Refresh Toggle
        self.ops_refresh_toggle = vw_state.vw_Toggle(self.frame_param,
                                            label="Auto Update", 
                                            cb_func=self.cb_refreshToggle)
        self.ops_refresh_toggle.pack()
        
        # Immediate update
        self.ops_update_immed = vw_state.w_Trigger(self.frame_param,
                                           label="Update Immediately", button_label="Update", 
                                           cb_func=self.update)
        self.ops_update_immed.pack()
        
        self.frame_param.grid(row=0, column=0)
        
        #=======================================================================
        # Diagnostics
        #=======================================================================
        self.frame_diag = Tk.LabelFrame(self, text="Diagnostics", padx=5, pady=5)
        self.diag_efficiency = vw_entry.vw_GetValue(self.frame_diag,
                                           get_cb=self.model.getEfficiency,
                                           label="Efficiency", units="%")
        self.diag_efficiency.pack()
        self.diag_convRatio = vw_entry.vw_GetValue(self.frame_diag,
                                          get_cb=self.model.getConversionRatio,
                                          label="Conversion Ratio", units="")
        self.diag_convRatio.pack()
        self.frame_diag.grid(row=1, column=0)
        
        self.update_elems.append(self.diag_efficiency)
        self.update_elems.append(self.diag_convRatio)
        
        #=======================================================================
        # Operation
        #=======================================================================
#===============================================================================
#         self.frame_ops = Tk.LabelFrame(self, text="Operation", padx=5, pady=5)
#         # Operation State
#         self.ops_mode = ICP_Operation_Mode(self.frame_ops, self.model)
#         self.ops_mode.pack()
#         self.update_elems.append(self.ops_mode)
# 
#         self.frame_ops.grid(row=0, column=2)
#===============================================================================
        
        #=======================================================================
        # Primary
        #=======================================================================
        self.frame_primary = Tk.LabelFrame(self, text="Primary", padx=5, pady=5)
        self.pri_sensor_voltage = BDPC_Sensor(self.frame_primary, self.model, 'PrimaryVoltage')
        self.pri_sensor_voltage.pack()
        self.pri_sensor_current = BDPC_Sensor(self.frame_primary, self.model, 'PrimaryCurrent')
        self.pri_sensor_current.pack()
        self.pri_power = vw_entry.vw_GetValue(self.frame_primary, 
                                        label="Input Power", units="W", 
                                        get_cb=self.model.getPrimaryPower)
        self.pri_power.pack()
        self.frame_primary.grid(row=0, column=1)
        
        self.update_elems.append(self.pri_sensor_voltage)
        self.update_elems.append(self.pri_sensor_current)
        self.update_elems.append(self.pri_power)
        
        # Secondary
        self.frame_secondary = Tk.LabelFrame(self, text="Secondary", padx=5, pady=5)
        self.sec_sensor_voltage = BDPC_Sensor(self.frame_secondary, self.model, 'SecondaryVoltage')
        self.sec_sensor_voltage.pack()
        self.sec_sensor_current = BDPC_Sensor(self.frame_secondary, self.model, 'SecondaryCurrent')
        self.sec_sensor_current.pack()
        self.sec_power = vw_entry.vw_GetValue(self.frame_secondary, 
                                        label="Output Power", units="W", 
                                        get_cb=self.model.getSecondaryPower)
        self.sec_power.pack()
        self.frame_secondary.grid(row=1, column=1)
        
        self.update_elems.append(self.sec_sensor_voltage)
        self.update_elems.append(self.sec_sensor_current)
        self.update_elems.append(self.sec_power)
    
    def update(self):
        """
        Update all elements in the window. Makes a call to the Model
        update function to quickly queue all operations
        """
        self.model.update()
        
        for elem in self.update_elems:
            try:
                elem.update()
            except:
                pass
        
    def cb_refreshToggle(self):
        pass
    
    def cb_setAllParams(self):
        v = float(self.param_v.get())
        i = float(self.param_i.get())
        p = float(self.param_p.get())
        
        new_v = self.model.setVoltage(v)
        new_i = self.model.setCurrent(i)
        new_p = self.model.setPower(p)
        self.model.commitParameters()
        
        self.param_v.set(new_v)
        self.param_i.set(new_i)
        self.param_p.set(new_p)
    
class BDPC_Sensor(vw.vw_Base):
    """
    ICP Sensor Class is a specific type of register for
    sensors.
    
    TODO: Add Calibration editor
    """
    
    def __init__(self, master, model, sensor):
        vw.vw_Base.__init__(self, master, 8, 2)
        
        self.model = model
        
        name = self.model.getSensorDescription(sensor)
        units = self.model.getSensorUnits(sensor)
        
        self.vw_SensorValue = vw_entry.vw_GetValue(self, label=name, units=units, 
                                          get_cb=lambda: self.model.getSensorValue(sensor))
        
    def get(self):
        return self.vw_SensorValue.get()
        
    def update(self):
        self.vw_SensorValue.update()
    
class BDPC_MainController(Tk.Toplevel):
    """
    Main Controller:
        * Closed-Loop Controller Gain
        * Power Command
        * MMC Droop Resistance
        * Dead Time (Td)
        
    Minimum Current Trajectory (MCT):
        * Power Command
        * Conversion Ratio
        * Phi AB, AD, DC
    
    """
    pass

class BDPC_AuxController(Tk.Toplevel):
    """
    Auxiliary Leg Controllers:
    
        * Angle Command (ACMD or Phi')
        * Desired ZVS current
        * Measured ZVS current
        * Minimum Angle Command
        
    Aux Controller Programmable Parameters:
    
        * Dead Time (Tda)
        * Open Loop Angle Command
    """
    pass
