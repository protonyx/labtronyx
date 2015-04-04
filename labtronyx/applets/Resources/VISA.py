"""
.. codeauthor:: Kevin Kennedy <kennedy.kevin@gmail.com>
"""
from Base_Applet import Base_Applet

import Tkinter as Tk

from widgets import *

class VISA(Base_Applet):
    
    info = {
        # Description
        'description':          'Generic view for VISA Resources',  
            
        # List of compatible resource types
        'validResourceTypes':   ['VISA']
    }

    def run(self):
        self.wm_title("VISA Resource")

        self.instr = self.getInstrument()

        # Driver info
        self.w_info = vw_info.vw_DriverInfo(self, self.instr)
        self.w_info.grid(row=0, column=0, columnspan=2)

        # Send
        self.send_val = Tk.StringVar(self)
        self.lbl_send = Tk.Label(self, width=20,
                                 text="Send Command",
                                 anchor=Tk.W, justify=Tk.LEFT)
        self.lbl_send.grid(row=1, column=0)
        self.txt_send = Tk.Entry(self, width=40,
                                 textvariable=self.send_val)
        self.txt_send.grid(row=1, column=1)

        # Buttons
        self.f_buttons = Tk.Frame(self, padx=5, pady=5)
        self.btn_write = Tk.Button(self.f_buttons,
                                  text="Write",
                                  command=self.cb_write,
                                  width=10,
                                  padx=3)
        self.btn_write.pack(side=Tk.LEFT)
        self.btn_query = Tk.Button(self.f_buttons,
                                   text="Query",
                                   command=self.cb_query,
                                   width=10,
                                   padx=3)
        self.btn_query.pack(side=Tk.LEFT),
        self.btn_read = Tk.Button(self.f_buttons,
                                  text="Read",
                                  command=self.cb_read,
                                  width=10,
                                  padx=3)
        self.btn_read.pack(side=Tk.LEFT)
        self.f_buttons.grid(row=2, column=1)

        # Receive
        self.lbl_receive = Tk.Label(self, width=20,
                                    text="Received Data",
                                    anchor=Tk.W, justify=Tk.LEFT)
        self.lbl_receive.grid(row=3, column=0)
        self.txt_receive = Tk.Text(self, state=Tk.DISABLED,
                                   width=20, height=10)
        self.txt_receive.grid(row=3, column=1,
                              sticky=Tk.N+Tk.E+Tk.S+Tk.W)

    def cb_write(self):
        data = self.send_val.get()

        self.instr.write(data)

    def cb_query(self):
        self.cb_write()
        self.cb_read()

    def cb_read(self):
        data = self.instr.read()

        self.txt_receive.configure(state=Tk.NORMAL)
        self.txt_receive.delete(1, Tk.END)
        self.txt_receive.insert(Tk.END, data)
        self.txt_receive.configure(state=Tk.DISABLED)

