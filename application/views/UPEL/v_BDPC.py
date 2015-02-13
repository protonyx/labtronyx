import application.views as views

from application.widgets import *

import Tkinter as Tk

# ICP Widgets
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
    
    info = {
        # View revision author
        'author':               'KKENNEDY',
        # View version
        'version':              '1.0',
        # Revision date of View version
        'date':                 '2015-02-11',    
        
        # List of compatible models
        'validModels':          ['models.UPEL.BDPC.m_BDPC_BR2',
                                 'models.UPEL.BDPC.m_BDPC_BR32',
                                 'models.UPEL.BDPC.m_BDPC_SRC6']
    }
    
    def run(self):
        # TODO: Make this work
        # self.model = self.getModelObject()
        
        # List of GUI elements to update
        self.update_elems = []
        self.wm_title("BDPC")
        
        self.model = self.getResource()
         
        self.frame_left = Tk.Frame(self)
        #=======================================================================
        # Control
        #=======================================================================
        self.frame_control = Tk.LabelFrame(self.frame_left, text="Control", padx=5, pady=5)
        
        self.ops_control = vw_state.vw_BinaryFields(self.frame_control,
                                        cb_get=self.methodWrapper(self.model, 'getOption'),
                                        cb_set=self.methodWrapper(self.model, 'setOption'),
                                        fields=self.methodWrapper(self.model, 'getOptionFields')(),
                                        names=self.methodWrapper(self.model, 'getOptionDescriptions')() )
        self.ops_control.pack()
        
        self.frame_control.pack()
        
        #=======================================================================
        # Status
        #=======================================================================
        
        self.frame_status = Tk.LabelFrame(self.frame_left, text="Status", padx=5, pady=5)
        
        self.ops_status = vw_state.vw_BinaryFields(self.frame_status,
                                        cb_get=self.methodWrapper(self.model, 'getStatus'),
                                        cb_set=None,
                                        fields=self.methodWrapper(self.model, 'getStatusFields')(),
                                        names=self.methodWrapper(self.model, 'getStatusDescriptions')(),
                                        update_interval=1000 )
        self.ops_status.pack()
        
        self.frame_status.pack()
        
        #=======================================================================
        # Parameters
        #=======================================================================
        self.frame_param = Tk.LabelFrame(self.frame_left, text="Parameters", padx=5, pady=5)
        self.param_v = vw_entry.vw_GetSetValue(self.frame_param,
                                           get_cb=self.methodWrapper(self.model, 'getVoltageReference'), 
                                           set_cb=self.methodWrapper(self.model, 'setVoltageReference'),
                                           label="Voltage", units="V")
        self.param_v.pack()
        
        self.param_i = vw_entry.vw_GetSetValue(self.frame_param,
                                        get_cb=self.methodWrapper(self.model, 'getCurrentReference'), 
                                        set_cb=self.methodWrapper(self.model, 'setCurrentReference'),
                                        label="Current", units="A")
        self.param_i.pack()
        
        self.param_p = vw_entry.vw_GetSetValue(self.frame_param,
                                        get_cb=self.methodWrapper(self.model, 'getPowerReference'), 
                                        set_cb=self.methodWrapper(self.model, 'setPowerReference'),
                                        label="Power", units="W")
        self.param_p.pack()
        
        self.param_setall = vw_state.vw_Trigger(self.frame_param,
                                          cb_func=self.cb_setAllParams,
                                          label="Set All", button_label="Set")
        self.param_setall.pack()
        
        self.frame_param.pack()
        
        self.frame_left.grid(row=0, column=0, rowspan=2)
        
        #-----------------------------------------------------------------------
        
        self.frame_middle = Tk.Frame(self)
        #=======================================================================
        # Sensors
        #=======================================================================
        self.sensor_widgets = []

        self.frame_sensors = Tk.LabelFrame(self.frame_middle, text="Sensors", padx=5, pady=5)
        sensor1 = BDPC_Sensor(self.frame_sensors, self.model, 'PrimaryVoltage',
                              update_interval=1000)
        sensor1.pack()
        self.sensor_widgets.append(sensor1)
        sensor2 = BDPC_Sensor(self.frame_sensors, self.model, 'SecondaryVoltage',
                              update_interval=1000)
        sensor2.pack()
        self.sensor_widgets.append(sensor2)
        sensor3 = BDPC_Sensor(self.frame_sensors, self.model, 'PrimaryCurrent',
                              update_interval=1000)
        sensor3.pack()
        self.sensor_widgets.append(sensor3)
        sensor4 = BDPC_Sensor(self.frame_sensors, self.model, 'SecondaryCurrent',
                              update_interval=1000)
        sensor4.pack()
        self.sensor_widgets.append(sensor4)
        self.frame_sensors.pack()
        
        self.frame_zvs = Tk.LabelFrame(self.frame_middle, text="Zero Voltage Switching (ZVS)", padx=5, pady=5)
        sensor1 = BDPC_Sensor(self.frame_zvs, self.model, 'ZVSCurrentA')
        sensor1.pack()
        self.sensor_widgets.append(sensor1)
        sensor2 = BDPC_Sensor(self.frame_zvs, self.model, 'ZVSCurrentB')
        sensor2.pack()
        self.sensor_widgets.append(sensor2)
        sensor3 = BDPC_Sensor(self.frame_zvs, self.model, 'ZVSCurrentC')
        sensor3.pack()
        self.sensor_widgets.append(sensor3)
        sensor4 = BDPC_Sensor(self.frame_zvs, self.model, 'ZVSCurrentD')
        sensor4.pack()
        self.sensor_widgets.append(sensor4)
        self.frame_zvs.pack()
        
        #=======================================================================
        # Diagnostics
        #=======================================================================
        self.frame_diag = Tk.LabelFrame(self.frame_middle, text="Diagnostics", padx=5, pady=5)
        self.pri_power = vw_entry.vw_GetValue(self.frame_diag, 
                                        label="Input Power", units="W", 
                                        get_cb=self.methodWrapper(self.model, 'getPrimaryPower'))
        self.pri_power.pack()
        self.sec_power = vw_entry.vw_GetValue(self.frame_diag, 
                                        label="Output Power", units="W", 
                                        get_cb=self.methodWrapper(self.model, 'getSecondaryPower'))
        self.sec_power.pack()
        self.diag_efficiency = vw_entry.vw_GetValue(self.frame_diag,
                                        get_cb=self.methodWrapper(self.model, 'getEfficiency'),
                                        label="Efficiency", units="%",
                                        update_interval=5000)
        self.diag_efficiency.pack()
        self.diag_convRatio = vw_entry.vw_GetValue(self.frame_diag,
                                        get_cb=self.methodWrapper(self.model, 'getConversionRatioCalc'),
                                        label="Conversion Ratio", units="")
        self.diag_convRatio.pack()
        self.diag_pcmd = vw_entry.vw_GetValue(self.frame_diag,
                                        get_cb=self.methodWrapper(self.model, 'getPowerCommand'),
                                        label="Power Command", units="%")
        self.diag_pcmd.pack()
        self.frame_diag.pack()
        
        self.frame_middle.grid(row=0, column=1, rowspan=2)
        
        #=======================================================================
        # Graphs
        #=======================================================================
        self.graph_input = vw_plots.vw_Plot(self, title="Input")
        self.graph_input.addPlot(model=self.model, method='getInputVoltage')
        self.graph_input.addPlot(model=self.model, method='getInputCurrent')
        self.graph_input.grid(row=0, column=2)
        
        self.graph_output = vw_plots.vw_Plot(self, title="Output")
        self.graph_output.addPlot(model=self.model, method='getOutputVoltage')
        self.graph_output.addPlot(model=self.model, method='getOutputCurrent')
        self.graph_output.grid(row=1, column=2)
    
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
    
    def __init__(self, master, model, sensor, **kwargs):
        vw.vw_Base.__init__(self, master, 8, 2)
        
        self.model = model
        self.sensor = sensor
        
        name = self.model.getSensorDescription(sensor)
        units = self.model.getSensorUnits(sensor)
        
        self.f_top = Tk.Frame(self)
        self.l_name = Tk.Label(self.f_top, width=25, font=("Purisa", 12), text=name, anchor=Tk.W, justify=Tk.LEFT)
        self.l_name.pack(side=Tk.LEFT)
        self.f_top.grid(row=0, column=0, sticky=Tk.N+Tk.E+Tk.W)
            
        self.f_bottom = Tk.Frame(self)
        self.l_units = Tk.Label(self.f_bottom, width=2, font=("Purisa", 12), text=units)
        self.l_units.pack(side=Tk.RIGHT)
        self.val = Tk.StringVar()
        self.val.set("0")
        self.l_data = Tk.Label(self.f_bottom, width=6, font=("Purisa", 10), textvariable=self.val, relief=Tk.RIDGE)
        self.l_data.pack(side=Tk.RIGHT)
        self.l_calibrate = Tk.Button(self.f_bottom, text="Calibrate", font=("Purisa", 10), state=Tk.DISABLED)
        self.l_calibrate.pack(side=Tk.LEFT)
        self.f_bottom.grid(row=1, column=0, sticky=Tk.E+Tk.S+Tk.W)
        
        self.update_interval = kwargs.get('update_interval', None)
        self._schedule_update()

    def cb_update(self):
        try:
            val = self.model.getSensorValue(self.sensor)
            val = "{:.2f}".format(val)
            
            self.val.set(val)
            
        except:
            self.l_data.config(bg="red")
            
    def get(self):
        return self.val.get()
    
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
