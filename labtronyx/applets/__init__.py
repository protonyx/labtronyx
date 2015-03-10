import sys
import os
import importlib
import copy

def getAllApplets():
    applets = {}
    
    canpath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir))) # Resolves symbolic links
    
    if not canpath in sys.path:
        sys.path.append(canpath)
        
    for dir in os.walk(canpath):
        dirpath, dirnames, filenames = dir

        # Verify valid directory
        if len(dir[2]) == 0:
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
            if fileExtension in ['.py', '.pyc'] and '__init__' not in file:
                # Get module name from relative path
                
                com_pre = os.path.commonprefix([canpath, filepath])
                r_path = modulepath.replace(com_pre + os.path.sep, '')
                moduleName = r_path.replace(os.path.sep, '.')
                fileName, _ = os.path.splitext(file)

                # Attempt to load the view
                try:
                    testModule = importlib.import_module(moduleName)
                
                    # Check to make sure the correct class exists
                    testClass = getattr(testModule, fileName) # Will raise exception if doesn't exist
                    
                    info = copy.deepcopy(testClass.info)
                    applets[moduleName] = info
                
                except Exception as e:
                    pass
            
    return applets
