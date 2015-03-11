from Base_Applet import Base_Applet

import Tkinter as Tk

import matplotlib
import pylab

class source(Base_Applet):
    
    info = {
        # View revision author
        'author':               'KKENNEDY',
        # View version
        'version':              '1.0',
        # Revision date of View version
        'date':                 '2015-03-11',    
        
        # List of compatible models
        'validDrivers':          ['BK_Precision.Source.m_911X', 
                                  'BK_Precision.Source.m_912X',
                                  'BK_Precision.Source.m_XLN',
                                  'Chroma.Source.m_620XXP',
                                  'Regatron.m_GSS']
    }