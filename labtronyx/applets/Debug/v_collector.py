from Base_Applet import Base_Applet

import Tkinter as Tk

#debug
import numpy as np

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler

class v_collector(Base_Applet):
    
    info = {
        # View revision author
        'author':               'KKENNEDY',
        # View version
        'version':              '1.0',
        # Revision date of View version
        'date':                 '2015-02-11',  
        # Description
        'description':          'Collector test view',  
            
        # List of compatible Models
        'validModels':          ['models.Test.m_test']
    }
    
    lastTime = 0.0
    data = []
    max_samples = 100
    sample_time = 0.10
    
    sampling = False
        
    def run(self):
        self.wm_title("Collector Test")
        
        # Initialize Data
        # self.time_axis = [x/self.sample_time for x in xrange(0, self.max_samples)]
        self.time_axis = np.arange(0.0, self.max_samples * self.sample_time, self.sample_time)
        self.data = [0.0] * self.max_samples
        
        # GUI Elements
        # Figure
        self.fig = matplotlib.figure.Figure(figsize=(5,4))
        self.subplot_1 = self.fig.add_subplot(111)
        self.dataset_1 = self.subplot_1.plot(self.time_axis, self.data)
        self.subplot_1.grid(True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.show()
        self.canvas.get_tk_widget().grid(row=0,column=0,columnspan=2)

        # Buttons
        self.btnStart = Tk.Button(self, text="Start", command=self.cb_start)
        self.btnStart.grid(row=1,column=0)
        self.btnStop = Tk.Button(self, text="Stop", command=self.cb_stop)
        self.btnStop.grid(row=1,column=1)
        
        # Update plot
        self.event_update()
        
    def cb_start(self):
        self.model.startCollector('doCos', self.sample_time, self.max_samples)
        self.sampling = True
        
    def cb_stop(self):
        self.model.stopCollector('doCos')
        self.sampling = False
        
    def event_update(self):
        
        if self.sampling:
            try:
                new_data = self.model.getCollector('doCos', self.lastTime)
                 
                for timestamp, sample in new_data:
                    self.lastTime = timestamp
                    self.data.append(sample)
                 
                if len(self.data) > self.max_samples:
                    self.data = self.data[(-1 * self.max_samples):]
                
                #self.data = np.sin(2*np.pi*t)
                
                # Update plot data    
                self.dataset_1[0].set_data(self.time_axis, self.data)
                
                # Autoscale axis
                self.subplot_1.axis([0, self.sample_time*self.max_samples, min(self.data)*1.10, max(self.data)*1.10])
                
                self.canvas.draw()
            
            except Exception as e:
                print 'exception'
        
        self.after(250, self.event_update)