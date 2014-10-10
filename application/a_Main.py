import sys
import os
import logging
import importlib

import Tkinter as Tk
import ttk
import tkMessageBox

#import ImageTk
#from PIL import Image

sys.path.append("..")
from InstrumentControl import InstrumentControl

class a_Main(object):
    """
    Main application for 
    TODO:
    - Splash screen on load (http://code.activestate.com/recipes/534124-elegant-tkinter-splash-screen/)
    - Toolbar (http://zetcode.com/gui/tkinter/menustoolbars/)
    - Instrument Nicknames
    - Persistant settings
    - Nanny thread to periodically check if connected hosts and resources are still active
    """

    openViews = {}
    
    # Tree Organization
    treeGroup = 'hostname'
    treeSort = 'deviceModel'
    
    def __init__(self):
        # Get root directory
        # Get the root path
        can_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir) # Resolves symbolic links
        self.rootPath = os.path.abspath(can_path)
        
        # Instantiate a logger
        self.logger = logging.getLogger(__name__)
        self.logFormatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        self.logger.setLevel(logging.DEBUG)
        # TODO: Log to console?
        #console = logging.StreamHandler(stream=sys.stdout)
        #self.logger.addHandler(console)
        # TODO: Log to file?
        
        # Instantiate an InstrumentControl object
        self.ICF = InstrumentControl(Logger=self.logger)
        
        # Attempt to start a local InstrumentManager
        self.ICF.startWaitManager()
        
        # Instantiate root Tk object
        self.myTk = Tk.Tk()
            
        # GUI Startup
        self.rebuild()
        self.rebind()
        
        # Index views
        self.__loadViews()
        
        # TODO: Persistent Settings
        
        self.run()
        
    def __pathToModelName(self, path):
        # Get module name from relative path
        com_pre = os.path.commonprefix([self.rootPath, path])
        r_path = path.replace(com_pre + "\\", '')
        
        modulePath = r_path.replace("\\", '.')
        return modulePath
        
    def __loadViews(self):
        # Clear the view dictionary
        self.views = {} 
        
        # Build view dictionary
        view_dir = os.path.join(self.rootPath, 'views')
        allviews = os.walk(view_dir)
        for dir in allviews:
            # Verify valid directory
            if len(dir[2]) == 0:
                # Directory is empty, move on
                continue
            
            elif '__init__.py' not in dir[2]:
                # Directory must be a python module
                # TODO: Create an __init__.py file if one does not exist
                self.logger.warning('Non-module model found: %s', dir[0])
                continue
            
            for file in dir[2]:
                # Iterate through each file
                if file[-3:] == '.py' and '__init__' not in file:
                    # Get module name from relative path     
                    className = file.replace('.py', '')
                    viewModule = self.__pathToModelName(dir[0]) + '.' + className

                    # Attempt to load the view
                    try:
                        testModule = importlib.import_module(viewModule)
                        
                        # Check to make sure the correct class exists
                        testClass = getattr(testModule, className) # Will raise exception if doesn't exist
                        
                        validVIDs = testClass.validVIDs
                        validPIDs = testClass.validPIDs
                        
                        self.views[viewModule] = (className, validVIDs, validPIDs)
                    
                    except Exception as e:
                        self.logger.error('Unable to load module %s: %s', viewModule, str(e))
                        continue
    
    def _getValidViews(self, VID, PID):   
        validViews = []
        
        for viewModule, viewInfo in self.views.items():
            viewClass, validVIDs, validPIDs = viewInfo
        
            if VID in validVIDs or len(validVIDs) == 0:
                if PID in validPIDs or len(validPIDs) == 0:
                    validViews.append((viewModule, viewClass))
                
        return validViews
    
    def rebuild(self):
        """
        Rebuilds all GUI elements and positions
        
        Pane Layout:
        +-----------+-----------------------+
        |           |                       |
        |   tree    |                       |
        |   frame   |     controlFrame      |
        |           |                       |
        |           |                       |
        +-----------+-----------------------+
        |                                   |
        |             logFrame              |
        |                                   |
        +-----------------------------------+
        """
        master = self.myTk
        #ttk.Style().theme_use('vista')
        #master = Tk.Toplevel(self.myTk)
        master.wm_title("Instrument Control")
        master.minsize(500, 500)
        master.geometry("800x600")
        
        #=======================================================================
        # Menubar
        #=======================================================================
        master.option_add('*tearOff', Tk.FALSE)
        self.menubar = Tk.Menu(master) 
        master['menu'] = self.menubar
        # File
        self.m_File = Tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.m_File, label='File')
        self.m_File.add_command(label='Connect to host...', command=lambda: self.cb_managerConnect())
        self.m_File.add_command(label='Refresh all hosts...', command=lambda: self.cb_refreshTree())
        self.m_File.add_separator()
        # File - LogLevel
        self.m_File_LogLevel = Tk.Menu(self.m_File)
        self.m_File.add_cascade(menu=self.m_File_LogLevel, label='Log Level')
        self.m_File_LogLevel.add_radiobutton(label='Critical',  command=lambda: self.cb_setLogLevel(logging.CRITICAL))
        self.m_File_LogLevel.add_radiobutton(label='Error',     command=lambda: self.cb_setLogLevel(logging.ERROR))
        self.m_File_LogLevel.add_radiobutton(label='Warning',   command=lambda: self.cb_setLogLevel(logging.WARNING))
        self.m_File_LogLevel.add_radiobutton(label='Info',      command=lambda: self.cb_setLogLevel(logging.INFO))
        self.m_File_LogLevel.add_radiobutton(label='Debug',     command=lambda: self.cb_setLogLevel(logging.DEBUG))
        
        self.m_File.add_separator()
        self.m_File.add_command(label='Exit', command=self.cb_exitWindow)
        # Help
        self.m_Help = Tk.Menu(self.menubar, name='help')
        self.menubar.add_cascade(menu=self.m_Help, label='Help')
        self.m_Help.add_command(label='About')
        
        #=======================================================================
        # Status Bar
        #=======================================================================
        self.statusbar = self.Statusbar(master)
        self.statusbar.pack(side=Tk.BOTTOM, fill=Tk.X)
        
        # Horizontal Pane
        self.HPane = Tk.PanedWindow(master, orient=Tk.VERTICAL, height=400, sashpad=5, sashwidth=8)
        self.HPane.pack(fill=Tk.BOTH, expand=Tk.YES)
        #=======================================================================
        # Horizontal Pane - Top
        #=======================================================================
        # Vertical Pane
        self.VPane = Tk.PanedWindow(self.HPane, orient=Tk.HORIZONTAL, height=400, width=400, sashpad=5, sashwidth=8)
        self.HPane.add(self.VPane)
        
        #=======================================================================
        #     Vertical Pane - Left
        #     Treeview Frame
        #     Min size: 400px
        #=======================================================================
        self.treeFrame = Tk.Frame(self.VPane) #, highlightcolor='green', highlightthickness=2)
        self.VPane.add(self.treeFrame, width=800, minsize=400)
        
        Tk.Label(self.treeFrame, text='Instruments').pack(side=Tk.TOP)
        self.tree = ttk.Treeview(self.treeFrame, height=20)
        
        self.tree['columns'] = ('Type', 'Serial')
        self.tree.heading('#0', text='Instrument')
        self.tree.column('Type', width=150)
        self.tree.heading('Type', text='Type')
        self.tree.column('Serial', width=100)
        self.tree.heading('Serial', text='Serial Number')
        self.tree.pack(fill=Tk.BOTH)
        
        #=======================================================================
        #     Vertical Pane - Right
        #     Controls Frame
        #     Min size: None
        #=======================================================================
        self.controlFrame = Tk.Frame(self.VPane)
        self.VPane.add(self.controlFrame)
        
        # TODO: Add some controls here
        # Notebook?: http://www.tkdocs.com/tutorial/complex.html
        #=======================================================================
        # Horizontal Pane - Bottom
        # Logger Frame
        # Min size: 200px
        #=======================================================================
        self.logFrame = Tk.Frame(self.HPane)
        self.HPane.add(self.logFrame, width=200, minsize=200)
        
        Tk.Label(self.logFrame, text='Log').pack(side=Tk.TOP)
        self.logConsole = Tk.Text(self.logFrame)
        self.logConsole.configure(state=Tk.DISABLED)
        self.logConsole.pack(fill=Tk.BOTH)

    def rebind(self):
        """
        Creates all of the GUI element bindings
        """
        self.myTk.wm_protocol("WM_DELETE_WINDOW", lambda: self.cb_exitWindow())
        
        # Console
        h_textHandler = TextHandler(self.logConsole)
        h_textHandler.setFormatter(self.logFormatter)
        self.logger.addHandler(h_textHandler)
        
        self.tree.bind('<Button-3>', self.e_TreeRightClick)
        self.tree.bind('<Double-Button-1>', self.e_TreeDoubleClick)
        
    def resize(self):
        """
        Resize the frames when the window size changes
        """
        pass
        
    def run(self):

        # Try to connect to the local manager
        self.ICF.addManager('localhost')
        
        self.rebuildTreeview()
        
        self.logger.info('Application start')
        
        self.myTk.mainloop()
    
    def rebuildTreeview(self, group='hostname', sort='deviceModel', reverseOrder=False):
        """
        Possible groupings:
        - None (Flat list)
        - Hostname (default)
        - Controller
        - deviceType
        - deviceVendor
        - deviceModel
        
        Sorting can be done on any valid key
        """
        validGroups = ['hostname', 'controller', 'deviceType', 'deviceVendor', 'deviceModel']
        
        # Clear the treeview
        treenodes = self.tree.get_children()
        for n in treenodes:
            self.tree.delete(n)
            
        # Import Image Assets
        #img_host = Image.open('assets/computer.png')
        #img_host = ImageTk.PhotoImage(img_host)
        #img_device = Image.open('assets/drive.png')
        #img_device = ImageTk.PhotoImage(img_device)

        # Get a flat list of resources and sort
        self.ICF.cacheProperties()
        resources = self.ICF.getProperties().values()
        resources.sort(key=lambda res: res.get(sort, ''), reverse=reverseOrder)
        
        # Build a list of group values
        if group is 'hostname':
            # Fixes a bug where hosts were not added if no resources were present
            for gval in self.ICF.getConnectedHosts():
                self.tree.insert('', 'end', gval, text=gval, open=True) #, image=img_host)
                
        elif group is not None and group in validGroups:
            group_vals = []
            for res in resources:
                gv = res.get(group, None)
                if gv is not None and gv not in group_vals:
                    group_vals.append(gv)
            
            group_vals.sort()
            
            # Create group tree nodes
            for gval in group_vals:
                self.tree.insert('', 'end', gval, text=gval)
            
        # Populate child nodes
        for res in resources:
            lineID = res.get('uuid', None)
            if lineID is not None:
                # If no driver loaded, use Resource ID
                if res.get('modelName', None) is None:
                    lineText = res.get('resourceID', 'Unknown Resource')
                else:
                    # TODO: Device nicknames
                    lineText = res.get('deviceVendor') + ' ' + res.get('deviceModel')
    
                
                self.tree.insert(res.get(group, ''), 'end', lineID, text=lineText) #, image=img_device)
                self.tree.set(lineID, 'Type', res.get('deviceType', 'Generic'))
                self.tree.set(lineID, 'Serial', res.get('deviceSerial', 'Unknown'))

    def loadView(self, uuid, viewModule, viewClass=None):
        
        try:
            if viewClass is None:
                viewClass = self.views.get(viewModule)[0]
            
            viewModule = importlib.import_module(viewModule)
            viewClass = getattr(viewModule, viewClass)
            
            instrument = self.ICF.getInstrument(uuid)
            
            if instrument is not None:
                viewWindow = viewClass(self.myTk, instrument)
                
                # Store the object in open views
                self.openViews[uuid] = viewWindow
                
                viewWindow.run()
                
            else:
                tkMessageBox.showwarning('Unable to load view', 'No Model is loaded for this device')
            
        except:
            self.logger.exception("Failed to load view: %s", viewModule)

    #===========================================================================
    # Callback Functions
    #
    # Callback functions with variable parameters should:
    # - start with 'cb_'
    #===========================================================================
    def cb_exitWindow(self):
        try:
            if tkMessageBox.askokcancel("Quit", "Do you really wish to quit?"):
                self.myTk.destroy()
        
        except:
            self.myTk.destroy()
            
    def cb_managerConnect(self):
        # Spawn a window to get address and port
        from include.a_managerHelpers import a_ConnectToHost
        
        # Create the child window
        w_connectToHost = a_ConnectToHost(self.myTk, lambda address, port: self.cb_addManager(address, port))
        
        
    def cb_addManager(self, address, port=None):
        # Attempt a connection to the manager
        self.ICF.addManager(address, port)
        self.cb_refreshTree()
    
    def cb_managerDisconnect(self, address):
        self.ICF.removeManager(address)
        self.cb_refreshTree()
        
    def cb_addResource(self, address):
        from include.a_managerHelpers import a_AddResource
            
        controllers = self.ICF.getControllers(address)
            
        # Create the child window
        w_addResource = a_AddResource(self.myTk, self, controllers, lambda controller, resID: self.ICF.addResource(address, controller, resID))
        
        # Make the child modal
        w_addResource.focus_set()
        w_addResource.grab_set()
            
    def cb_loadDriver(self, uuid):
        validModels = self.ICF.getValidModels(uuid)
        
        if len(validModels) > 0:
            tkMessageBox.showwarning('Unable to load driver', 'Driver conflict. Kevin\'s fault.')
        
        else:
            tkMessageBox.showwarning('Unable to load driver', 'No valid drivers could be found for this device')
            
    def cb_unloadDriver(self, uuid):
        self.ICF.unloadModel(uuid)
        #addr = self.ICF.getAddressFromUUID(uuid)
        #self.ICF.refresh
        self.cb_refreshTree()
        
    def cb_loadView(self, uuid):

        if uuid in self.openViews.keys():
            try:
                # Do nothing? Bring window into focus?
                view_window = self.openViews.get(uuid)
                
                view_window.lift()
            
                return None
            except:
                # On exception, load the view selector
                pass
            
        # Load view selector
        props = self.ICF.getProperties(uuid)
        VID = props.get('vendorID', None)
        PID = props.get('productID', None)
        
        validViews = self._getValidViews(VID, PID)
        
        if len(validViews) > 1:
            # Spawn a window to select the view to load
            from include.a_managerHelpers import a_ViewSelector
            
            # Create the child window
            viewList = [x[0] for x in validViews]
            w_ViewSelector = a_ViewSelector(self.myTk, viewList, lambda viewModule: self.loadView(uuid, viewModule, None))
            
        elif len(validViews) is 1:
            viewModule, viewClass = validViews[0]
            
            self.loadView(uuid, viewModule, viewClass)
                
        else:
            tkMessageBox.showwarning('Unable to load view', 'No suitable views could be found for this model')
    
    def cb_refreshTree(self, address=None):
        self.ICF.refreshManager(address)            
        self.rebuildTreeview()
            
    def cb_setLogLevel(self, level):
        #numeric_level = getattr(logging, loglevel.upper(), None)
        self.logger.setLevel(level)
        self.logger.log(level, 'Log Level Changed')

    #===========================================================================
    # Event Handlers
    #
    # All Tk bound event handlers should:
    # - start with 'e_'
    # - accept a parameter 'event'
    # 
    #===========================================================================

    def e_TreeRightClick(self, event):
        elem = self.tree.identify_row(event.y)

        # Create a context menu
        menu = Tk.Menu(self.myTk)
        
        # Populate menu based on context
        if self.ICF.isConnectedHost(elem):
            # Context is Hostname
            
            # Context menu:
            # -Refresh
            # -Load Device
            # -Get log?
            menu.add_command(label='Add Resource', command=lambda: self.cb_addResource(elem))
            menu.add_command(label='Refresh', command=lambda: self.cb_refreshTree(elem))
            menu.add_command(label='Disconnect', command=lambda: self.cb_managerDisconnect(elem))
            
        elif self.ICF.isValidResource(elem):
            # Context is Resource, elem is the UUID
            
            # Context menu:
            # -Load Driver/Unload Driver
            # -Control Instrument (Launch View/GUI)
            res_props = self.ICF.getProperties(elem)
            
            if res_props.get('modelName', None) == None:
                menu.add_command(label='Load Driver', command=lambda: self.cb_loadDriver(elem))
            else:
                menu.add_command(label='Control Device', command=lambda: self.cb_loadView(elem))
                menu.add_command(label='Unload Driver', command=lambda: self.cb_unloadDriver(elem))
            
            #menu.add_command(label='Properties...', command=lambda: tkMessageBox.showinfo('Instrument Properties', elem))
        
        else:
            # Something else maybe empty space?
            menu.add_command(label='Connect to host...', command=lambda: self.cb_managerConnect())
        
        menu.post(event.x_root, event.y_root)

    def e_TreeDoubleClick(self, event):
        pass
        
    #===========================================================================
    # Internal Class Definitions
    #===========================================================================        
        
    class Statusbar(Tk.Frame):
        """
        TODO:
        - Add sections
        """
        def __init__(self, master, sections=1):
            Tk.Frame.__init__(self, master)
            
            if sections < 1:
                sections = 1
                    
            self.sections = [None]*sections
            for i in range(0, sections):
                self.sections[i] = Tk.Label(self, bd=1, relief=Tk.SUNKEN, anchor=Tk.W)
                self.sections[i].pack(fill=Tk.X)
                
        def add_section(self):
            pass
    
        def set(self, section, format, *args):
            self.label.config(text=format % args)
            self.label.update_idletasks()
    
        def clear(self, section):
            self.label.config(text="")
            self.label.update_idletasks()
            
    class Toolbar(Tk.Frame):
        def __init__(self, master, **kwargs):
            Tk.Frame.__init__(self, master)

        
class TextHandler(logging.Handler):
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
        
if __name__ == "__main__":
    # Load Application GUI
    try:
        main_gui = a_Main()
         
    except Exception as e:
        print "Unable to load main application"
        raise
        sys.exit()
