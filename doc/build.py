import sys
import os
import importlib

#===============================================================================
# Configuration
#===============================================================================
#SPHINXBUILD = "sphinx-build"

#DOC_SOURCE_DIR = "doc"
#DOC_BUILD_DIR = "doc-build"

LIB_ROOT = "../labtronyx"

# Drivers
DRIVER_SRC = "labtronyx.drivers"
DRIVER_DOC = "api/drivers"
INSTRUMENT_DOC = "instruments"

DRIVER_TEMPLATE = "template.tmpl"

canpath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir))) # Resolves symbolic links
libpath = os.path.join(canpath, LIB_ROOT)
sys.path.append(canpath)
sys.path.append(libpath)

import labtronyx

#===============================================================================
# Build Documentation
#===============================================================================
def gen_sphinx_header(text, undl):
    return '{0}\n{1}\n\n'.format(text, str(undl)[0]*len(text))

def gen_sphinx_automodule(module, options):
    ret = '.. automodule:: {0}\n'.format(module)
    for opt in options:
        ret += '   :{0}:\n'.format(opt)
    ret += '\n'
    
    return ret

def gen_sphinx_toctree(elems):
    ret =   '.. toctree::\n\n'

    for item in elems:
        ret += '   {0}\n'.format(item)
        
    ret += '\n'
    
    return ret

def build_driver_docs():
    print "Generating driver documentation..."
    
    import labtronyx.drivers
    driver_dict = labtronyx.drivers.getAllDrivers()
    
    # Create RST file for each driver
    for driver_module, driver_info in driver_dict.items():
        if driver_info == {}:
            continue
        driver_filename = os.path.join(canpath, DRIVER_DOC, str(driver_module) + ".rst")
        with file(driver_filename, "w+") as f:
            f.write(gen_sphinx_header(driver_module, "="))
            
            f.write(gen_sphinx_automodule(driver_module, ['show-inheritance', 'members']))

    print "Generating driver toctree..."
    
    # Create index with TOCtree
    toc_list = driver_dict.keys()
    toc_list.sort()
    
    toc_filename = os.path.realpath(os.path.join(canpath, DRIVER_DOC, 'index.rst'))
    with file(toc_filename, "w+") as f:
        f.write(gen_sphinx_header("Drivers", "="))
        
        f.write(gen_sphinx_toctree(toc_list))
    

# Sphinx build
#os.system("{} -b html {} {}".format(SPHINXBUILD, DOC_SOURCE_DIR, DOC_BUILD_DIR) )
