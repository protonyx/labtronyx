from . import vw_Base

import Tkinter as Tk

class vw_Trigger(vw_Base):
    def __init__(self, master, cb_func, **kwargs):
        vw_Base.__init__(self, master, 8, 1)
        
        # Label
        if 'label' in kwargs:
            label = kwargs.get('label')
            self.l_name = Tk.Label(self, width=15, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
            self.l_name.pack(side=Tk.LEFT)

        # Button
        button_label = kwargs.get('button_label', 'Execute')
        self.b_button = Tk.Button(self, text=button_label, command=cb_func)
        self.b_button.pack(side=Tk.RIGHT)
        
class vw_Toggle(vw_Base):
    """
    View Widget: State Toggle
    
    :param cb_func: method called when state is changed. Must accept 1 argument
    :type cb_func: bound_method    
    """
        
    def __init__(self, master, cb_func, **kwargs): #label, states=None, cb=None):
        vw_Base.__init__(self, master, 8, 1)
        
        self.states = kwargs.get('states', ['Off', 'On'])
        self.state = 0
        self.cb_func = cb_func
        
        # Label
        if 'label' in kwargs:
            label = kwargs.get('label')
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
        
        self.cb_func(self.state)
        
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

class vw_BinaryFields(vw_Base):
    field_objects = {}
    
    def __init__(self, master, cb_get, cb_set, fields):
        vw_Base.__init__(self, master, 8, 10)
        
        self.cb_get = cb_get
        self.cb_set = cb_set
        
        for key, value in fields.items():
            if cb_set is None:
                obj_temp = self.g_field_readonly(self, key, value)
            else:
                obj_temp = self.g_field_readwrite(self, cb_set, key, value)
                
            obj_temp.pack()
            self.field_objects[key] = obj_temp 
            
        self.update()

    def update(self):
        field_vals = self.cb_get()
        
        for obj in self.field_objects.values():
            obj.update(field_vals)

    class g_field_readwrite(Tk.Frame):
        def __init__(self, master, cb_func, field_name, field_desc):
            Tk.Frame.__init__(self, master)
            
            self.field_name = field_name
            self.cb_set = cb_func
            
            # Label
            self.l_name = Tk.Label(self, width=22, font=("Purisa", 12), text=field_desc, anchor=Tk.W, justify=Tk.LEFT)
            self.l_name.pack(side=Tk.LEFT)

            # Field Status
            self.b_status = Tk.Button(self, width=3, command=self.cb_buttonPressed)
            self.b_status.pack(side=Tk.RIGHT)
            
            self.state = 0
            
        def update(self, val):
            val_field = val.get(self.field_name, 0)
            
            self.state = val_field
            
            if val_field:
                self.b_status.config(bg='green')
            else:
                self.b_status.config(bg='red')
        
        def cb_buttonPressed(self):
            self.state = not self.state # invert
            field_dict = {}
            field_dict[self.field_name] = self.state
            self.cb_set(**field_dict)
            self.update(field_dict)

    class g_field_readonly(Tk.Frame):
        def __init__(self, master, field_name, field_desc):
            Tk.Frame.__init__(self, master)
            
            self.field_name = field_name
            
            # Label
            self.l_name = Tk.Label(self, width=22, font=("Purisa", 12), text=field_desc, anchor=Tk.W, justify=Tk.LEFT)
            self.l_name.pack(side=Tk.LEFT)

            # Field Status
            self.b_status = Tk.Button(self, width=3, state=Tk.DISABLED)
            self.b_status.pack(side=Tk.RIGHT)
            
            self.state = 0
            
        def update(self, val):
            val_field = val.get(self.field_name, 0)
            
            self.state = val_field
            
            if val_field:
                self.b_status.config(bg='green')
            else:
                self.b_status.config(bg='red')
                
            # Field Status
            
