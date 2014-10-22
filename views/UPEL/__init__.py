"""
UPEL View Helper Classes
"""

import Tkinter as Tk
from common.icp.errors import *

class ICP_Widget(Tk.Frame):
    PIXELS_PER_X = 30
    PIXELS_PER_Y = 30
    
    def __init__(self, master, model, units_x=8, units_y=1):
        Tk.Frame.__init__(self, master, padx=2, pady=2)
        
        self.model = model
        
        width = units_x * self.PIXELS_PER_X
        height = units_y * self.PIXELS_PER_Y
        
        self.config(width=width, height=height)
        self.pack_propagate(0)
        
class ICP_Operation_Mode(ICP_Widget):
    def __init__(self, master, model):
        ICP_Widget.__init__(self, master, model, 8, 2)
        
        # Current Mode
        self.f_cmode = Tk.Frame(self)
        Tk.Label(self.f_cmode, font=("Purisa", 12), text="Current Mode:", anchor=Tk.W, justify=Tk.LEFT).pack(side=Tk.LEFT)
        self.mode = Tk.StringVar()
        self.mode.set("")
        self.l_mode = Tk.Label(self.f_cmode, width=14, font=("Purisa", 12), textvariable=self.mode, relief=Tk.RIDGE)
        self.l_mode.pack(side=Tk.RIGHT)
        self.f_cmode.pack(fill=Tk.X)
        
        # Set Mode
        self.f_smode = Tk.Frame(self, pady=2)
        Tk.Label(self.f_smode, font=("Purisa", 12), text="Set Mode:", anchor=Tk.W, justify=Tk.LEFT).pack(side=Tk.LEFT)
        self.b_next = []
        self.f_smode.pack(fill=Tk.X)
        
        self.states = model.getStates() or {}
        self.state_transitions = model.getStateTransitions() or {}
        map(int, self.state_transitions.keys())
        self.update()
        
    def update(self):
        state = self.model.getState()
        
        state_text, _ = self.states.get(str(state), ('Invalid State', 'Invalid State'))
        # Set Current State
        self.mode.set(state_text)
        
        for widget in self.b_next:
            widget.destroy()
            del widget
        
        # Create buttons to make transitions
        for next_state in self.state_transitions.get(state, [0x81]):
            _, next_state_text = self.states.get(str(next_state), ('Invalid State', 'Invalid State'))
            b_new = Tk.Button(self.f_smode, text=next_state_text, command=lambda: self.cb_set(next_state))
            b_new.pack(side=Tk.RIGHT)
            self.b_next.append(b_new)
        
        #state_next = '???'
        #self.mode_next.set(state_next)
    
    def cb_set(self, mode):
        self.model.setState(mode)
        self.update()
                
