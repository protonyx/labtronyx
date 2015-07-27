from labtronyx.bases import Base_Driver

class m_335XX(Base_Driver):
    
    info = {
        # Model revision author
        'author':               'KKENNEDY',
        # Model version
        'version':              '1.0',
        # Revision date of Model version
        'date':                 '2015-03-11',
        # Device Manufacturer
        'deviceVendor':         'Agilent',
        # List of compatible device models
        'deviceModel':          ['33509B',
                                 '33510B',
                                 '33511B',
                                 '33512B',
                                 '33519B', 
                                 '33520B',
                                 '33521A', '33521B', 
                                 '33522A', '33522B'
                                 ],
        # Device type    
        'deviceType':           'Function Generator',      
        
        # List of compatible resource types
        'validResourceTypes':   ['VISA'],  
        
        #=======================================================================
        # VISA Attributes        
        #=======================================================================
        # Compatible VISA Manufacturers
        'VISA_compatibleManufacturers': ['Agilent Technologies'],
        # Compatible VISA Models
        'VISA_compatibleModels':        ['33509B', '33510B', '33511B',
                                         '33512B', '33519B', '33520B',
                                         '33521A', '33521B', '33522A', 
                                         '33522B']
    }
    
    def _onLoad(self):
        self.instr = self.getResource()
    
    def _onUnload(self):
        pass