from . import vw_Base

import Tkinter as Tk
from aifc import data

class vw_Plot(vw_Base):
    """
    Plotting Widget for views.
    
    Dependencies:
    
        * matplotlib
        * numpy
        
    """
    # Data
    methods = {} # (Model object, Method) -> 'last', 'data'
    
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
        :param title: Plot title
        :type title: str
        """
        vw_Base.__init__(self, master, 8, 1)
        
        # Plot parameters
        self.max_samples = kwargs.get('sample_depth', 100)
        self.sample_time = kwargs.get('sample_interval', 0.1)
        self.update_time = int(kwargs.get('update_interval', 0.25) * 1000)
        self.sampling = kwargs.get('start', False)
        self.title = kwargs.get('title', 'Generic Plot')
        
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
            
            #===================================================================
            # GUI Elements
            #===================================================================
            # Figure
            self.fig = matplotlib.figure.Figure(figsize=(4,3), facecolor='w')
            self.subplot_1 = self.fig.add_subplot(1, 1, 1)
            self.subplot_1.grid(True)
            self.fig.suptitle(self.title)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self)
            self.canvas.show()
            self.canvas.get_tk_widget().grid(row=0, column=0)
    
            #===================================================================
            # Buttons
            #===================================================================
            self.frame_control = Tk.Frame(self)
            # Start/Stop
            self.txt_btnRun = Tk.StringVar()
            self.txt_btnRun.set('Start')
            self.sampling = False
            self.btnRun = Tk.Button(self.frame_control, textvariable=self.txt_btnRun, command=self.cb_run)
            self.btnRun.pack()
            # Export
            # TODO
            # Options
            # TODO
            self.frame_control.grid(row=0, column=1)
            
            # Update plot
            self.event_update()
            
        except ImportError:
            Tk.Label(self, text="Missing Dependencies!").pack()
        
    def addPlot(self, model, method, **kwargs):
        """
        :param model: Model object
        :type model: object
        :param method: Y-Axis data method name
        :type method: str
        """
        key = (model, method)
        self.methods[key]['dataset'] = self.subplot_1.plot(self.time_axis, self.data)
        
        if self.sampling == True:
            self.startSampling()
        else:
            self.stopSampling()
        
    def startSampling(self):
        for model, method in self.methods:
            model.startCollector(method, self.sample_time, self.max_samples)

    def stopSampling(self):
        for model, method in self.methods:
            model.stopCollector(method)

    def cb_run(self):
        if self.sampling == False:
            self.startSampling()
            self.txt_btnRun.set('Stop')
            self.sampling = True
        else:
            
            self.stopSampling()
            self.txt_btnRun.set('Start')
            self.sampling = False
        
        
    def event_update(self):
        if self.sampling:
            for plot_key, plot_attr in self.methods.items():
                model, method = plot_key
                
                new_data = self.model.getCollector(method, plot_attr.get('lastTime',0))
                
                try:
                    data = plot_attr.get('data', [])
                 
                    for timestamp, sample in new_data:
                        plot_attr['lastTime'] = timestamp
                        data.append(sample)
                     
                    if len(data) > self.max_samples:
                        self.data = self.data[(-1 * self.max_samples):]
                        
                    plot_attr['data'] = data
                    
                    dataset = plot_attr.get('dataset')
                    dataset.set_data(self.time_axis, self.data)
                    
                    # Autoscale axis
                    self.subplot_1.axis([0, self.sample_time*self.max_samples, min(self.data)*1.10, max(self.data)*1.10])
                    
                    self.canvas.draw()
                    
                except:
                    pass
        
        self.after(self.update_time, self.event_update)
        
class vw_XYPlot(Tk.Frame):
    pass