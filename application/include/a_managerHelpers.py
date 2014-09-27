import Tkinter as Tk

class a_ConnectToHost(Tk.Toplevel):
    
    def __init__(self, master, cb_func):
        Tk.Toplevel.__init__(self, master)
        
        # Store reference to parent window callback function
        self.cb_func = cb_func
        
        self.wm_title('Connect to host...')
        Tk.Label(master, text='Connect to remote host').grid(row=0, column=0, columnspan=2)
        Tk.Label(master, text='Address or Hostname').grid(row=1, column=0)
        self.txt_address = Tk.Text(master)
        self.txt_address.grid(row=1, column=1)
        Tk.Button(master, text='Connect', command=lambda: self.cb_Add()).grid(row=2, column=0)
        
        # Make this dialog modal
        self.focus_set()
        self.grab_set()
        
    def cb_Add(self):
        address = self.txt_address.get(0)
        port = self.txt_port.get(0)
        
        self.cb_func(address, port)
        
        # Close this window
        self.destroy()
        
    def cb_Cancel(self):
        self.destroy()
        
class a_AddResource(Tk.Toplevel):
    
    def __init__(self, master, controllers, cb_func):
        Tk.Toplevel.__init__(self, master)
        
        # Store reference to parent window callback function
        self.cb_func = cb_func
        self.controller = Tk.StringVar(self)
        self.controller.set(controllers[0])
        
        self.wm_title('Add Resource')
        Tk.Label(self, text='Controller').grid(row=0, column=0)
        Tk.Label(self, text='Resource ID').grid(row=1, column=0)
        self.lst_controller = Tk.OptionMenu(self, self.controller, *controllers)
        self.lst_controller.grid(row=0, column=1, columnspan=2)
        self.txt_resID = Tk.Entry(self)
        self.txt_resID.grid(row=1, column=1, columnspan=2)
        Tk.Button(self, text='Cancel', command=lambda: self.cb_Cancel()).grid(row=2, column=1)
        Tk.Button(self, text='Connect', command=lambda: self.cb_Add()).grid(row=2, column=2)
            
        # Make this dialog modal
        #self.focus_set()
        #self.grab_set()
        
    def cb_Add(self):
        controller = self.controller.get()
        resID = self.txt_resID.get(0)
        
        self.cb_func(controller, resID)
        
        # Close this window
        self.destroy()
        
    def cb_Cancel(self):
        self.destroy()
        
class a_ViewSelector(Tk.Toplevel):
    
    def __init__(self, master, cb_func):
        Tk.Toplevel.__init__(self, master)
        
        # Store reference to parent window callback function
        self.cb_func = cb_func
        
        self.wm_title('Load a view...')
        Tk.Label(t, text='Connect to remote host').grid(row=0, column=0, columnspan=2)
        Tk.Button(t, text='').grid(row=1, column=0)
        self.txt_address = Tk.Text(t)
        self.txt_address.grid(row=1, column=1)
        Tk.Button()
        
        # Make this dialog modal
        self.focus_set()
        self.grab_set()