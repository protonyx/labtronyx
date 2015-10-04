"""
.. codeauthor:: Kevin Kennedy <protonyx@users.noreply.github.com>

"""
from labtronyx.bases import Base_Driver
from labtronyx.common.errors import *

info = {
    # Plugin author
    'author':               'KKENNEDY',
    # Plugin version
    'version':              '1.0',
    # Last Revision Date
    'date':                 '2015-10-04',
}

class d_335XX(Base_Driver):
    """
    Driver for Agilent Function Generators

    .. warning::

       This driver is a stub and has no implemented functionality
    """
    info = {
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
        'validResourceTypes':   ['VISA']
    }

    @classmethod
    def VISA_validResource(cls, identity):
        return identity[0] == 'Agilent Technologies' and identity[1] in cls.info['deviceModel']