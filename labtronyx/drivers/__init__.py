import sys
import os
import importlib
import copy

def getAllDrivers():
    drivers = {}
    
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
            if fileExtension in ['.py'] and '__init__' not in file:
                # Get module name from relative path
                
                com_pre = os.path.commonprefix([canpath, filepath])
                r_path = modulepath.replace(com_pre + os.path.sep, '')
                moduleName = r_path.replace(os.path.sep, '.')
                fileName, _ = os.path.splitext(file)
        
                # Attempt to load the model
                try:
                    testModule = importlib.import_module(moduleName)
                    
                    # Check to make sure the correct class exists
                    testClass = getattr(testModule, fileName) # Will raise exception if doesn't exist
                    
                    info = copy.deepcopy(testClass.info)
                    drivers[moduleName] = info
                    
                except Exception as e:
                    print testModule
                    raise
                
                #===========================================================
                # except AttributeError:
                #     self.logger.error('Model %s does not have a class %s', modelModule, className)
                #     continue
                #===========================================================
    
    return drivers
