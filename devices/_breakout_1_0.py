from pyControl.hardware import *

class Breakout_1_0(Mainboard):
    def __init__(self):
        # Inputs and outputs.
        self.port_1 = Port(DIO_A='X1' , DIO_B='X2' , POW_A='Y8', POW_B='Y4')
        self.port_2 = Port(DIO_A='X3' , DIO_B='X4' , POW_A='Y7', POW_B='Y3')
        self.port_3 = Port(DIO_A='X7' , DIO_B='X8' , POW_A='Y6', POW_B='Y2')
        self.port_4 = Port(DIO_A='X12', DIO_B='X11', POW_A='Y5', POW_B='Y1')
        self.BNC_1 = 'Y11'
        self.BNC_2 = 'Y12'
        self.DAC_1 = 'X5'
        self.DAC_2 = 'X6'
        self.button_1 = 'X9'
        self.button_2 = 'X10'
        # Set default pullup/pulldown resistors.
        self.set_pull_updown({'up': ['X9','X10']})