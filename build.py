import sys
import os
import importlib

#===============================================================================
# Configuration
#===============================================================================
SPHINXBUILD = "sphinx-build"

DOC_SOURCE_DIR = "doc/source"
DOC_BUILD_DIR = "doc-build"

LIB_ROOT = "labtronyx"

# Drivers
DRIVER_SRC = "labtronyx.drivers"
DRIVER_DOC = "doc/source/user_guide/api/drivers"
DRIVER_TEMPLATE = "template.tmpl"

#===============================================================================
# Build Documentation
#===============================================================================
canpath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir))) # Resolves symbolic links
libpath = os.path.join(canpath, LIB_ROOT)
sys.path.append(canpath)
sys.path.append(libpath)

import labtronyx
    
# Generate autodoc files for drivers
import labtronyx.drivers

driver_dict = labtronyx.drivers.getAllDrivers()

# Get template
template_filename = os.path.realpath(os.path.join(canpath, DRIVER_DOC, DRIVER_TEMPLATE))
template = 'TEMPLATE ERROR'
with file(template_filename) as f:
    template = f.read()
    
toc_filename = os.path.realpath(os.path.join(canpath, DRIVER_DOC, 'index.rst'))
toc = open(toc_filename, 'w+')
toc.write('Drivers\n')
toc.write('=======\n')
toc.write('\n')
toc.write('.. toctree::\n\n')

toc_list = driver_dict.keys()
toc_list.sort()
for driver in toc_list:
    if driver_dict.get(driver, {}) != {}:
        toc.write('   ' + driver + '\n')
toc.close()

for driver_module, driver_info in driver_dict.items():
    if driver_info == {}:
        continue
    with file(os.path.join(canpath, DRIVER_DOC, str(driver_module) + ".rst"), "w+") as f:
        f.write(template.format(driver=driver_module, 
                                ul="="*len(driver_module),
                                class_name=driver_module.split('.')[-1] ,
                                **driver_info))
   
# Sphinx build
os.system("{} -b html {} {}".format(SPHINXBUILD, DOC_SOURCE_DIR, DOC_BUILD_DIR) )