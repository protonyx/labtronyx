import common
import common.rpc

import sys
import importlib

import views

class m_Base(common.rpc.RpcBase, common.IC_Common):
    
    deviceType = 'Generic'
    view = None
    
    # Model Lookup
    validControllers = []
    validVIDs = []
    validPIDs = []
    
    def __init__(self, uuid, controller, resID, **kwargs):
        common.rpc.RpcBase.__init__(self)
        common.IC_Common.__init__(self, **kwargs)
        
        self.uuid = uuid
        self.controller = controller
        self.resID = resID
        
        # Check for logger
        if 'logger' in kwargs or 'Logger' in kwargs:
            self.logger = kwargs.get('logger', None) or kwargs.get('Logger', None)
            
        else:
            # TODO: Model default logger?
            pass
        
    def onLoad(self):
        raise NotImplementedError
    
    def onUnload(self):
        raise NotImplementedError
    
    #===========================================================================
    # def _loadView(self, **kwargs):
    #     testView = self.view
    #     
    #     if 'view' in kwargs:
    #         testView = kwargs['view']
    #         
    #     if testView != None:
    #         try:
    #             self.logger.debug('Loading view: ' + testView)
    #             
    #             # RPC Server must be running to load a view
    #             if self.socketThread == None:
    #                 self._startRPC()
    #             
    #             testModule = importlib.import_module('views.' + testView)
    #             testClass = getattr(testModule, testView)
    #             if 'port' in kwargs:
    #                 testClass = testClass(port=kwargs['port'])
    #             else:
    #                 testClass = testClass(port=self.socketThread.portNum)
    #             
    #             # View must be a child class of v_Base to load
    #             if isinstance(testClass, views.v_Base):
    #             #if views.v_Base in testClass.__class__.__bases__:
    #                 # Start the view in a new thread
    #                 testClass.start()
    #                 return testClass
    #             
    #             else:
    #                 self.logger.error('Unable to load view %s, views must inherit v_Base', testView)
    #         
    #         except ImportError:
    #             self.logger.exception('Specified view does not exist')
    #         except AttributeError:
    #             self.logger.exception('View %s must have a class %s', self.view, self.view)
    #         except:
    #             self.logger.exception('An unhandled exception occurred during loadView')
    #             
    #     else:
    #         self.logger.error('No view specified for this model')
    #         
    #     return False
    #===========================================================================
    
    def getModelName(self):
        return self.__class__.__name__

    # Models must implement these functions
    
    def getProperties(self):
        return { 'uuid': self.uuid,
                 'controller': self.controller.getControllerName(),
                 'resourceID': self.resID,
                 'modelName': self.getModelName(),
                 'port': self.rpc_getPort(),
                 'deviceType': self.deviceType,
                 'deviceVendor': 'Generic',
                 'deviceModel': 'Device',
                 'deviceSerial': 'Unknown',
                 'deviceFirmware': 'Unknown'
                }

