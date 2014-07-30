import Tkinter as Tk

class a_ConnectToHost(Tk.Toplevel):
    
    def __init__(self, master, cnf):
        Tk.Toplevel.__init__(self, master, cnf)
        
        self.wm_title('Connect to host...')
        Tk.Label(t, text='Connect to remote host').grid(row=0, column=0, columnspan=2)
        Tk.Label(t, text='Address or Hostname').grid(row=1, column=0)
        self.txt_address = Tk.Text(t)
        self.txt_address.grid(row=1, column=1)
        
    