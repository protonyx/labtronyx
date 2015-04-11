from InstrumentManager import InstrumentManager

import threading
import logging
import inspect
import time
import sys
import Queue

import Tkinter as Tk

class Base_Script(object):
    """
    Base object for scripts
    
    Contains a set of helper functions and a pre-built GUI for rapid development
    of scripts for lab instrument automated testing
    """
    
    TIMER_UPDATE_TESTS = 250
    TIMER_UPDATE_INSTR = 1000
    
    def __init__(self):
        # Instantiate a logger
        self.logger = logging.getLogger(__name__)
        
        # Instantiate InstrumentManager
        self.instr = InstrumentManager(logger=self.logger, enableRpc=False)

        # Initialize instance variables
        self.__instruments = []
        self.__tests = []
    
        self.__g_instruments = []
        self.__g_tests = []
    
        self.__test_queue = Queue.Queue()
        self.__test_curr = None
    
        # Run the script startup routine
        try:
            self.open()
        except NotImplementedError:
            # Get a list of class attributes, identify test methods
            # Test methods must be prefixed by 'test_'
            for func in dir(self.__class__):
                test = getattr(self.__class__, func)
                if func.startswith('test_') and inspect.ismethod(test):
                    self.registerTest(func, func)
        
        # Start test runner thread
        self.__test_run_thread = threading.Thread(target=self.__main_runner)
        
        # Keep the main thread occupied with the GUI
        self.__main_gui()
        
    def __prepare(self):
        """
        Register all required instruments as attributes in the script object.
        
        Run before every test function
        """
        for req_instr in self.__g_instruments:
            if req_instr.getStatus():
                # Register instruments as test attributes
                attr_name = req_instr.getAttributeName()
                instr_obj = req_instr.getInstrument()
                
                if type(instr_obj) == list and len(instr_obj) == 1:
                    setattr(self, attr_name, instr_obj[0])
                else:
                    setattr(self, attr_name, instr_obj)                        
            else:
                ready = False
                
        self.logger.info("All instruments enumerated and registered")
        
    def _queue_test(self, test):
        if test.getState() == 'On' and not self._queue_contains(test):
            self.__test_queue.put(test, False)
            
    def _queue_contains(self, test):
        return test in self.__test_queue.queue
    
    def _queue_all(self):
        for test in self._g_tests:
            self._queue_test(test)
          
    def __main_runner(self):
        """
        Main thread for the test runner
        """
        pass
        
    def __main_gui(self):
        """
        Main thread for the GUI
        """
        self.myTk = Tk.Tk()
        master = self.myTk
        
        master.wm_title(self.test_info.get('name', 'Run Tests'))
        master.config(padx=10, pady=10)
        
        #=======================================================================
        # Instruments
        #=======================================================================
        Tk.Label(master, text="Required Instruments:").pack()
        
        try:
            if len(self.__instruments) > 0:
                # Create an instrument element for each instrument
                for instr_details in self.__instruments:
                    temp_instr = self.g_InstrElement(master, self.instr, instr_details)
                    temp_instr.pack(fill=Tk.BOTH)
                    
                    self.__g_instruments.append(temp_instr)
                    
        except:
            raise
        
        #=======================================================================
        # Test State
        #=======================================================================
        Tk.Label(master, text="Test Control:").pack()
        
        self.state_controller = self.g_StateController(master, self._queue_all)
        self.state_controller.pack(fill=Tk.BOTH)
        
        #=======================================================================
        # Tests
        #=======================================================================
        Tk.Label(master, text="Tests:").pack()
        
        self.f_tests = Tk.Frame(master)
        if len(self._tests) > 0:
            # Create a test element for each test method
            for test_name, test_method in self._tests:
                elem = self.g_TestElement(self.f_tests, self, 
                                          name=test_name,
                                          method_name=test_method, 
                                          logger=self.logger)
                elem.pack()
                
                self._g_tests.append(elem)
        self.f_tests.pack(fill=Tk.BOTH)
        #self.f_run = Tk.Frame(master)
        
        #=======================================================================
        # Console Logger
        #=======================================================================
        # Logger GUI Element
        Tk.Label(master, text="Test Log:").pack()
        self.logConsole = self.g_ConsoleLogger(master) #Tk.Text(master)
        self.logConsole.configure(state=Tk.DISABLED, width=60, height=15)
        self.logConsole.columnconfigure(0, weight=1)
        self.logConsole.rowconfigure(0, weight=1)
        self.logConsole.pack(fill=Tk.BOTH)
        
        # Configure Logger
        self.logFormatter = logging.Formatter('%(message)s')
        self.logger.setLevel(logging.DEBUG)
        h_textHandler = self.g_ConsoleLoggerHandler(self.logConsole)
        h_textHandler.setFormatter(self.logFormatter)
        self.logger.addHandler(h_textHandler)
        
        #=======================================================================
        # Run GUI
        #=======================================================================
        self._Timer_UpdateTests()
        self._Timer_UpdateInstruments()
        self.myTk.mainloop()
        
    #===========================================================================
    # Timers
    #===========================================================================
    
    def _Timer_UpdateTests(self):
        # Update GUI elements
        for test in self._g_tests:
            test.updateStatus()
            
        self.myTk.after(self.TIMER_UPDATE_TESTS, self._Timer_UpdateTests)
        
    def _Timer_UpdateInstruments(self):
        ready = True
        # Update Required Instruments
        for instr in self.__g_instruments:
            instr.cb_update()
            status = instr.getStatus()
            if not status:
                ready = False
            
        # If ready, enable all tests
        if ready:
            for test in self._g_tests:
                test.enable()
        else:
            for test in self._g_tests:
                test.disable()
            
        self.myTk.after(self.TIMER_UPDATE_INSTR, self._Timer_UpdateInstruments)
        
    #===========================================================================
    # Helper Functions
    #===========================================================================
    
    def open(self):
        """
        Script startup routine. Contains all of the code to register tests and
        notify the test framework of any required instruments.
        
        If not implemented by subclass, all methods beginning with 'test_' will
        be registered by default.
        """
        raise NotImplementedError
    
    def requireInstrument(self, name, attr_name, **kwargs):
        """
        Notify the test framework to require an Instrument. Instrument will be
        registered as an attribute during test startup. At least one of the
        optional arguments must be provided to correctly identify an 
        instrument.
        
        :param name: Human readable instrument name
        :type name: str
        :param attr_name: Attribute to register
        :type attr_name: str

        :param interface: Interface
        :param resourceID: Interface Resource Identifier (Port, Address, etc.)
        :param resourceType: Resource Type (Serial, VISA, etc.)
        :param deviceVendor: Instrument Vendor
        :param deviceModel: Instrument Model Number
        :param deviceSerial: Instrument Serial Number
        :param deviceType: Instrument Type
        """
        self.__instruments.append((name, attr_name, kwargs))
        
    def registerTest(self, name, method_name):
        """
        Notify the test framework to register a test function.
        
        :param name: Human readable test name
        :type name: str
        :param method_name: Method name
        :type method_name: str
        """
        self.__tests.append((name, method_name))
        
    #===========================================================================
    # Test Runner
    #===========================================================================
    
    class TestRunner(threading.Thread):
        
        def __init__(self):
            super(TestRunner, self).__init__()
            self._running = threading.Event()
            
        def stop(self):
            self._running.clear()
            
        
        
    #===========================================================================
    # GUI Frame Elements
    #===========================================================================
    class g_ConsoleLogger(Tk.Frame):
        def __init__(self, master, cnf=None, **kw):
            Tk.Frame.__init__(self, master)
            
            self.yscrollbar = Tk.Scrollbar(self)
            self.console = Tk.Text(self, cnf=cnf, yscrollcommand=self.yscrollbar.set, **kw)
            self.yscrollbar.config(command=self.console.yview)
            
            self.console.grid(row=0, column=0, sticky=Tk.N+Tk.E+Tk.S+Tk.W)            
            self.yscrollbar.grid(row=0, column=1, sticky=Tk.N+Tk.S)
        
        def config(self, cnf=None, **kw):
            return self.console.config(cnf=cnf, **kw)
        
        def configure(self, cnf=None, **kw):
            return self.console.configure(cnf=cnf, **kw)
        
        def insert(self, index, chars, *args):
            return self.console.insert(index, chars, *args)
        
        def see(self, index):
            return self.console.see(index)
        
    class g_ConsoleLoggerHandler(logging.Handler):
        """ 
        Logging handler to direct logging input to a Tkinter Text widget
        """
        def __init__(self, console):
            logging.Handler.__init__(self)
    
            self.console = console
    
        def emit(self, record):
            message = self.format(record) + '\n'
            
            # Disabling states so no user can write in it
            self.console.configure(state=Tk.NORMAL)
            self.console.insert(Tk.END, message)
            self.console.configure(state=Tk.DISABLED)
            self.console.see(Tk.END)
            
    class g_InstrElement(Tk.Frame):
        
        def __init__(self, master, labManager, instr_details):
            Tk.Frame.__init__(self, master)
            
            self.labManager = labManager
            self.name, self.attr_name, self.instr_details = instr_details
            
            self.l_name = Tk.Label(self, text=self.name, font=("Helvetica", 10), width=40, anchor=Tk.W)
            self.l_name.pack(side=Tk.LEFT)
            
            # TODO: Give information about the instrument being used?
            #===================================================================
            # self.instr_match = Tk.StringVar()
            # self.l_instr = Tk.Label(self, textvariable=self.instr_match, font=("Helvetica", 10), width=45, anchor=Tk.W)
            # self.l_instr.grid(row=1,column=0)
            #===================================================================
            
            self.status = Tk.StringVar()
            self.l_status = Tk.Label(self, textvariable=self.status, font=("Helvetica", 11), width=10, anchor=Tk.E)
            self.l_status.pack(side=Tk.RIGHT)
            
            self.instr = []
            #self.instr_sel = 0
            
        def cb_update(self):
            assert type(self.instr_details) == dict
            
            self.instr = self.labManager.findInstruments(**self.instr_details)
                    
            if len(self.instr) == 1:
                self.status.set("Ready")
                self.l_status.config(fg='green3')
                
            elif len(self.instr) > 1:
                self.status.set('Multiple Found')
                self.l_status.config(fg='red')
                
            else:
                self.status.set("Not Present")
                self.l_status.config(fg='red')
            
        def getStatus(self):
            if len(self.instr) == 1:
                return True
            
            else:
                return False
            
        def getInstrument(self):
            return self.instr[0]
        
        def getAttributeName(self):
            return self.attr_name
        
    class g_StateController(Tk.Frame):
        
        def __init__(self, master, m_startup, m_shutdown, m_run):
            Tk.Frame.__init__(self, master, padx=3, pady=3)
            
            self.state = 0
            self.m_startup = m_startup
            self.m_shutdown = m_shutdown
            self.m_run = m_run
            
            self.b_start = Tk.Button(self, text="Startup", command=self.cb_startup, width=10)
            self.b_start.pack(side=Tk.LEFT, padx=2)
            self.b_stop = Tk.Button(self, text="Shutdown", command=self.cb_shutdown, width=10, state=Tk.DISABLED)
            self.b_stop.pack(side=Tk.LEFT, padx=2)
            self.b_run = Tk.Button(self, text="Run Tests", command=self.cb_run, width=10, state=Tk.DISABLED)
            self.b_run.pack(side=Tk.LEFT, padx=2)
            
            self.status = Tk.StringVar()
            self.l_status = Tk.Label(self, textvariable=self.status, font=("Helvetica", 12), width=10, justify=Tk.CENTER)
            self.l_status.pack(side=Tk.RIGHT)
            self.status.set("Not Ready")
            
        def getState(self):
            return self.state
            
        def cb_startup(self):
            ret = self.m_startup()
            
            if ret == True:
                self.b_start.config(state=Tk.DISABLED)
                self.b_stop.config(state=Tk.NORMAL)
                self.b_run.config(state=Tk.NORMAL)
                
                self.state = 1
                self.status.set("Ready")
        
        def cb_shutdown(self):
            ret = self.m_shutdown()
            
            if ret == True:
                self.b_start.config(state=Tk.NORMAL)
                self.b_stop.config(state=Tk.DISABLED)
                self.b_run.config(state=Tk.DISABLED)
                
                self.state = 0
                self.status.set("Not Ready")
                
        def cb_run(self):
            self.m_run()
        
    class g_TestElement(Tk.Frame):
        
        states = ['On', 'Off']
        
        def __init__(self, master, scriptObject, name, method_name, logger):
            Tk.Frame.__init__(self, master, padx=3, pady=3)
            
            self.logger = logger
            
            self.testMethodName = method_name
            self.testName = name
            
            self.testMethod = getattr(scriptObject, self.testMethodName)
            self.active = False
            
            self.state = 0
            self.v_state = Tk.StringVar()
            self.b_state = Tk.Button(self, textvariable=self.v_state, width=5,
                                     command=self.cb_buttonPressed)
            self.b_state.pack(side=Tk.LEFT)
            
            self.l_name = Tk.Label(self, text=self.testName, 
                                   font=("Helvetica", 12), width=30, 
                                   anchor=Tk.W, justify=Tk.LEFT)
            self.l_name.pack(side=Tk.LEFT)
            
            self.b_run = Tk.Button(self, text="Run", width=5,
                                   command=lambda: self.scriptObject._queue_test(self))
            self.b_run.pack(side=Tk.LEFT)
            
            self.status = Tk.StringVar()
            self.l_status = Tk.Label(self, textvariable=self.status, 
                                     font=("Helvetica", 12), width=10, 
                                     justify=Tk.CENTER)
            self.l_status.pack(side=Tk.LEFT)
            
            # Set Initial state
            self.testThread = None
            self.testResult = None
            self.setState(self.state)
            
        def cb_buttonPressed(self):
            next_state = (self.state + 1) % len(self.states)
            
            self.setState(next_state)
            
        def enable(self):
            self.active = True
            self.updateState()
        
        def disable(self):
            self.active = False
            self.updateState()
                
        def setState(self, new_state):
            if new_state < len(self.states):
                self.state = new_state
                self.updateState()
            
            else:
                raise IndexError
            
        def getState(self):
            return self.states[self.state]
                
        def updateState(self):
            stateIdent = self.states[self.state]
            self.v_state.set(stateIdent)
            
            if stateIdent == "On" and self.active == True:
                self.b_run.config(state=Tk.NORMAL)
                
            elif stateIdent == "Off" and self.active == True:
                self.b_run.config(state=Tk.DISABLED)
                
            else:
                self.b_run.config(state=Tk.DISABLED)
            
            # Reset test results
            self.testThread = None
            self.testResult = None
        
        def updateStatus(self):
            if self.testThread is None:
                self.status.set("")
                
            elif self.testThread.isAlive():
                self.l_status.config(fg='gold')
                self.status.set("Running")
                
            elif not self.testThread.isAlive():
                # Return Test Status
                if self.testResult == True:
                    self.l_status.config(fg='green3')
                    self.status.set("Pass")
                    
                elif self.testResult == False:
                    self.l_status.config(fg='red')
                    self.status.set("Fail")
                    
                else:
                    self.l_status.config(fg='red')
                    self.status.set("Fail")
            else:
                self.status.set("Error")
                
        def run(self):
            try:
                self.testResult = self.testMethod()
                
            except:
                self.logger.exception("Exception while running test")
                self.testResult = False
            
            
