import sys
import os
import importlib
import sets
import copy

#===============================================================================
# Configuration
#===============================================================================
ROOT_DIR = "../"
LIB_DIR = "labtronyx"

# Drivers
DRIVER_SRC = "labtronyx.drivers"
DRIVER_DOC = "api/drivers"

# Supported Instruments
INSTRUMENT_DOC = "instruments"

canpath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir))) # Resolves symbolic links
rootPath = os.path.realpath(os.path.join(canpath, ROOT_DIR))
libPath = os.path.realpath(os.path.join(rootPath, LIB_DIR))

sys.path.append(rootPath)

import labtronyx

# Load Plugins

# Directories to search
dirs = ['drivers', 'interfaces']
dirs_res = map(lambda dir: os.path.join(libPath, dir), dirs)

# Categorize plugins by base class
cat_filter = {
    "drivers": labtronyx.bases.Base_Driver,
    "interfaces": labtronyx.bases.Base_Interface,
    "resources": labtronyx.bases.Base_Resource
}

plugin_manager = labtronyx.common.plugin.PluginManager(directories=dirs_res, categories=cat_filter)
plugin_manager.search()

# # Load Drivers
# self._drivers = plugin_manager.getPluginsByCategory('drivers')
#
# # Load Interfaces
# for interface_name in self.plugin_manager.getPluginsByCategory('interfaces'):
#     self.enableInterface(interface_name)

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

def gen_sphinx_autoclass(cls, options):
    ret = '.. autoclass:: {0}\n'.format(cls)
    for opt in options:
        ret += '   :{0}:\n'.format(opt)
    ret += '\n'

    return ret

def gen_sphinx_toctree(elems, depth=2):
    ret = '.. toctree::\n'
    ret += '   :maxdepth: %s\n\n' % depth

    for item in elems:
        ret += '   {0}\n'.format(item)
        
    ret += '\n'
    
    return ret

def build_driver_docs():
    print "Generating driver documentation..."

    driver_folder = os.path.join(canpath, DRIVER_DOC)

    # Clear out old driver files
    files = os.listdir(driver_folder)
    for filename in files:
        file_path = os.path.join(driver_folder, filename)

        try:
            if os.path.isfile(file_path):
                print "Deleting {0}".format(filename)
                os.unlink(file_path)
        except Exception, e:
            print e
    
    # Create RST file for each driver
    toc_list = []
    for driver_name, driver_cls in plugin_manager.getPluginsByCategory('drivers').items():
        driver_info = driver_cls.info
        driver_class = driver_name.split('.')[-1]
        driver_module = driver_name[:-1*(len(driver_class)+1)]

        if driver_info == {}:
            continue

        if driver_name not in toc_list:
            toc_list.append(driver_name)
        
        print "Processing: {0}".format(driver_name)
        driver_filename = os.path.join(driver_folder, str(driver_name) + ".rst")

        with file(driver_filename, "w+") as f:
            f.write(gen_sphinx_header(driver_name, "="))
            
            f.write(gen_sphinx_autoclass('labtronyx.drivers.' + driver_name, ['members']))

    print "Generating driver toctree..."
    
    # Create index with TOCtree
    toc_list.sort()
     
    toc_filename = os.path.realpath(os.path.join(canpath, DRIVER_DOC, 'index.rst'))
    with file(toc_filename, "w+") as f:
        f.write(gen_sphinx_header("Drivers", "="))
         
        f.write(gen_sphinx_toctree(toc_list, 1))
    
def build_instrument_docs():
    print "Generating Supported Instruments..."

    instr_folder = os.path.join(canpath, INSTRUMENT_DOC)
    
    # Clear out old driver files
    files = os.listdir(instr_folder)
    for filename in files:
        file_path = os.path.join(instr_folder, filename)

        try:
            if os.path.isfile(file_path):
                print "Deleting {0}".format(filename)
                os.unlink(file_path)
        except Exception, e:
            print e

    instruments = []

    # Iterate drivers and scrape instrument information
    for driver_name, driver_cls in plugin_manager.getPluginsByCategory('drivers').items():
        driver_info = driver_cls.info
        # driver_class = driver_name.split('.')[-1]
        # driver_module = driver_name[:-1*(len(driver_class)+1)]

        for driver_model in driver_info.get('deviceModel'):
            entry = (driver_info.get('deviceVendor'), driver_info.get('deviceType'), driver_model, driver_name)
            instruments.append(entry)

    # Sort by model, vendor
    instruments.sort(key=lambda x: x[2])
    instruments.sort(key=lambda x: x[0])

    filename = os.path.realpath(os.path.join(instr_folder, 'index.rst'))
    with file(filename, "w+") as f:
        cur_vendor = ''

        f.write(gen_sphinx_header("Supported Instruments", "="))

        for instr in instruments:
            d_vendor, d_type, d_model, d_name = instr

            if cur_vendor != d_vendor:
                cur_vendor = d_vendor
                f.write("\n")
                f.write(gen_sphinx_header(d_vendor, "-"))

            f.write("  * :doc:`{0} {1} <../../{2}/{3}>`\n".format(d_model, d_type, DRIVER_DOC, d_name))


if __name__ == "__main__":
    build_driver_docs()
    build_instrument_docs()
