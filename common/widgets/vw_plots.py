from . import vw_Base

import Tkinter as Tk

class vw_Plot(vw_Base):
    """
    Plotting Widget for views.
    
    Dependencies:
    
        * matplotlib
        * numpy
        
    """
    # Data
    methods = [] # (Model object, Method)
    lastTime = {}
    data = []
    
    def __init__(self, master, **kwargs):
        """
        :param master: Tkinter master element
        :type master: object
        :param sample_interval: Sample interval in seconds
        :type sample_interval: float
        :param sample_depth: Number of samples to display
        :type sample_depth: int
        :param update_interval: Update interval in milliseconds
        :type update_interval: int
        :param start: Enable sampling immediately
        :type start: bool
        """
        vw_Base.__init__(self, master, 8, 1)
        
        # Plot parameters
        self.max_samples = kwargs.get('sample_depth', 100)
        self.sample_time = kwargs.get('sample_interval', 0.1)
        self.update_time = kwargs.get('update_interval', 0.25) * 1000
        self.sampling = kwargs.get('start', False)
        
        try:
            # Dependent Imports
            import numpy as np
    
            import matplotlib
            matplotlib.use('TkAgg')
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
            from matplotlib.backend_bases import key_press_handler
            
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
            self.txt_btnRun = Tk.StringVar()
            self.txt_btnRun.set('Start')
            self.sampling = False
            self.btnRun = Tk.Button(self, textvariable=self.txt_btnRun, command=self.cb_run)
            self.btnRun.grid(row=1,column=0)
            
            # Update plot
            self.cb_update()
            
        except Exception as e:
            Tk.Label(self, text="Missing Dependencies!").pack()
        
    def addPlot(self, model, method, **kwargs):
        """
        :param model: Model object
        :type model: object
        :param method: Y-Axis data method name
        :type method: str
        """
        self.methods.append((model, method))

    def cb_run(self):
        if self.sampling == False:
            for model, method in self.methods:
                model.startCollector(method, self.sample_time, self.max_samples)
                
            self.txt_btnRun.set('Stop')
            self.sampling = True
        else:
            for model, method in self.methods:
                model.stopCollector(method)
            
            self.txt_btnRun.set('Start')
            self.sampling = False
        
        
    def cb_update(self):
        
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
                pass
        
        self.after(self.update_time, self.cb_update)
        
class vw_XYPlot(Tk.Frame):
    pass