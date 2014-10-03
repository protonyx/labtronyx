"""
UPEL View Helper Classes
"""

import Tkinter as Tk

class ICP_Widget(Tk.Frame):
    def __init__(self, master, model):
        Tk.Frame.__init__(self, master, padx=2, pady=2)
        
class ICP_Operation_Mode(ICP_Widget):
    def __init__(self, master, model):
        ICP_Widget.__init__(self, master, model)
        
        # Current Mode
        Tk.Label(self, font=("Purisa", 12), text="Current Mode:", anchor=Tk.W, justify=Tk.LEFT).grid(row=0, column=0)
        self.mode = Tk.StringVar()
        self.mode.set("Off")
        self.l_mode = Tk.Label(self, font=("Purisa", 12), textvariable=self.mode)
        self.l_mode.grid(row=0, column=1)
        
        # Set Mode
        Tk.Label(self, font=("Purisa", 12), text="Set Mode:", anchor=Tk.W, justify=Tk.LEFT).grid(row=1, column=0)
        self.mode_next = Tk.StringVar()
        self.mode_next.set("On")
        self.b_mode = Tk.Button(self, textvariable=self.mode_next, command=self.cb_set)
        self.b_mode.grid(row=1, column=1)
        
    def update(self):
        state = self.model.getOperationMode()
        self.mode.set(state)
        
        state_next = self.model.getValidOperationTransitions()
        self.mode_next.set(state_next)
    
    def cb_set(self, mode):
        pass
        
class ICP_Launch_Window(ICP_Widget):
    def __init__(self, master, model, label, window_class):
        ICP_Widget.__init__(self, master, model)
        
        self.window_class = window_class
        self.window_obj = None
        
        # Label
        self.l_name = Tk.Label(self, width=15, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
        self.l_name.pack(side=Tk.LEFT)

        # Launch Button
        self.b_launch = Tk.Button(self, text="Open", command=self.cb_open)
        self.b_launch.pack(side=Tk.LEFT)
        
    def cb_open(self):
        if self.window_obj is None:
            try:
                self.window_obj = self.window_class()
                
            except:
                # TODO: Popup!
                pass

class ICP_Value_Read(ICP_Widget):
    # Data Type?
    def __init__(self, master, model, label, units, read_cb):
        ICP_Widget.__init__(self, master, model)
        
        self.read_cb = read_cb
        
        # Label
        self.l_name = Tk.Label(self, width=15, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
        self.l_name.pack(side=Tk.LEFT)

        # Data
        self.val = Tk.StringVar()
        self.val.set("0")
        self.l_data = Tk.Label(self, width=5, font=("Purisa", 12), textvariable=self.val, relief=Tk.RIDGE)
        self.l_data.pack(side=Tk.LEFT)
        
        # Units
        self.l_units = Tk.Label(self, font=("Purisa", 12), text=units)
        self.l_units.pack(side=Tk.LEFT)
        
    def update(self):
        val = self.read_cb()
        self.val.set(val)

class ICP_Value_ReadWrite(ICP_Widget):
    def __init__(self, master, model, label, units, read_cb, write_cb):
        ICP_Widget.__init__(self, master, model)
        
        self.read_cb = read_cb
        self.write_cb = write_cb
        
        # Label
        self.l_name = Tk.Label(self, width=15, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
        self.l_name.pack(side=Tk.LEFT)
        
        # Data
        self.val = Tk.StringVar()
        self.val.set("0")
        self.txt_data = Tk.Entry(self, width=5, textvariable=self.val)
        self.txt_data.pack(side=Tk.LEFT)
        
        # Units
        self.l_units = Tk.Label(self, font=("Purisa", 12), text=units)
        self.l_units.pack(side=Tk.LEFT)
        
        # Set Button
        self.b_set = Tk.Button(self, text="Set", command=self.cb_set)
        self.b_set.pack(side=Tk.LEFT)
    
    def update(self):
        val = self.read_cb()
        self.val.set(val)
        
    def cb_set(self):
        try:
            self.write_cb(self.val.get())
            
        except:
            pass

class ICP_Value_Toggle(ICP_Widget):
    def __init__(self, master, model, label, states=None, cb=None):
        ICP_Widget.__init__(self, master, model)
        
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
        self.b_state.pack(side=Tk.LEFT)
        
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
        
