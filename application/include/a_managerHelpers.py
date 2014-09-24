import Tkinter as Tk

class a_ConnectToHost(Tk.Toplevel):
    
    def __init__(self, master, cb_func):
        Tk.Toplevel.__init__(self, master)
        
        # Store reference to parent window callback function
        self.cb_func = cb_func
        
        self.wm_title('Connect to host...')
        Tk.Label(t, text='Connect to remote host').grid(row=0, column=0, columnspan=2)
        Tk.Label(t, text='Address or Hostname').grid(row=1, column=0)
        self.txt_address = Tk.Text(t)
        self.txt_address.grid(row=1, column=1)
        Tk.Button()
        
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
        
class a_ViewSelector(Tk.Toplevel):
    
    def __init__(self, master, cb_func):
        Tk.Toplevel.__init__(self, master)
        
        # Store reference to parent window callback function
        self.cb_func = cb_func
        
        self.wm_title('Connect to host...')
        Tk.Label(t, text='Connect to remote host').grid(row=0, column=0, columnspan=2)
        Tk.Label(t, text='Address or Hostname').grid(row=1, column=0)
        self.txt_address = Tk.Text(t)
        self.txt_address.grid(row=1, column=1)
        Tk.Button()
        
        # Make this dialog modal
        self.focus_set()
        self.grab_set()