class ICP_Launch_Window(ICP_Widget):
    def __init__(self, master, model, label, window_class):
        ICP_Widget.__init__(self, master, model, 8, 1)
        
        self.window_class = window_class
        self.window_obj = None
        
        # Label
        self.l_name = Tk.Label(self, width=15, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
        self.l_name.pack(side=Tk.LEFT)

        # Launch Button
        self.b_launch = Tk.Button(self, text="Open", command=self.cb_open)
        self.b_launch.pack(side=Tk.RIGHT)
        
    def cb_open(self):
        if self.window_obj is None:
            try:
                self.window_obj = self.window_class()
                
            except:
                # TODO: Popup!
                pass
            
class ICP_Button(ICP_Widget):
    def __init__(self, master, model, label, button_label, cb_func):
        ICP_Widget.__init__(self, master, model, 8, 1)
        
        # Label
        self.l_name = Tk.Label(self, width=15, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
        self.l_name.pack(side=Tk.LEFT)

        # Button
        self.b_button = Tk.Button(self, text=button_label, command=cb_func)
        self.b_button.pack(side=Tk.RIGHT)

class ICP_Value_Read(ICP_Widget):
    # Data Type?
    def __init__(self, master, model, label, units, read_cb):
        ICP_Widget.__init__(self, master, model, 8, 1)
        
        self.read_cb = read_cb
        
        # Label
        self.l_name = Tk.Label(self, width=15, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
        self.l_name.pack(side=Tk.LEFT)
        
        # Units
        self.l_units = Tk.Label(self, width=3, font=("Purisa", 12), text=units)
        self.l_units.pack(side=Tk.RIGHT)

        # Data
        self.val = Tk.StringVar()
        self.val.set("0")
        self.l_data = Tk.Label(self, width=6, font=("Purisa", 10), textvariable=self.val, relief=Tk.RIDGE)
        self.l_data.pack(side=Tk.RIGHT)
        
    def update(self):
        try:
            val = self.read_cb()
            val = "{:.2f}".format(val)
            
            self.val.set(val)
            
        except:
            self.l_data.config(bg="red")

class ICP_Value_ReadWrite(ICP_Widget):
    def __init__(self, master, model, label, units, read_cb, write_cb):
        ICP_Widget.__init__(self, master, model, 8, 1)
        
        self.read_cb = read_cb
        self.write_cb = write_cb
        
        # Label
        self.l_name = Tk.Label(self, width=10, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
        self.l_name.pack(side=Tk.LEFT)
        
        # Set Button
        self.b_set = Tk.Button(self, text="Set", command=self.cb_set)
        self.b_set.pack(side=Tk.RIGHT)
        
        # Get Button
        self.b_set = Tk.Button(self, text="Get", command=self.cb_get)
        self.b_set.pack(side=Tk.RIGHT, padx=3)
        
        # Units
        self.l_units = Tk.Label(self, width=2, font=("Purisa", 12), text=units)
        self.l_units.pack(side=Tk.RIGHT)
        
        # Data
        self.val = Tk.StringVar()
        self.val.set("0")
        self.txt_data = Tk.Entry(self, width=6, textvariable=self.val)
        self.txt_data.pack(side=Tk.RIGHT)
        
    def get(self):
        return self.val.get()
    
    def set(self, val):
        self.val.set(val)
    
    def update(self):
        val = self.read_cb()
        self.val.set(val)
        
    def cb_get(self):
        try:
            val = self.read_cb()
            
            self.val.set(val)
            
        except:
            self.txt_data.config(bg='red')
        
    def cb_set(self):
        try:
            self.write_cb(self.val.get())
            
        except:
            self.txt_data.config(bg='red')

class ICP_Value_Toggle(ICP_Widget):
    def __init__(self, master, model, label, states=None, cb=None):
        ICP_Widget.__init__(self, master, model, 8, 1)
        
        if states is None:
            self.states = ['Off', 'On']
        else:
            self.states = states
            
        self.state = 0
        self.cb = cb
        
        # Label
        self.l_name = Tk.Label(self, width=15, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
        self.l_name.pack(side=Tk.LEFT)
        
        self.val = Tk.StringVar()
        self.b_state = Tk.Button(self, textvariable=self.val, command=self.cb_buttonPressed)
        self.b_state.pack(side=Tk.RIGHT)
        
        # Init
        self.setState(self.state)
        
    def cb_buttonPressed(self):
        next_state = (self.state + 1) % len(self.states)
        
        self.setState(next_state)
        
        if self.cb is not None:
            self.cb()
        
    def setState(self, new_state):
        if new_state < len(self.states):
            self.state = new_state
            self.val.set(self.states[self.state])
        else:
            raise IndexError
        
    def getState(self):
        return self.state
    
    def update(self):
        pass
        
class ICP_Sensor(ICP_Value_Read):
    """
    ICP Sensor Class is a specific type of register for
    sensors.
    
    TODO: Add Calibration editor
    """
    
    def __init__(self, master, model, sensorNumber):
        self.model = model
        self.sensorNumber = sensorNumber
        
        sensor = self.model.getSensorType(sensorNumber)
        
        name = sensor.get('description', 'Sensor')
        units = sensor.get('units', '')
        
        ICP_Value_Read.__init__(self, master, model, label=name, units=units, 
                                      read_cb=lambda: self.model.getSensorValue(sensorNumber))
        
