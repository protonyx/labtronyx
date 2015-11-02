"""
.. codeauthor:: Kevin Kennedy <protonyx@users.noreply.github.com>

"""
from labtronyx.bases import DriverBase
from labtronyx.common.errors import *


class d_335XX(DriverBase):
    """
    Driver for Agilent Function Generators

    .. warning::

       This driver is a stub and has no implemented functionality
    """
    author = 'KKENNEDY'
    version = '1.0'
    deviceType = 'Function Generator'
    compatibleInterfaces = ['VISA']
    compatibleInstruments = {
        'Agilent': ['33509B', '33510B', '33511B', '33512B', '33519B', '33520B', '33521A', '33521B', '33522A', '33522B']
    }

    @classmethod
    def VISA_validResource(cls, identity):
        return identity[0] == 'Agilent Technologies' and identity[1] in cls.compatibleInstruments['Agilent']

    def getProperties(self):
        pass