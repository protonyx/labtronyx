
import views
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
    
    validVIDs = ['UPEL']
    validPIDs = []
    
    def run(self):
        # List of GUI elements to update
        self.update_elems = []
        self.wm_title("BDPC")
         
        #=======================================================================
        # Parameters
        #=======================================================================
        self.frame_param = Tk.LabelFrame(self, text="Parameters", padx=5, pady=5)
        self.param_v = ICP_Value_ReadWrite(self.frame_param, self.model,
                                           label="Voltage", units="V", 
                                           read_cb=self.model.getVoltage, write_cb=self.model.setVoltage)
        self.param_v.pack()
        self.param_i = ICP_Value_ReadWrite(self.frame_param, self.model,
                                           label="Current", units="A", 
                                           read_cb=self.model.getCurrent, write_cb=self.model.setCurrent)
        self.param_i.pack()
        self.param_p = ICP_Value_ReadWrite(self.frame_param, self.model,
                                           label="Power", units="W", 
                                           read_cb=self.model.getPower, write_cb=self.model.setPower)
        self.param_p.pack()
        self.param_setall = ICP_Button(self.frame_param, self.model,
                                            label="Set All", button_label="Set", cb_func=self.cb_setAllParams)
        self.param_setall.pack()
        self.frame_param.grid(row=0, column=0)
        
        #=======================================================================
        # Diagnostics
        #=======================================================================
        self.frame_diag = Tk.LabelFrame(self, text="Diagnostics", padx=5, pady=5)
        self.diag_efficiency = ICP_Value_Read(self.frame_diag, self.model,
                                              label="Efficiency", units="%", read_cb=self.model.getEfficiency)
        self.diag_efficiency.pack()
        self.diag_convRatio = ICP_Value_Read(self.frame_diag, self.model,
                                              label="Conversion Ratio", units="", read_cb=self.model.getConversionRatio)
        self.diag_convRatio.pack()
        self.diag_mainController = ICP_Launch_Window(self.frame_diag, self.model,
                                                     label="Main Controller", window_class=None)
        self.diag_mainController.pack()
        self.diag_auxController = ICP_Launch_Window(self.frame_diag, self.model,
                                                     label="Aux Controllers", window_class=None)
        self.diag_auxController.pack()
        self.frame_diag.grid(row=0, column=1)
        
        self.update_elems.append(self.diag_efficiency)
        self.update_elems.append(self.diag_convRatio)
        
        #=======================================================================
        # Operation
        #=======================================================================
        self.frame_ops = Tk.LabelFrame(self, text="Operation", padx=5, pady=5)
        # Operation State
        self.ops_mode = ICP_Operation_Mode(self.frame_ops, self.model)
        self.ops_mode.pack()
        self.update_elems.append(self.ops_mode)
        # Refresh Interval
        
        # Refresh Toggle
        self.ops_refresh_toggle = ICP_Value_Toggle(self.frame_ops, self.model,
                                                   label="Auto Update", states=["Off", "On"], cb=self.cb_refreshToggle)
        self.ops_refresh_toggle.pack()
        # Immediate update
        self.ops_update_immed = ICP_Button(self.frame_ops, self.model,
                                           label="Update Immediately", button_label="Update", cb_func=self.update)
        self.ops_update_immed.pack()
        self.frame_ops.grid(row=0, column=2)
        
        #=======================================================================
        # Primary
        #=======================================================================
        self.frame_primary = Tk.LabelFrame(self, text="Primary", padx=5, pady=5)
        self.pri_sensor_voltage = ICP_Sensor(self.frame_primary, self.model, 1)
        self.pri_sensor_voltage.pack()
        self.pri_sensor_current = ICP_Sensor(self.frame_primary, self.model, 3)
        self.pri_sensor_current.pack()
        self.pri_power = ICP_Value_Read(self.frame_primary, self.model, 
                                        label="Input Power", units="W", read_cb=self.model.getPrimaryPower)
        self.pri_power.pack()
        self.frame_primary.grid(row=1, column=0)
        
        self.update_elems.append(self.pri_sensor_voltage)
        self.update_elems.append(self.pri_sensor_current)
        self.update_elems.append(self.pri_power)
        
        # Picture Frame
        
        # Secondary
        self.frame_secondary = Tk.LabelFrame(self, text="Secondary", padx=5, pady=5)
        self.sec_sensor_voltage = ICP_Sensor(self.frame_secondary, self.model, 2)
        self.sec_sensor_voltage.pack()
        self.sec_sensor_current = ICP_Sensor(self.frame_secondary, self.model, 4)
        self.sec_sensor_current.pack()
        self.sec_power = ICP_Value_Read(self.frame_secondary, self.model, 
                                        label="Output Power", units="W", read_cb=self.model.getSecondaryPower)
        self.sec_power.pack()
        self.frame_secondary.grid(row=1, column=2)
        
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
    
class BDPC_Graph(Tk.Toplevel):
    
    def __init__(self):
        pass
    
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
