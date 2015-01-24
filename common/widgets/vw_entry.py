from . import vw_Base

import Tkinter as Tk

#__all__ = ['vm_GetSetValue', 'vw_GetValue']

class vw_GetSetValue(vw_Base):
    """
    Widget to get and set values        
    """
    def __init__(self, master, get_cb, set_cb, **kwargs):
        """
        :param label: String L
        """
        vw_Base.__init__(self, master, 8, 1)
        
        self.get_cb = get_cb
        self.set_cb = set_cb
        
        # Label
        if 'label' in kwargs:
            label = kwargs.get('label')
            self.l_name = Tk.Label(self, width=10, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
            self.l_name.pack(side=Tk.LEFT)
        
        # Set Button
        self.b_set = Tk.Button(self, text="Set", command=self.cb_set)
        self.b_set.pack(side=Tk.RIGHT)
        
        # Get Button
        if 'update_interval' not in kwargs:
            self.b_get = Tk.Button(self, text="Get", command=self.cb_get)
            self.b_get.pack(side=Tk.RIGHT, padx=3)
        
        # Units
        if 'units' in kwargs:
            units = kwargs.get('units')
            self.l_units = Tk.Label(self, width=2, font=("Purisa", 12), text=units)
            self.l_units.pack(side=Tk.RIGHT)
        
        # Data
        self.val = Tk.StringVar()
        self.val.set("0")
        self.txt_data = Tk.Entry(self, width=6, textvariable=self.val)
        self.txt_data.pack(side=Tk.RIGHT)
        
        self.update_interval = kwargs.get('update_interval', None)
        
        self.e_update()
        
    def e_update(self):
        """
        Event to handle self-updating
        """
        self.cb_update()
        
        if self.update_interval is not None:
            self.after(self.update_interval, self.e_update)
        
    def get(self):
        # Get the value in the entry
        return self.val.get()
    
    def set(self, val):
        # Set the value in the entry
        self.val.set(val)
        # Also trigger the callback
        cb_set()
    
    def cb_update(self):
        val = self.get_cb()
        self.val.set(val)
        
    def cb_get(self):
        try:
            val = self.get_cb()
            
            self.val.set(val)
            
        except:
            self.txt_data.config(bg='red')
        
    def cb_set(self):
        try:
            self.set_cb(self.val.get())
            
        except:
            self.txt_data.config(bg='red')
            
class vw_GetValue(vw_Base):
    # Data Type?
    def __init__(self, master, get_cb, **kwargs):
        vw_Base.__init__(self, master, 8, 1)
        
        self.get_cb = get_cb
        
        # Label
        if 'label' in kwargs:
            label = kwargs.get('label')
            self.l_name = Tk.Label(self, width=10, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
            self.l_name.pack(side=Tk.LEFT)
            
        # Get Button
        self.b_set = Tk.Button(self, text="Get", command=self.update)
        self.b_set.pack(side=Tk.RIGHT, padx=3)
        
        # Units
        if 'units' in kwargs:
            units = kwargs.get('units')
            self.l_units = Tk.Label(self, width=2, font=("Purisa", 12), text=units)
            self.l_units.pack(side=Tk.RIGHT)

        # Data
        self.val = Tk.StringVar()
        self.val.set("0")
        self.l_data = Tk.Label(self, width=6, font=("Purisa", 10), textvariable=self.val, relief=Tk.RIDGE)
        self.l_data.pack(side=Tk.RIGHT)
        
    def get(self):
        return self.val.get()
        
    def update(self):
        try:
            val = self.get_cb()
            val = "{:.2f}".format(val)
            
            self.val.set(val)
            
        except:
            self.l_data.config(bg="red")