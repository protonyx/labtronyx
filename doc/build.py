import sys
import os
import importlib
import sets

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
print canpath
rootpath = os.path.realpath(os.path.join(canpath, ROOT_DIR))
print rootpath
libpath = os.path.realpath(os.path.join(rootpath, LIB_DIR))
print libpath
sys.path.append(canpath)
sys.path.append(rootpath)
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
    for driver_module, driver_info in driver_dict.items():
        if driver_info == {}:
            continue

        toc_list.append(driver_module)
        
        print "Processing: {0}".format(driver_module)
        driver_filename = os.path.join(driver_folder, str(driver_module) + ".rst")

        with file(driver_filename, "w+") as f:
            f.write(gen_sphinx_header(driver_module, "="))
            
            f.write(gen_sphinx_automodule(driver_module, ['show-inheritance', 'members']))

    print "Generating driver toctree..."
    
    # Create index with TOCtree
    toc_list.sort()
     
    toc_filename = os.path.realpath(os.path.join(canpath, DRIVER_DOC, 'index.rst'))
    with file(toc_filename, "w+") as f:
        f.write(gen_sphinx_header("Drivers", "="))
         
        f.write(gen_sphinx_toctree(toc_list))
    
def build_instrument_docs():
    print "Generating Supported Instruments..."

    import labtronyx.drivers
    driver_dict = labtronyx.drivers.getAllDrivers()

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

    # Get list of vendors
    vendors = list(set([x.get('deviceVendor') for x in driver_dict.values()]))
    if None in vendors:
        vendors.remove(None)
    vendors.sort()

    # Create RST file for each vendor
    for vendor in vendors:
        print "Processing vendor {0}...".format(vendor)

        # Get dict of drivers from this vendor
        vendor_drivers = {}
        for driver, driver_info in driver_dict.items():
            if driver_info.get('deviceVendor') == vendor:
                vendor_drivers[driver] = driver_info

        # Get list of unique device types from this vendor
        vendor_types = list(set([x.get('deviceType') for x in vendor_drivers.values()]))
        if None in vendor_types:
            vendor_types.remove(None)
        vendor_types.sort()

        vendor_filename = os.path.realpath(os.path.join(instr_folder, str(vendor) + '.rst'))
        with file(vendor_filename, "w+") as f:
            f.write(gen_sphinx_header(vendor, "="))

            for dev_type in vendor_types:
                f.write(gen_sphinx_header(dev_type, '-'))

                for driver, driver_info in vendor_drivers.items():
                    if driver_info.get('deviceType') == dev_type:

                        for model in driver_info.get('deviceModel', []):
                            f.write("  * :doc:`{0} <../../{1}/{2}>`\n".format(model, DRIVER_DOC, driver))

                        f.write("\n")

    # Create index with TOCtree
    toc_filename = os.path.realpath(os.path.join(instr_folder, 'index.rst'))
    with file(toc_filename, "w+") as f:
        f.write(gen_sphinx_header("Supported Instruments", "="))
        
        f.write(gen_sphinx_toctree(vendors))

if __name__ == "__main__":
    build_driver_docs()
