from InstrumentControl import InstrumentControl

import threading
import logging
import inspect
import time
import sys

import Tkinter as Tk

class Base_Script(object):
    """
    Base object for tests
    
    Tests are a collection of scripts to test the functionality of a 
    device-under-test (DUT). They are not necessarily limited to regression
    testing for software, but can also be used to test physical devices.
    """
    
    TIMER_UPDATE_TESTS = 250
    TIMER_UPDATE_INSTR = 1000
    
    _instruments = []
    _test_methods = [] # List of all test methods
    _tests = []
    
    _g_instruments = []
    _g_tests = []
    
    def __init__(self):
        """
        Test Initialization
        
        - Attempt to connect to the local InstrumentManager instance
        - Get a list of test methods
        - Initialize the logger
        - Draw the GUI window
        """
        # Instantiate a logger
        self.logger = logging.getLogger(__name__)
        
        self.instr = InstrumentControl(logger=self.logger)
        
        # Get a list of class attributes, identify test methods
        # Test methods must be prefixed by 'test_'
        for func in dir(self.__class__):
            test = getattr(self.__class__, func)
            if func.startswith('test_') and inspect.ismethod(test):
                new_test = {}
                new_test['name'] = func
                new_test['method'] = func
                self._test_methods.append(new_test)
                
        # Create a lock object to prevent multiple tests from running at once
        self.testLock = threading.Lock()
        
        self.open()
        
        self._runGUI()
        
    def _startup(self):
        ready = True
        
        # Register all required instruments as object attributes in self
        for req_instr in self._g_instruments:
            if req_instr.getStatus():
                # Register instruments as test attributes
                attr_name = req_instr.getAttributeName()
                instr_obj = req_instr.getInstrument()

                self.logger.debug("Attr [%s] registered", attr_name)
                
                if type(instr_obj) == list and len(instr_obj) == 1:
                    setattr(self, attr_name, instr_obj[0])
                else:
                    setattr(self, attr_name, instr_obj)                        
            else:
                ready = False
                
        if not ready:
            self.logger.error("Not all instruments are ready")
        else:
            if self.startup():
                for test in self._g_tests:
                    test.enable()


        self.logger.info("All instruments enumerated and registered")
                
        return ready
    
    def _shutdown(self):
        for test in self._g_tests:
            test.stop()
            
        res = self.shutdown()
        
        if res:
            for test in self._g_tests:
                test.disable()
                
        return res
    
    def _runTests(self):
        for test in self._g_tests:
            test.run()
            test.wait()
        
    def _runGUI(self):
        self.myTk = Tk.Tk()
        master = self.myTk
        
        master.wm_title(self.test_info.get('name', 'Run Tests'))
        master.config(padx=10, pady=10)
        
        #=======================================================================
        # Instruments
        #=======================================================================
        Tk.Label(master, text="Required Instruments:").pack()
        
        try:
            if len(self._instruments) > 0:
                # Create an instrument element for each instrument
                for instr_details in self._instruments:
                    temp_instr = self.g_InstrElement(master, self.instr, instr_details)
                    temp_instr.pack(fill=Tk.BOTH)
                    
                    self._g_instruments.append(temp_instr)
                    
        except:
            raise
        
        #=======================================================================
        # Test State
        #=======================================================================
        Tk.Label(master, text="Test State:").pack()
        
        self.state_controller = self.g_StateController(master, self._startup, self._shutdown, self._runTests)
        self.state_controller.pack(fill=Tk.BOTH)
        
        #=======================================================================
        # Tests
        #=======================================================================
        Tk.Label(master, text="Tests:").pack()
        
        if len(self._tests) > 0:
            # Create a test element for each test method
            for reg_test in self._tests:
                elem = self.g_TestElement(master, self, reg_test, self.logger, self.testLock)
                elem.pack()
                
                self._g_tests.append(elem)
                
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
        # Update Required Instruments
        for instr in self._g_instruments:
            instr.updateStatus()
            
        self.myTk.after(self.TIMER_UPDATE_INSTR, self._Timer_UpdateInstruments)
        
    #===========================================================================
    # Helper Functions
    #===========================================================================
    
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
        :param serial: Optional - Serial number to identify instrument
        :type serial: str
        :param model: Optional - Model number to identify instrument
        :type model: str
        :param type: Optional - Instrument type to identify instrument
        :type type: str
        :param driver: Optional - Instrument driver (Model) to identify instrument)
        :type driver: str
        """
        kwargs['name'] = name
        kwargs['object'] = attr_name
        self._instruments.append(kwargs)
        
    def registerTest(self, name, method_name):
        """
        Notify the test framework to register a test function.
        
        :param name: Human readable test name
        :type name: str
        :param method_name: Method name
        :type method_name: str
        """
        new_test = {}
        new_test['name'] = name
        new_test['method'] = method_name
        
        self._tests.append(new_test)
        
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
        
        def __init__(self, master, ICF, instr_details):
            Tk.Frame.__init__(self, master)
            
            assert type(instr_details) == dict
            
            self.ICF = ICF
            self.instr_details = instr_details
            
            self.l_name = Tk.Label(self, text=instr_details.get('name', 'Instrument'), font=("Helvetica", 10), width=40, anchor=Tk.W)
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
            
        def updateStatus(self):
            assert type(self.instr_details) == dict
            
            if self.instr_details.get('serial', None) is not None:
                # Serial
                instr_serial = self.instr_details.get('serial')
                self.instr = self.ICF.getInstrument_serial(instr_serial)
            
            elif self.instr_details.get('model', None) is not None:
                # Model
                instr_model = self.instr_details.get('model')
                self.instr = self.ICF.getInstrument_model(instr_model)
                if len(self.instr) == 0:
                    self.instr = None
            
            elif self.instr_details.get('type', None) is not None:
                # Type
                instr_type = self.instr_details.get('type')
                self.instr = self.ICF.getInstrument_type(instr_type)
                if len(self.instr) == 0:
                    self.instr = None
                    
            elif self.instr_details.get('driver', None) is not None:
                # Driver
                instr_driver = self.instr_details.get('driver')
                self.instr = self.ICF.getInstrument_driver(instr_driver)
                if len(self.instr) == 0:
                    self.instr = None
                    
            if self.instr is not None:
                self.status.set("Ready")
                self.l_status.config(fg='green3')
                
            else:
                self.status.set("Not Present")
                self.l_status.config(fg='red')
            
        def getStatus(self):
            if self.instr is not None:
                return True
            
            else:
                return False
            
        def getInstrument(self):
            return self.instr
        
        def getAttributeName(self):
            return self.instr_details.get('object', None)
        
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
        
        def __init__(self, master, testObject, test_details, logger, lock):
            Tk.Frame.__init__(self, master, padx=3, pady=3)
            
            self.logger = logger
            self.lock = lock
            
            self.testMethodName = test_details.get('method')
            self.testName = test_details.get('name')
            
            self.testMethod = getattr(testObject, self.testMethodName)
            self.active = False
            
            self.state = 0
            self.v_state = Tk.StringVar()
            self.b_state = Tk.Button(self, textvariable=self.v_state, command=self.cb_buttonPressed, width=5)
            self.b_state.pack(side=Tk.LEFT)
            
            self.l_name = Tk.Label(self, text=self.testName, font=("Helvetica", 12), width=30, anchor=Tk.W, justify=Tk.LEFT)
            self.l_name.pack(side=Tk.LEFT)
            
            self.b_run = Tk.Button(self, text="Run", command=self.run, width=5)
            self.b_run.pack(side=Tk.LEFT)
            
            self.status = Tk.StringVar()
            self.l_status = Tk.Label(self, textvariable=self.status, font=("Helvetica", 12), width=10, justify=Tk.CENTER)
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
            """
            Run the test in a new thread
            """
            stateIdent = self.states[self.state]
            
            if stateIdent == "On":
                self.testThread = threading.Thread(target=self._run_thread)
                self.testThread.start()
            
        def wait(self):
            if self.testThread is not None:
                self.testThread.join()
                
        def stop(self):
            pass
            
        def _run_thread(self):
            """
            Test Thread handler
            """
            try:
                with self.lock:
                    self.testResult = self.testMethod()
                
            except:
                self.logger.exception("Exception while running test")
                self.testResult = False
            
