from Base_Driver import Base_Driver

class m_Template(Base_Driver):
    
    info = {
        # Model revision author
        'author':               '',
        # Model version
        'version':              '1.0',
        # Revision date of Model version (YYYY-MM-DD)
        'date':                 '1-1-1970',
        # Device Manufacturer
        'deviceVendor':         'Unknown',
        # List of compatible device models
        'deviceModel':          [''],
        # Device type    
        'deviceType':           'Generic',      
        
        # List of compatible resource types
        'validResourceTypes':   [''],
        
        #=======================================================================
        # VISA Attributes        
        #=======================================================================
        # Compatible VISA Manufacturers
        'VISA_compatibleManufacturers': [''],
        # Compatible VISA Models
        'VISA_compatibleModels':        ['']            
    }
    
    def _onLoad(self):
        self.instr = self.getResource()
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        prop = Base_Driver.getProperties(self)
        
        # Add any additional properties here
        return prop
    
    