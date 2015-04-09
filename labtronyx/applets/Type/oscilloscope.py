from Base_Applet import Base_Applet

import csv

import Tkinter as Tk
import tkFileDialog

import matplotlib
import pylab

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

from widgets import *

class oscilloscope(Base_Applet):
    
    info = {    
        # List of compatible models
        'validDrivers':          ['Tektronix.Oscilloscope.d_2XXX', 
                                  'Tektronix.Oscilloscope.d_5XXX7XXX']
    }
    
    def run(self):
        self.wm_title("Tektronix Oscilloscope")
        
        self.instr = self.getInstrument()
        
        matplotlib.use('TkAgg')
        
        # Driver info
        self.w_info = vw_info.vw_DriverInfo(self, self.instr)
        self.w_info.grid(row=0, sticky=Tk.W)
        
        # Controls
        self.f_controls = Tk.Frame(self, pady=5)
        self.btn_update = Tk.Button(self.f_controls, text="Update", command=self.cb_update)
        self.btn_update.grid(row=1, column=0, padx=10)
        self.btn_export = Tk.Button(self.f_controls, text="Export...", command=self.cb_export)
        self.btn_export.grid(row=1, column=1, padx=10)
        self.btn_screenshot = Tk.Button(self.f_controls, text="Save Screenshot...", command=self.cb_screenshot)
        self.btn_screenshot.grid(row=1, column=2, padx=10)
        self.f_controls.grid(row=1)
        
        # MatPlot Figure
        self.f_figure = Tk.Frame(self)
        Tk.Label(self.f_figure, text="Waveform Data").pack(side=Tk.TOP)
        self.figure = Figure(frameon=False)#(figsize=(5,4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, self.f_figure)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        self.f_figure.grid(row=2)
        
        #pylab.plot(self.data['Time'], self.data['CH4'])
        #pylab.show()
        self.data = {}
        
        self.cb_update()
        
    def cb_update(self):
        self.data = self.instr.getWaveform()
        
        self.figure.clear()
        
        if 'CH1' in self.data:
            ch1 = self.figure.add_subplot(2,2,1, title='CH1', axis_bgcolor='k')
            ch1.plot(self.data['Time'], self.data['CH1'], 'y')
            
        if 'CH2' in self.data:
            ch1 = self.figure.add_subplot(2,2,2, title='CH2', axis_bgcolor='k')
            ch1.plot(self.data['Time'], self.data['CH2'], 'b')
            
        if 'CH3' in self.data:
            ch1 = self.figure.add_subplot(2,2,3, title='CH3', axis_bgcolor='k')
            ch1.plot(self.data['Time'], self.data['CH3'], 'm')
            
        if 'CH4' in self.data:
            ch1 = self.figure.add_subplot(2,2,4, title='CH4', axis_bgcolor='k')
            ch1.plot(self.data['Time'], self.data['CH4'], 'g')
            
        self.canvas.show()
        
    def cb_export(self):
        
        filename = tkFileDialog.asksaveasfilename(defaultextension='.csv',
                                       filetypes=[('CSV files', '.csv')],
                                       title='Export Oscilloscope Data...')
        
        with open(filename, 'w+') as f:
            writer = csv.writer(f)
            for header, data in self.data.items():
                writer.writerow([header] + list(data))

    def cb_screenshot(self):
        filename = tkFileDialog.asksaveasfilename(defaultextension='.png',
                                       filetypes=[('PNG files', '.png')],
                                       title='Save Oscilloscope Screenshot...')
        
        self.instr.saveScreenshot(filename)
        