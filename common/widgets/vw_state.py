from . import vw_Base

import Tkinter as Tk

class vw_Trigger(vw_Base):
    def __init__(self, master, model, cb_func, **kwargs):
        vw_Base.__init__(self, master, model, 8, 1)
        
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
        