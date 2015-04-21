"""
UPEL View Helper Classes
"""

import Tkinter as Tk
from interfaces.icp.errors import *

import widgets as vw
        
class ICP_Operation_Mode(vw.vw_Base):
    def __init__(self, master, model):
        vw.vw_Base.__init__(self, master, 8, 2)
        
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
