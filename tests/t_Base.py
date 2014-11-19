import inspect
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
    
    def __init__(self):
        """
        Test Initialization
        
        - Attempt to connect to the local InstrumentManager instance
        - Get a list of test methods
        - Initialize the logger
        - Draw the GUI window
        """
        self.instr = InstrumentControl()
        
        # Get a list of class attributes, identify test methods
        # Test methods must be prefixed by 'test_'
        self.test_methods = []
        for func in dir(self.__class__):
            test = getattr(self.__class__, func)
            if func.startswith('test_') and inspect.ismethod(test):
                self.test_methods.append(func)
        
        self.open()
        
        self._runGUI()
        
    def _runGUI(self):
        self.myTk = Tk.Tk()
        master = self.myTk
        
        master.wm_title("Run Tests")
        
        #=======================================================================
        # Build GUI
        #=======================================================================
        self.l_name = Tk.Label(master, text=self.test_info.get('name', 'Test'), font=("Helvetica", 14), justify=Tk.CENTER)
        self.l_name.pack()
        if len(self.test_methods) == 0:
            # No tests to run!
            pass
        
        else:
            # Create a test element for each test method
            self.tests = []
            for func in self.test_methods:
                temp = self.g_TestElement(master, self, func)
                temp.pack()
                self.tests.append(temp)
                
        self.f_run = Tk.Frame(master)
        
        
        #=======================================================================
        # Run GUI
        #=======================================================================
        self.myTk.mainloop()
        
    def cb_RunTest(self):
        pass
    
        
    #===========================================================================
    # GUI Frame Elements
    #===========================================================================
    class g_TestElement(Tk.Frame):
        
        states = ['On', 'Off']
        
        def __init__(self, master, testObject, testMethodName):
            Tk.Frame.__init__(self, master, padx=3, pady=3)
            
            testMethod = getattr(testObject, testMethodName)
            testName = testObject.test_names.get(testMethodName, testMethodName.replace('test_', ''))
            
            self.state = 0
            self.v_state = Tk.StringVar()
            self.b_state = Tk.Button(self, textvariable=self.v_state, command=self.cb_buttonPressed, width=5)
            self.b_state.pack(side=Tk.LEFT)
            self.setState(self.state)
            
            self.l_name = Tk.Label(self, text=testName, font=("Helvetica", 12), width=30, anchor=Tk.W, justify=Tk.LEFT)
            self.l_name.pack(side=Tk.LEFT)
        
            
        def cb_buttonPressed(self):
            next_state = (self.state + 1) % len(self.states)
            
            self.setState(next_state)
                
        def setState(self, new_state):
            if new_state < len(self.states):
                self.state = new_state
                self.v_state.set(self.states[self.state])
            else:
                raise IndexError
                
        def run(self):
            """
            Run the test in a new thread
            """
            pass