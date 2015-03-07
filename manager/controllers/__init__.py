import sys
import os
import importlib
import copy

def getAllInterfaces():
    interfaces = {}
    
    canpath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir))) # Resolves symbolic links
    
    if not canpath in sys.path:
        sys.path.append(canpath)
        
    for dir in os.walk(canpath):
        dirpath, dirnames, filenames = dir
        
        # Verify valid directory
        if len(filenames) == 0:
            # Directory is empty, move on
            continue
        
        elif '__init__.py' not in filenames:
            # Directory must be a python module
            try:
                with file.open(os.path.join(dirpath, "__init__.py"), "w"):
                    pass
            except:
                continue
        
        for file in filenames:
            # Iterate through each file
            filepath = os.path.join(dirpath, file)
            modulepath, fileExtension = os.path.splitext(filepath)
            if fileExtension in ['.py', '.pyd', 'pyo'] and '__init__' not in file:
                # Get module name from relative path
                
                com_pre = os.path.commonprefix([canpath, filepath])
                r_path = modulepath.replace(com_pre + os.path.sep, '')
                moduleName = r_path.replace(os.path.sep, '.')
                fileName, _ = os.path.splitext(file)
        
                # Attempt to load the model
                #try:
                testModule = importlib.import_module(moduleName)
                
                # Check to make sure the correct class exists
                testClass = getattr(testModule, fileName) # Will raise exception if doesn't exist
                
                info = copy.deepcopy(testClass.info)
                interfaces[moduleName] = info
                
                #except Exception as e:
                #    continue
                
                #===========================================================
                # except AttributeError:
                #     self.logger.error('Model %s does not have a class %s', modelModule, className)
                #     continue
                #===========================================================
    
    return interfaces
#===============================================================================
# 
#     def __loadControllers(self):
#         """
#         Scan the controllers folder and instantiate each controller found
#         
#         This function is only run on startup
#         """
#         self.logger.info("Loading Controllers...")
#         
#         # Clear the controller dictionary to free resources
#         self.controllers = {}
#         
#         # Scan for controllers
#         cont_dir = os.path.join(self.rootPath, 'controllers')
#         allcont = os.walk(cont_dir)
#         for dir in allcont:
#             if len(dir[2]) > 0:
#                 # Directory is not empty
#                 if '__init__.py' in dir[2]: # Must be a module
#                     for file in dir[2]:
#                         # Iterate through each file
#                         if file[-3:] == '.py' and '__init__' not in file:
#                             # Instantiate each controller and add to controller list
#                             # Get relative path
#                             className = file.replace('.py', '')
#                             
#                             # Get module name from relative path
#                             contModule = self.__pathToModelName(dir[0]) + '.' + className
#                             
#                             self.logger.debug('Loading controller: %s', contModule)
#                             
#                             try:
#                                 # Attempt to import the controller module
#                                 testModule = importlib.import_module(contModule)
#                                 
#                                 # Instantiate the controller with a link to the model dictionary
#                                 testClass = getattr(testModule, className)(self)
#                                 
#                                 if testClass.open() == True:
#                                     self.controllers[className] = testClass
#                                     
#                                 else:
#                                     self.logger.warning('Controller %s failed to initialize', contModule)
#                                     testClass.close()
#                                     
#                             except ImportError:
#                                 self.logger.exception('Exception during controller import')
#                     
#                             except AttributeError as e:
#                                 self.logger.exception('Controller %s does not have a class %s', contModule, className)
#                                 
#                             except Exception as e:
#                                 self.logger.exception("Unable to load controller %s: %s", contModule, str(e))
#                                 
#     
#===============================================================================
