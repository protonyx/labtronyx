from Base_Applet import Base_Applet

import Tkinter as Tk

import matplotlib
import pylab

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

class v_Oscilloscope(Base_Applet):
    
    info = {
        # View revision author
        'author':               'KKENNEDY',
        # View version
        'version':              '1.0',
        # Revision date of View version
        'date':                 '2015-02-11',    
        
        # List of compatible models
        'validDrivers':          ['Tektronix.Oscilloscope.m_MixedSignal', 
                                  'Tektronix.Oscilloscope.m_Oscilloscope']
    }
    
    def _plot(self):
        if self.model.data != {}:
            keys = self.model.data.keys()
            keys.remove('Time')
        
            for ch in keys:
                x = self.model.data[ch]
                a.plot(self.model.data['Time'], x)
        
    def run(self):
        self.myTk = Tk.Tk()
        master = self.myTk
        self.myTk.wm_title("Tektronix Oscilloscope")
        
        matplotlib.use('TkAgg')
        
        # MatPlot Figure
        self.figure = Figure(figsize=(5,4), dpi=100)
        a = self.figure.add_subplot(111)
            
        # GUI Figure
        self.figureFrame = Tk.Frame(master)
        self.figureFrame.grid(row=0,column=0)
        self.canvas = FigureCanvasTkAgg(self.figure, self.figureFrame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.myTk)
        self.toolbar.update()
        
        # GUI Controls
        self.controlsFrame = Tk.Frame(master)
        self.controlsFrame.grid(row=0,column=1)
        self.btnSingle = Tk.Button(self.controlsFrame, text="Single", command=self.cb_Single)
        self.btnSingle.grid(row=0,column=0)
        
        self.myTk.mainloop()
        
        #pylab.plot(self.data['Time'], self.data['CH4'])
        #pylab.show()
        
        
    def stop(self):
        self.myTk.quit()
        self.myTk.destroy()
        
    def cb_Single(self):
        pass
        
        