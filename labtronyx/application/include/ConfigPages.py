import Tkinter as Tk

import serial

class config_Serial(Tk.Toplevel):
    
    std_baud = ['50', '75', '110', '134', '150', '200', '300', '600', '1200', 
                '1800', '2400', '4800', '9600', '19200', '38400', '57600', 
                '115200', '230400', '460800', '500000', '576000', '921600', 
                '1000000', '1152000', '1500000', '2000000', '2500000', 
                '3000000', '3500000', '4000000']
    
    valid_baudrates = ['9600', '19200', '38400', '57600', '115200']
    
    valid_parity = [serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD,
                    serial.PARITY_MARK, serial.PARITY_SPACE]
    
    valid_bits = [serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS, 
                  serial.EIGHTBITS]
    
    valid_stop = [serial.STOPBITS_ONE, serial.STOPBITS_TWO]
    
    def __init__(self, master, resource):
        Tk.Toplevel.__init__(self, master)
        
        self.wm_title("Serial Configuration")
        
        self.resource = resource
        
        try:
            config = self.resource.getConfiguration()
        except Exception as e:
            tkMessageBox.showerror(e.__class__.__name__, e.message)
            self.destroy()
        
        # Baud
        Tk.Label(self, text="Baud Rate").grid(row=0, column=0)
        self.str_baudrate = Tk.StringVar(self)
        self.lst_baud = Tk.OptionMenu(self, self.str_baudrate, *self.valid_baudrates)
        self.lst_baud.config(width=20)
        self.lst_baud.grid(row=0, column=1, 
                           sticky=Tk.N+Tk.E+Tk.S+Tk.W, padx=5, pady=5)
        
        # Bits
        Tk.Label(self, text="Frame Size").grid(row=1, column=0)
        self.str_bits = Tk.StringVar(self)
        self.lst_bits = Tk.OptionMenu(self, self.str_bits, *self.valid_bits)
        self.lst_bits.grid(row=1, column=1, 
                           sticky=Tk.N+Tk.E+Tk.S+Tk.W, padx=5, pady=5)
        
        # Parity
        Tk.Label(self, text="Parity").grid(row=2, column=0)
        self.str_parity = Tk.StringVar(self)
        self.lst_parity = Tk.OptionMenu(self, self.str_parity, *self.valid_parity)
        self.lst_parity.grid(row=2, column=1, 
                           sticky=Tk.N+Tk.E+Tk.S+Tk.W, padx=5, pady=5)
        
        # Stop Bits
        Tk.Label(self, text="Stop Bits").grid(row=3, column=0)
        self.str_stop = Tk.StringVar(self)
        self.lst_stop = Tk.OptionMenu(self, self.str_stop, *self.valid_stop)
        self.lst_stop.grid(row=3, column=1, 
                           sticky=Tk.N+Tk.E+Tk.S+Tk.W, padx=5, pady=5)
        
        # Buttons
        self.btn_cancel = Tk.Button(self, text='Cancel', command=lambda: self.cb_cancel())
        self.btn_cancel.grid(row=4, column=0, padx=5, pady=5)
        self.btn_save = Tk.Button(self, text='Save', command=lambda: self.cb_save())
        self.btn_save.grid(row=4, column=1, padx=5, pady=5)
        
        # Set values
        self.str_baudrate.set(config.get('baudrate'))
        self.str_bits.set(config.get('bytesize'))
        self.str_parity.set(config.get('parity'))
        self.str_stop.set(config.get('stopbits'))
        
        # Make this dialog modal
        self.focus_set()
        self.grab_set()
        
    def cb_cancel(self):
        self.destroy()
    
    def cb_save(self):
        try:
            self.resource.configure(baudrate=self.str_baudrate.get(),
                                bytesize=self.str_bits.get(),
                                parity=self.str_parity.get(),
                                stopbits=self.str_stop.get())
        except Exception as e:
            tkMessageBox.showerror(e.__class__.__name__, e.message)
        
        self.destroy()