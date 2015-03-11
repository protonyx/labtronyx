from Base_Applet import Base_Applet

import Tkinter as Tk

import matplotlib
import pylab

class function_generator(Base_Applet):
    
    info = {
        # View revision author
        'author':               'KKENNEDY',
        # View version
        'version':              '1.0',
        # Revision date of View version
        'date':                 '2015-03-11',    
        
        # List of compatible models
        'validDrivers':          ['Agilent.FunctionGenerator.m_335XX'
                                  'BK_Precision.FunctionGenerator.m_406X']
    }