import threading
import logging
import inspect
import time
import sys
sys.path.append('..')

import Tkinter as Tk
from InstrumentControl import InstrumentControl

class t_Base(object):
    """
    Base object for tests
    
    Tests are a collection of scripts to test the functionality of a 
    device-under-test (DUT). They are not necessarily limited to regression
    testing for software, but can also be used to test physical devices.
    """
    
    TIMER_UPDATE_TESTS = 250
    TIMER_UPDATE_INSTR = 1000
    
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
        self.test_methods = []
        for func in dir(self.__class__):
            test = getattr(self.__class__, func)
            if func.startswith('test_') and inspect.ismethod(test):
                self.test_methods.append(func)
                
        # Create a lock object to prevent multiple tests from running at once
        self.testLock = threading.Lock()
        
        self.open()
        
        self._runGUI()
        
    def _runGUI(self):
        self.myTk = Tk.Tk()
        master = self.myTk
        
        master.wm_title(self.test_info.get('name', 'Run Tests'))
        master.config(padx=10, pady=10)
        
        #=======================================================================
        # Instruments
        #=======================================================================
        Tk.Label(master, text="Required Instruments:").pack()
        
        self.req_instr = []
        try:
            if len(self.test_requires) > 0:
                for instr_details in self.test_requires:
                    temp_instr = self.g_InstrElement(master, self.instr, instr_details)
                        
                    self.req_instr.append(temp_instr)
                    temp_instr.pack(fill=Tk.BOTH)
        except:
            raise
        
        #=======================================================================
        # Tests
        #=======================================================================
        Tk.Label(master, text="Tests:").pack()
        
        self.tests = []
        if len(self.test_methods) > 0:
            # Create a test element for each test method
            for func in self.test_methods:
                testDetails = self.test_details.get(func, {}) or {}
                order = testDetails.get('order', 999)
                
                elem = self.g_TestElement(master, self, func, self.logger, self.testLock)
                self.tests.append((order, elem))
                
            self.tests.sort(key=lambda x: x[0])
            
            # Pack the test elements onto the GUI
            for order, elem in self.tests:
                elem.pack()
                
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
        
        self.logger.debug("Test Initialization Finished.")
        
        #=======================================================================
        # Run GUI
        #=======================================================================
        self.cb_TimerUpdateTests()
        self.cb_TimerUpdateInstruments()
        self.myTk.mainloop()
        
    #===========================================================================
    # Callbacks
    #===========================================================================
    
    def cb_TimerUpdateTests(self):
        # Update GUI elements
        for order, test in self.tests:
            test.updateStatus()
            
        self.myTk.after(self.TIMER_UPDATE_TESTS, self.cb_TimerUpdateTests)
        
    def cb_TimerUpdateInstruments(self):
        # Update Required Instruments
        for instr in self.req_instr:
            instr.updateStatus()
            
        self.myTk.after(self.TIMER_UPDATE_INSTR, self.cb_TimerUpdateInstruments)
        
    def cb_RunAllTests(self):
        pass
        
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
            if hasattr(self.instr_details, 'serial'):
                # Serial
                self.instr = self.ICF.getInstrument_serial(self.instr_details.get('serial', None))
            
            elif hasattr(self.instr_details, 'model'):
                # Model
                self.instr = self.ICF.getInstrument_model(self.instr_details.get('model', None))
            
            elif hasattr(self.instr_details, 'type'):
                # Type
                self.instr = self.ICF.getInstrument_type(self.instr_details.get('type', None))
                    
            if len(self.instr) > 0:
                self.status.set("Ready")
                self.l_status.config(fg='green3')
                
            else:
                self.status.set("Not Present")
                self.l_status.config(fg='red')
            
        def getStatus(self):
            if len(self.instr) > 0:
                return True
            
            else:
                return False
        
        
    class g_TestElement(Tk.Frame):
        
        states = ['On', 'Off']
        
        def __init__(self, master, testObject, testMethodName, logger, lock):
            Tk.Frame.__init__(self, master, padx=3, pady=3)
            
            self.logger = logger
            self.lock = lock
            
            self.testMethod = getattr(testObject, testMethodName)
            defaultName = testMethodName.replace('test_', '')
            self.testName = testObject.test_details.get(testMethodName, {}).get('name', defaultName) or defaultName
            
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
                
        def setState(self, new_state):
            if new_state < len(self.states):
                self.state = new_state
                stateIdent = self.states[self.state]
                self.v_state.set(stateIdent)
                
                if stateIdent == "On":
                    self.b_run.config(state=Tk.NORMAL)
                    
                elif stateIdent == "Off":
                    self.b_run.config(state=Tk.DISABLED)
                
                # Reset test results
                self.testThread = None
                self.testResult = None
                
            else:
                raise IndexError
        
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
            self.testThread = threading.Thread(target=self._run_thread)
            self.testThread.start()
            
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
            
