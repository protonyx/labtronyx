"""
Dependencies
------------
    
   * matplotlib
   
Usage Notes
-----------
     
.. note::

   Make sure to take into account the amount of time it takes to retrieve data
   from a physical device. This will depend on the interface used, the data
   transfer rate, operating system overhead and the process priority. This will 
   limit how quickly you will be able to collect data.
"""

from . import vw_Base

import Tkinter as Tk

import time
import threading

class vw_Plot(vw_Base):
    """
    Plotting Widget using matplotlib.
    """
    
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
        self.update_interval = int(kwargs.get('update_interval', 1.0) * 1000)
        self.sampling = kwargs.get('start', False)
        self.title = kwargs.get('title', 'Generic Plot')
        
        self.plot_lock = threading.Lock()
        self.sample_thread = None
        
        self.plots = {}
        self.nextID = 0
        
        try:
            # Dependent Imports
            #import numpy as np
    
            import matplotlib
            matplotlib.use('TkAgg')
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.backend_bases import key_press_handler
            
            # Initialize Data
            self.time_axis = [x/self.sample_time for x in xrange(0, self.max_samples)]
            #self.time_axis = np.arange(0.0, self.max_samples * self.sample_time, self.sample_time)
            self.data = [0.0] * self.max_samples
            
            #===================================================================
            # GUI Elements
            #===================================================================
            # Figure
            self.fig = matplotlib.figure.Figure(frameon=False, figsize=(4,3), facecolor='w')
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
            self._schedule_update()
            
        except ImportError:
            Tk.Label(self, text="Missing Dependencies!").pack()
            
    def __del__(self):
        self.stopSampling()
        
    def addPlot(self, name, method):
        """
        Add an object and method to the plot
        
        :param name: Dataset name
        :type name: str
        :param method: Data method
        :type method: str
        """
        with self.plot_lock:
            ret = {}
            
            ret['method'] = method
            ret['data'] = [0.0] * self.max_samples
            ret['dataset'] = self.subplot_1.plot(self.time_axis, ret['data'])
            ret['samples'] = self.max_samples
            ret['time'] = 0
            
            self.plots[name] = ret
            self.nextID = self.nextID + 1
    
    def addCollectorPlot(self, name, obj, method):
        """
        Add an object and method to the plot using a collector
        
        :param name: Dataset name
        :type name: str
        :param obj: Instrument object
        :type obj: object
        :param method: Y-Axis data method name
        :type method: str
        """
        with self.plot_lock:
            ret = {}
            
            ret['type'] = 'collector'
            ret['object'] = obj
            ret['method'] = method
            ret['dataset'] = self.subplot_1.plot(self.time_axis, self.data)
            ret['data'] = []
            ret['time'] = 0
            
            self.plots[self.nextID] = ret
            self.nextID = self.nextID + 1
        
    def removePlot(self, name):
        """
        Remove a data set from the plot
        
        :param name: Dataset name
        :type name: str
        """
        with self.plot_lock:
            plot = self.plots.pop(name)
            
            if plot.get('type') == 'collector':
                obj = plot.get('object')
                method = plot.get('method')
                
                obj.stopCollector(method)
        
    def startSampling(self):
        """
        Start sampling and updating the plot
        """
        for plot_name, plot_attr in self.plots.items():
            if plot_attr.get('type') == 'collector':
                obj = plot_attr.get('object')
                method = plot_attr.get('method')
                
                obj.startCollector(method, self.sample_time, self.max_samples)
            
        self.sampling = True
        
        if self.sample_thread is None:
            self.sample_thread = self.sampleThread(self)
            self.sample_thread.start()

    def stopSampling(self):
        """
        Stop sampling and updating the plot
        """
        self.sampling = False
        
        for plot_name, plot_attr in self.plots.items():
            if plot_attr.get('type') == 'collector':
                obj = plot_attr.get('object')
                method = plot_attr.get('method')
                
                obj.stopCollector(method)
                
        if self.sample_thread is not None:
            self.sample_thread.shutdown()
            self.sample_thread = None

    def cb_run(self):
        if self.sampling == False:
            self.startSampling()
            self.txt_btnRun.set('Stop')
            
        else:
            self.stopSampling()
            self.txt_btnRun.set('Start')
        
    def cb_update(self):
        if self.sampling:
            for plot_name, plot_attr in self.plots.items():
                dataset = plot_attr.get('dataset')
                data = plot_attr.get('data')
                last_time = plot_attr.get('time')
                
                with (self.plot_lock):
                    try:
                        # Update data
                        dataset[0].set_data(self.time_axis, data)
                        
                        # Autoscale axis
                        self.subplot_1.axis([self.time_axis[0], self.time_axis[-1], min(data)*0.9, max(data)*1.10])
                        
                        self.canvas.draw()
                        
                    except Exception as e:
                        self.stopSampling()
                        print e.message
                
    class sampleThread(threading.Thread):
        
        def __init__(self, plot_object):
            threading.Thread.__init__(self)
            
            self.plot_object = plot_object
            
            self.e_alive = threading.Event()
            self.e_alive.set()
        
        def run(self):
            while (self.e_alive.is_set()):
                # Iterate through all plots
                for plot_name, plot_attr in self.plot_object.plots.items():
                    dataset = plot_attr.get('dataset')
                    data = plot_attr.get('data')
                    last_time = plot_attr.get('time')
                    samples = plot_attr.get('samples', 100)
                    
                    try:
                        if plot_attr.get('type') == 'collector':
                            obj = plot_attr.get('object')
                            method = plot_attr.get('method')
                            new_data = obj.getCollector(method, last_time)
                        else:
                            method = plot_attr.get('method')
                            new_data = [(time.time(), method())]
                        
                        # Get lock to update all plots
                        with (self.plot_object.plot_lock):
                            for timestamp, sample in new_data:
                                plot_attr['time'] = timestamp
                                data.append(sample)
                                data.pop(0)
                            
                    except Exception as e:
                        pass
                
                time.sleep(self.plot_object.sample_time)
                
        def shutdown(self):
            self.e_alive.clear()
        