
# System Imports
import os
import socket
import threading

# Local Imports
from . import logger
from . import version

from . import bases
from . import common

class InstrumentManager(object):
    """
    Labtronyx InstrumentManager

    Facilitates communication with instruments using all available interfaces.

    :param server:         Enable RPC endpoint
    :type server:          bool
    :param server_port:    RPC endpoint port
    :type server_port:     int
    :param plugin_dirs:    List of directories containing plugins
    :type plugin_dirs:     list
    :param logger:         Logger
    :type logger:          logging.Logger
    """
    name = 'Labtronyx'
    longname = 'Labtronyx Instrumentation Control Framework'

    SERVER_PORT = 6780
    ZMQ_PORT = 6781
    
    def __init__(self, **kwargs):
        # Configurable instance variables
        self.plugin_dirs = kwargs.get('plugin_dirs', [])
        self.server_port = kwargs.get('server_port', self.SERVER_PORT)
        self.logger = kwargs.get('logger', logger)

        # Initialize instance variables
        self._interfaces = {}  # Plugin FQN -> Interface INSTANCE
        self._drivers = {}  # Plugin FQN -> Driver CLASS
        self._scripts = {} # Plugin UUID -> Script INSTANCE

        # Initialize PYTHONPATH
        self.rootPath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir)))
        # if self.rootPath not in sys.path:
        #     sys.path.append(self.rootPath)

        # Announce Version
        self.logger.info(self.longname)
        self.logger.info("Version: %s", version.ver_full)
        self.logger.debug("Build Date: %s", version.build_date)

        # Directories to search for plugins
        dirs = ['drivers', 'interfaces']
        dirs_res = [os.path.join(self.rootPath, dir) for dir in dirs] + self.plugin_dirs

        # Categorize plugins by base class
        cat_filter = {
            "drivers":      bases.DriverBase,
            "interfaces":   bases.InterfaceBase,
            "resources":    bases.ResourceBase,
            "scripts":      bases.ScriptBase
        }

        # Load Plugins
        self.plugin_manager = common.plugin.PluginManager(directories=dirs_res, categories=cat_filter, logger=self.logger)
        self.plugin_manager.search()

        # Validate plugins
        for plugin_name in self.plugin_manager.getAllPlugins().keys(): # Create a copy
            if not self.plugin_manager.validatePlugin(plugin_name):
                self.plugin_manager.disablePlugin(plugin_name)
        
        # Load Drivers
        self._drivers = self.plugin_manager.getPluginsByCategory('drivers')
        
        # Load Interfaces
        for interface_name in self.plugin_manager.getPluginsByCategory('interfaces'):
            self.enableInterface(interface_name)

        # Start Server
        if kwargs.get('server', False):
            if not self.server_start():
                raise EnvironmentError("Unable to start Labtronyx Server")
    
    def __del__(self):
        try:
            self.server_stop()
        except:
            pass

        self._close()

    def _close(self):
        """
        Close all resources and interfaces
        """
        # Disable all interfaces, close all resources
        for interface_name in self._interfaces.values(): # use values() so a copy is created
            self.disableInterface(interface_name)

    #===========================================================================
    # Labtronyx Server
    #===========================================================================

    def server_start(self, new_thread=True):
        """
        Start the API/RPC Server and Event publisher. If `new_thread` is True, the server will be started in a new
        thread in a non-blocking fashion.

        If a server is already running, it will be stopped and then restarted.

        :returns: True if successful, False otherwise
        :rtype: bool
        """
        # Clean out old server, if any exists
        self.server_stop()

        # Start event publisher
        self._server_events = common.events.EventPublisher(self.ZMQ_PORT)
        self._server_events.start()

        # Create a server app
        self._server_app = common.server.create_server(self, self.server_port, logger=self.logger)

        # Server start command
        from werkzeug.serving import run_simple
        srv_start_cmd = lambda: run_simple(
            hostname=self.getHostname(), port=self.server_port, application=self._server_app,
            threaded=True, use_debugger=True
        )

        # Instantiate server
        if new_thread:
            server_thread = threading.Thread(name='Labtronyx-Server', target=srv_start_cmd)
            server_thread.start()

            return True

        else:
            try:
                srv_start_cmd()

            except:
                self.server_stop()

    def server_stop(self):
        """
        Stop the Server
        """
        # Signal the event
        self._publishEvent(common.events.EventCodes.manager.shutdown)

        # Stop the event publisher
        if hasattr(self, '_server_events'):
            try:
                self._server_events.stop()

            except:
                pass

            finally:
                del self._server_events

        # Shutdown server
        if hasattr(self, '_server_app'):
            try:
                # Must use the REST API to shutdown
                import urllib2
                url = 'http://{0}:{1}/api/shutdown'.format(self.getHostname(), self.server_port)
                resp = urllib2.Request(url)
                handler = urllib2.urlopen(resp)

                if handler.code == 200:
                    self.logger.debug('Server stopped')
                else:
                    self.logger.error('Server stop returned code: %d', handler.code)

            except:
                pass

            finally:
                del self._server_app

    @property
    def version(self):
        return version

    @staticmethod
    def getVersion():
        """
        Get the Labtronyx version
        
        :returns: str
        """
        return version.ver_full

    def getAddress(self):
        """
        Get the local IP Address

        :returns: str
        """
        return socket.gethostbyname(self.getHostname())

    @staticmethod
    def getHostname():
        """
        Get the local hostname

        :rtype:                 str
        """
        return socket.gethostname()

    #===========================================================================
    # Event Publishing
    #===========================================================================

    def _publishEvent(self, event, *args, **kwargs):
        """
        Private method called internally to signal events. Calls handlers and dispatches event signal to subscribed
        clients

        :param event:           event
        :type event:            str
        """
        if hasattr(self, '_server_events'):
            self._server_events.publishEvent(event, *args, **kwargs)

    # ===========================================================================
    # Interface Operations
    # ===========================================================================

    @property
    def interfaces(self):
        """
        :rtype:                 dict[str:labtronyx.bases.interface.DriverBase]
        """
        # Make interfaces available by
        return {v.interfaceName:v for k,v in self._interfaces.items()}

    def listInterfaces(self):
        """
        Get a list of interfaces that are enabled

        :returns:               Interface names
        :rtype:                 list[str]
        """
        return self.interfaces.keys()
    
    def enableInterface(self, interfaceName, **kwargs):
        """
        Enable or restart an interface. Use this method to pass parameters to an interface. If an interface with the
        same name is already running, it will be stopped first. Each interface may only have one instance at a time
        (Singleton pattern).

        :param interfaceName:   Interface plugin name
        :type interfaceName:    str
        :rtype:                 bool
        :raises:                KeyError
        """
        int_cls = self.plugin_manager.getPlugin(interfaceName)

        # Attempt to find interface using the interfaceName attribute
        if int_cls is None:
            for pluginName, pluginCls in self.plugin_manager.getPluginsByCategory('interfaces').items():
                if pluginCls.interfaceName == interfaceName:
                    interfaceName = pluginName
                    int_cls = pluginCls
                    break

        if not issubclass(int_cls, bases.InterfaceBase):
            return False

        if int_cls is None:
            raise KeyError("Interface has not been loaded")

        try:
            # If the interface is already enabled, disable the existing one
            self.disableInterface(interfaceName)

            # Instantiate interface
            int_obj = int_cls(manager=self, logger=self.logger, **kwargs)

            # Call the plugin hook to open the interface. Ensure interface opens correctly
            if int_obj.open():
                self._interfaces[int_obj.uuid] = int_obj

                self.logger.debug("Started Interface: %s", interfaceName)
                return True

            else:
                self.logger.error("Interface %s failed to open", interfaceName)
                return False

        except NotImplementedError:
            return False

        except:
            self.logger.exception("Exception during enableInterface")
            return False
    
    def disableInterface(self, interfaceName):
        """
        Disable an interface that is running.

        :param interfaceName:   Interface plugin name
        :type interfaceName:    str
        :rtype:                 bool
        """
        if interfaceName in self.interfaces:
            try:
                inter = self.interfaces.get(interfaceName)
                inter_uuid = inter.uuid

                # Call the plugin hook to close the interface
                inter.close()

                self.logger.info("Stopped Interface: %s" % interfaceName)

                del self._interfaces[inter_uuid]
                return True

            except NotImplementedError:
                return False
                
            except:
                self.logger.exception("Exception during interface close")
                return False
        
    # ===========================================================================
    # Resource Operations
    # ===========================================================================
    
    def refresh(self):
        """
        Refresh all interfaces and resources. Attempts enumeration on all interfaces, then calls the `refresh`
        method for all resources.
        """
        for interfaceName, interfaceObj in self.interfaces.items():
            try:
                # Discover any new resources
                interfaceObj.refresh()
            except NotImplementedError:
                pass

    def getAttributes(self):
        """
        Get the class attributes for all loaded plugins. Dictionary keys are the Fully Qualified Names (FQN) of the
        plugins

        :rtype:                 dict[str:dict]
        """
        return self.plugin_manager.getAllPluginInfo()
    
    def getProperties(self):
        """
        Returns the property dictionaries for all resources
        
        :rtype:                 dict[str:dict]
        """
        ret = {}
        ret.update({uuid:pObj.getProperties() for uuid,pObj in self._interfaces.items()})
        ret.update({uuid:pObj.getProperties() for uuid,pObj in self.resources.items()})
        
        return ret

    @property
    def resources(self):
        all_resources = {}

        for interfaceName, interfaceObj in self.interfaces.items():
            for resID, resourceObj in interfaceObj.resources.items():
                all_resources[resourceObj.uuid] = resourceObj

        return all_resources

    def listResources(self):
        """
        Get a list of UUIDs for all resources

        :rtype:                 list[str]
        """
        return self.resources.keys()

    def getResource(self, interfaceName, resID, driverName=None):
        """
        Get a resource by name from the specified interface. Not supported by all interfaces, see interface
        documentation for more details.

        :param interfaceName:   Interface name
        :type interfaceName:    str
        :param resID:           Resource Identifier
        :type resID:            str
        :param driverName:      Driver to load for resource
        :type driverName:       str
        :returns:               Resource object
        :rtype:                 labtronyx.bases.resource.ResourceBase
        :raises:                InterfaceUnavailable
        :raises:                ResourceUnavailable
        :raises:                InterfaceError
        """
        # NON-SERIALIZABLE
        int_obj = self.interfaces.get(interfaceName)

        if int_obj is None:
            raise common.errors.InterfaceUnavailable('Interface not found')

        try:
            # Call the interface getResource hook
            res = int_obj.getResource(resID)

            # Attempt to load the specified driver, but do not force
            res.loadDriver(driverName)

            return res

        except NotImplementedError:
            raise common.errors.InterfaceError('Operation not support by interface %s' % interfaceName)
    
    def findResources(self, **kwargs):
        """
        Get a list of resources/instruments that match the parameters specified.
        Parameters can be any key found in the resource property dictionary, such as these:

        :param uuid:            Unique Resource Identifier (UUID)
        :param interface:       Interface
        :param resourceID:      Interface Resource Identifier (Port, Address, etc.)
        :param resourceType:    Resource Type (Serial, VISA, etc.)
        :param deviceVendor:    Instrument Vendor
        :param deviceModel:     Instrument Model Number
        :param deviceSerial:    Instrument Serial Number
        :rtype:                 list[labtronyx.bases.resource.ResourceBase]
        """
        # NON-SERIALIZABLE
        matching_instruments = []
        
        prop = self.getProperties()
        
        for uuid, res_dict in prop.items():
            match = True
            
            for key, value in kwargs.items():
                if res_dict.get(key) != value:
                    match = False
                    break
                
            if match:
                try:
                    matching_instruments.append(self.resources.get(uuid))
                except KeyError:
                    pass
                
        return matching_instruments
    
    def findInstruments(self, **kwargs):
        """
        Alias for :func:`findResources`
        """
        # NON-SERIALIZABLE
        return self.findResources(**kwargs)

    # ===========================================================================
    # Driver Operations
    # ===========================================================================

    @property
    def drivers(self):
        return self._drivers
                
    def listDrivers(self):
        """
        Get a list of loaded driver names. Returned names are the keys into the `driver` dictionary which contains the
        driver classes.

        :rtype:                 list[str]
        """
        return self._drivers.keys()

    def getDriverInfo(self):
        """
        Get a dictionary of loaded driver info

        :deprecated: Deprecated by :func:`getAttributes`

        :rtype:                 dict[str:dict]
        """
        return {driver:self.plugin_manager.getPluginInfo(driver) for driver in self.drivers}

    @property
    def scripts(self):
        """
        :rtype: dict[str:bases.ScriptBase]
        """
        return self._scripts

    def openScript(self, script_fqn, **kwargs):
        """
        Create an instance of a script. The script must have already been loaded by the plugin manager. Any required
        script parameters can be provided using keyword arguments.

        :param script_fqn:      Fully Qualified Name of the script plugin
        :type script_fqn:       str
        :returns:               Script Instance UUID
        :rtype:                 str
        :raises:                KeyError
        """
        scriptCls = self.plugin_manager.getPlugin(script_fqn)

        if scriptCls is None:
            raise KeyError("Script has not been loaded")

        if not issubclass(scriptCls, bases.ScriptBase):
            raise KeyError("Plugin is not a script")

        scriptObj = scriptCls(self, logger=self.logger, **kwargs)
        script_uuid = scriptObj.uuid
        self._scripts[script_uuid] = scriptObj

        self._publishEvent(common.events.EventCodes.script.created, script_uuid)

        return script_uuid

    def runScript(self, script_uuid):
        """
        Run a script that has been previously opened using :func:`openScript`. The script is run in a separate thread

        :param script_uuid:     Script Instance UUID
        :type script_uuid:      str
        :raises:                KeyError
        :raises:                ThreadError
        """
        scriptObj = self.scripts.get(script_uuid)

        if scriptObj is None:
            raise KeyError("Script instance could not be found")

        scriptThread = threading.Thread(target=scriptObj.start, name="script-"+script_uuid)
        scriptThread.setDaemon(True)
        scriptThread.start()

    def stopScript(self, script_uuid):
        """
        Stop a script that is currently running. Does not currently do anything.

        :param script_uuid:     Script Instance UUID
        :type script_uuid:      str
        :raises:                KeyError
        """
        scriptObj = self.scripts.get(script_uuid)

        if scriptObj is None:
            raise KeyError("Script instance could not be found")

        scriptObj.stop()

    def closeScript(self, script_uuid):
        """
        Destroy a script instance that is not currently running.

        :param script_uuid:     Script Instance UUID
        :type script_uuid:      str
        :rtype:                 bool
        """
        scriptObj = self.scripts.get(script_uuid)

        if scriptObj is None:
            return True

        if scriptObj.isRunning():
            return False

        del self.scripts[script_uuid]