import time
import struct
import serial
import csv

import numpy as np

import sys
sys.path.append('.')

from t_Base import t_Base

class t_AMPED(t_Base):
    
    test_info = {
        'name': "AMPED v2.2 Test Suite",
        'version': 1.0
    }
    
    def open(self):
        # Instruments
        self.requireInstrument('DMM - Primary Voltage', 'pri_voltage', serial='123F12106')
        self.requireInstrument('DMM - Primary Current', 'pri_current', serial='343B12138')
        self.requireInstrument('DMM - Secondary Voltage', 'sec_voltage', serial='123E12681')
        self.requireInstrument('DMM - Secondary Current', 'sec_current', serial='123G11250')
        self.requireInstrument('Source - Primary', 'pri_source', serial='602078010696820011')
        self.requireInstrument('Source - Secondary', 'sec_source', serial='00257')
        self.requireInstrument('AMPED Converter', 'conv', driver='models.UPEL.AMPED.m_BMS')
        self.requireInstrument('Load - Secondary', 'load', driver='models.BK_Precision.Load.m_85XX')
        
        # Tests
        self.registerTest('Calibrate', 'test_Calibrate')
        self.registerTest('Closed Loop Regulation', 'test_ClosedLoopRegulation')
        self.registerTest('Test Efficiency', 'test_Efficiency')
    
    def startup(self):
        try:
            self.pri_voltage = self.instr.getInstrument_serial("123F12106")
            self.pri_current = self.instr.getInstrument_serial("343B12138")
            self.pri_source = self.instr.getInstrument_serial("602078010696820011")
            self.sec_voltage = self.instr.getInstrument_serial("123E12681")
            self.sec_current = self.instr.getInstrument_serial("123G11250")
            self.sec_source = self.instr.getInstrument_serial("00257")
             
            #conv_uuid = self.instr.findResource('localhost', 'COM3')[0] # COM15 for the nice RS-485 converters
            #self.instr.loadModel(conv_uuid, 'models.UPEL.AMPED.m_BMS', 'm_BMS')
            self.conv = self.instr.getInstrument_driver('models.UPEL.AMPED.m_BMS') #(conv_uuid)
             
            #load_uuid = self.instr.findResource('localhost', 'COM4')[0]
            #self.instr.loadModel(conv_uuid, 'models.BK_Precision.Load.m_85XX', 'm_85XX')
            self.load = self.instr.getInstrument_driver('models.BK_Precision.Load.m_85XX') #(load_uuid)
             

    
            # Configuration
            self.pri_voltage.setFunction_DC_Voltage()
            self.pri_current.setFunction_DC_Current()
            self.sec_voltage.setFunction_DC_Voltage()
            self.sec_current.setFunction_DC_Current()
            
            #self.pri_source.powerOff()
            self.pri_source.setVoltage(3.0)
            self.pri_source.setCurrent(10.0)
            #self.sec_source.powerOff()
            self.sec_source.setVoltage(12.0)
            self.sec_source.setCurrent(3.0)
            time.sleep(1.0)
            
            # Power on primary
            self.pri_source.powerOn()
            time.sleep(1.0)
            
            # Power on secondary
            self.logger.info("Powering On...")
            self.sec_source.powerOn()
            time.sleep(2.0)
            
            # Initial setup of converter
            # Issue an identify command to get the connected module
            self.convAddress = self.conv.identify()
            self.logger.info("Identified module: %i", self.convAddress)
            
            self.conv.calibrate(1, 1)
            self.conv.enableSampling(self.convAddress)
            self.conv.shutoff_wdt(self.convAddress)
        
        except:
            self.logger.exception("Exception during test startup")
            return False
            
        return True
    
    def shutdown(self):
        # turn off so there's no voltage present when disconnecting/connecting modules
        self.conv.disableSwitching(self.convAddress)
        
        time.sleep(1.0)
        
        self.pri_source.powerOff()
        self.sec_source.powerOff()
        self.load.powerOff()
        
        return True
                    
    def test_Calibrate(self):
        
        #=======================================================================
        # Read calibration data from CSV
        #=======================================================================
        calibrationData = {}
        try:
            with open('calibrationData.csv', 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    try:
                        addr = int(row[0])
                        self.calibrationData[addr] = row[1:]
                    except:
                        self.logger.exception("Error while reading CSV row: %s" % row)
                        return False
        except IOError:
            # File doesn't exist
            pass
        
        #=======================================================================
        # Run Calibration scripts
        #=======================================================================
            z1 = self.cal_SecVoltage()
            z2 = self.cal_PriVoltage()
            z3 = self.cal_CurrentSensor()
            
            z = list(z1) + list(z2) + list(z3)
            
        #=======================================================================
        # Write data to CSV
        #=======================================================================
        try:
            with open('calibrationData.csv', 'w+') as f:
                writer = csv.writer(f)
                for addr, data in self.calibrationData.items():
                    try:
                        writer.writerow([addr] + list(data))
                    except:
                        self.logger.exception("Error writing data for [%s] to file: %s" % (addr, str(data)))
                        return False
                        
        except:
            self.logger.exception("Error during calibration")
            return False
        
    def cal_linearRegression(self, x, y):
        """
        Calculate the linear regression
        """
        # Phase 1 Polyfit
        z = np.polyfit(y, x, 1)
        
        # Outlier Removal
        outliers = []
        for i, pt in enumerate(x):
            # Calculate the point on the best-fit line
            reg = (pt * z[0]) - z[1]
            # Remove points that are far away from the line
            if abs(reg - y[i]) > 20:
                outliers.append[i]
                
        outliers = outliers.sort(reverse=True)
        for i in outliers:
            # Remove the outliers from the dataset, starting with the higher indicies
            x.delete[i]
            y.delete[i]
            
        # Run the polyfit again with the filtered data
        z = np.polyfit(y, x, 1)
        
        return z
    
    def cal_SecVoltage(self):
        
        #=======================================================================
        # Test Spinup
        #=======================================================================
        self.load.powerOff()
        self.pri_source.powerOff()
        self.sec_source.setVoltage(12.0)
        
        #=======================================================================
        # Calibration Parameters
        #=======================================================================
        minVoltage = 13.5
        maxVoltage = 16.2
        
        num_operatingPoints = 6
        num_dataPoints = 5
        
        #=======================================================================
        # Test Variables
        #=======================================================================
        x = []
        y = []
        
        stepWidth = (maxVoltage - minVoltage) / num_operatingPoints
        steps = [minVoltage + stepWidth*pt for pt in range(points+1)]
        sampleIndex = 0
        
        self.pri_source.setVoltage(startingVoltage)
        
        time.sleep(0.1)
        
        fmt = "| {0:7} | {1:16} | {2:16} | {3:16} |"
        self.logger.info("-"*65)
        self.logger.info(fmt.format('Sample', 'Operating Point', 'Multimeter', 'Converter'))
        self.logger.info("-"*65)
        
        self.sec_source.setVoltage(startingVoltage)
        time.sleep(0.1)
        
        for opPoint in steps:
            self.sec_source.setVoltage(opPoint)
            time.sleep(3.0)
            
            for desired_x in range(dataPointsPerPoint):
                _, vout, _, _, _ = conv_getData(self.convAddress)
                sampleIndex += 1
                
                try:
                    dataPoint = self.sec_voltage.getMeasurement()
                except:
                    dataPoint = 0
                    
                if vin == 0 or dataPoint == 0:
                    self.logger.info(fmt.format(sample, opPoint, "INVALID", "INVALID"))
                else:
                    self.logger.info(fmt.format(sample, opPoint, dataPoint, vout))
                    x.append(dataPoint)
                    y.append(vout)
                                     
                time.sleep(0.25)
        
        self.logger.info("-"*65)
        
        self.logger.info("Removing Outliers...")
        
        x=np.array(x)
        y=np.array(y)
        z = self.cal_linearRegression(x, y)
        
        self.logger.info("Gain: %f" % z[0])
        self.logger.info("Offset: %f" % z[1])
        
        # Set Secondary Source to nominal 12.0 V
        self.sec_source.setVoltage(12.0)
        
        return z
    
    def cal_PriVoltage(self):
        
        #=======================================================================
        # Test Spinup
        #=======================================================================
        self.load.powerOff()
        self.pri_source.powerOff()
        self.sec_source.setVoltage(12.0)
        
        #=======================================================================
        # Calibration Parameters
        #=======================================================================
        minVoltage = 3.0
        maxVoltage = 4.2
        
        num_operatingPoints = 6
        num_dataPoints = 5
        
        #=======================================================================
        # Test Variables
        #=======================================================================
        x = []
        y = []
        
        stepWidth = (maxVoltage - minVoltage) / num_operatingPoints
        steps = [minVoltage + stepWidth*pt for pt in range(points+1)]
        sampleIndex = 0
        
        self.pri_source.setVoltage(startingVoltage)
        
        time.sleep(0.1)
        
        fmt = "| {0:7} | {1:16} | {2:16} | {3:16} |"
        self.logger.info("-"*65)
        self.logger.info(fmt.format('Sample', 'Operating Point', 'Multimeter', 'Converter'))
        self.logger.info("-"*65)
        
        for opPoint in steps:
            self.pri_source.setVoltage(opPoint)
            
            for desired_x in range(dataPointsPerPoint):
                _, _, vin, _, _ = conv_getData(self.convAddress)
                sampleIndex += 1
                
                try:
                    dataPoint = self.pri_voltage.getMeasurement()
                except:
                    dataPoint = 0
                    
                if vin == 0 or dataPoint == 0:
                    self.logger.info(fmt.format(sample, opPoint, "INVALID", "INVALID"))
                else:
                    self.logger.info(fmt.format(sample, opPoint, dataPoint, vin))
                    x.append(dataPoint)
                    y.append(vin)
                                     
                time.sleep(0.25)
                
        self.logger.info("-"*65)
        
        self.logger.info("Removing Outliers...")
        
        x=np.array(x)
        y=np.array(y)
        z = self.cal_linearRegression(x, y)
        
        self.logger.info("Gain: %f" % z[0])
        self.logger.info("Offset: %f" % z[1])
        
        return z
    
    def cal_CurrentSensor(self):
        #=======================================================================
        # Test Spinup
        #=======================================================================
        self.sec_source.setVoltage(14.0)
        self.sec_source.powerOn()
        
        self.pri_source.setVoltage(3.5)
        self.pri_source.powerOn()
        
        self.load.powerOff()
        self.load.SetMode('cv') # Constant Voltage 
        self.load.SetCVVoltage(13.5)
        self.load.powerOn()
        
        # Converter configuration
        self.conv.resetStatus(self.convAddress)
        self.conv.calibrate(self.convAddress)
        self.conv.enableSampling(self.convAddress)
        self.conv.shutoff_wdt(self.convAddress)
        self.conv.enableSwitching(self.convAddress)
        
        # Allow converter to start switching
        time.sleep(2.0)
        
        _, _, _, _, status = conv_getData(self.convAddress)
        
        #=======================================================================
        # Calibration Parameters
        #=======================================================================
        minPhase = 0
        maxPhase = 1100
        
        num_operatingPoints = 8
        num_dataPoints = 2
        
        #=======================================================================
        # Test Variables
        #=======================================================================
        x = []
        y = []
        
        stepWidth = (maxPhase - minPhase) / num_operatingPoints
        steps = [minPhase + stepWidth*pt for pt in range(points+1)]
        sampleIndex = 0
        
        self.pri_source.setVoltage(startingVoltage)
        
        time.sleep(0.1)
        
        fmt = "| {0:7} | {1:16} | {2:16} | {3:16} |"
        self.logger.info("-"*65)
        self.logger.info(fmt.format('Sample', 'Operating Point', 'Multimeter', 'Converter'))
        self.logger.info("-"*65)

        for opPoint in steps:
            conv_set_phase_angle(convAddress, long(opPoint))
            time.sleep(0.75)
            
            for desired_x in range(dataPointsPerPoint):
                _, _, _, iin, _ = conv_getData(self.convAddress)
                
                try:
                    dataPoint = self.pri_current.getMeasurement()
                except:
                    dataPoint = 0
                    
                if iin == 0 or dataPoint == 0:
                    self.logger.info(fmt.format(sample, opPoint, "INVALID", "INVALID"))
                else:
                    self.logger.info(fmt.format(sample, opPoint, dataPoint, iin))
                    x.append(dataPoint)
                    y.append(iin)
                    
                time.sleep(0.25)
        
        self.logger.info("-"*65)
        
        self.logger.info("Removing Outliers...")
        
        x=np.array(x)
        y=np.array(y)
        z = self.cal_linearRegression(x, y)
        
        self.logger.info("Gain: %f" % z[0])
        self.logger.info("Offset: %f" % z[1])
        
        # stop the power flow
        conv_set_phase_angle(convAddress, 0x0000)
        conv_disable_switching(self.convAddress)
        _, _, _, _, status = conv_getData(self.convAddress)
        
        return z
    
    def test_ClosedLoopRegulation(self):
        #===============================================================================
        # Test 4 - Closed Loop Regulation
        #===============================================================================
        self.logger.info("--- TEST 4 / CLOSED LOOP REGULATION ---")
        
        # Set instruments into known state
        self.sec_source.setVoltage(13.0)
        self.sec_source.powerOn()
        
        self.pri_source.setVoltage(3.85)
        self.pri_source.powerOn()
        
        self.load.powerOff()
        self.load.SetMode('cc') # Constant Voltage 
        self.load.SetCCCurrent(1.0)
        self.load.powerOn()
        
        time.sleep(1.0)
        
        # setup the converter again since power might have dropped out when the load was turned on
        self.conv.resetStatus(self.convAddress)
        self.conv.calibrate(self.convAddress)
        self.conv.enableSampling(self.convAddress)
        self.conv.shutoff_wdt(self.convAddress)
        
        desiredSet = 15.0
        desiredSet_conv = int(desiredSet * z1[0])# - int(z1[1])
        
        self.conv.set_vRef(convAddress, desiredSet_conv)
        self.conv.setMode_closedloop(self.convAddress)
        self.conv.enableSwitching(self.convAddress)
        
        # give time to settle
        time.sleep(2.0)
        
        # Measure output voltage
        avg = 0
        vout = 0
        vout_avg = 0
        points = 10
        points_valid = points
        while (points > 0):
        	try:	
        		dataPoint = self.sec_voltage.getMeasurement()
        		_, vout, _, _, _ = conv_getData(self.convAddress)
        		self.logger.info("    MM: %f", dataPoint)
        		self.logger.info("    Conv: %i", vout)
        		avg += dataPoint
        		vout_avg += vout
        		points -= 1
        		time.sleep(0.2)
                
        	except:
        		self.logger.exception("Invalid data point, retrying")
        		points -=1 # temporary to basically disable this as it will go on forever - need to think of a better way
        		points_valid -= 1
        
        # setting converter back to open loop
        self.conv.setMode_openloop(self.convAddress)
        
        output = avg / points_valid
        vout_avg = vout_avg / points_valid
        self.logger.info("    MM AVG: [%f]", output)
        self.logger.info("    Conv AVG: [%f]", vout_avg)
        
        pct_error = (abs(output - desiredSet)/desiredSet) * 100.0
        self.logger.info("    PERCENT ERROR (MM): [%f]", pct_error)
        pct_error = (abs(vout_avg - desiredSet_conv)/desiredSet_conv) * 100.0
        self.logger.info("    PERCENT ERROR (Conv): [%f]", pct_error)
    
    def test_Efficiency(self):
        #===============================================================================
        # Test 5 - Efficiency
        #===============================================================================
        self.logger.info("--- TEST 5 / EFFICIENCY ---")
        
        # Set instruments into known state
        self.sec_source.setVoltage(13.0)
        self.sec_source.powerOn()
        
        self.pri_source.setVoltage(3.85)
        self.pri_source.powerOn()
        
        self.load.powerOff()
        self.load.SetMode('cc') # Constant Current 
        self.load.SetCCCurrent(1.0)
        self.load.powerOn()
        
        # setup the converter again since power might have dropped out when the load was turned on
        self.conv.resetStatus(self.convAddress)
        self.conv.calibrate(self.convAddress)
        self.conv.enableSampling(self.convAddress)
        self.conv.shutoff_wdt(self.convAddress)
        self.conv.enableSwitching(self.convAddress)
        
        time.sleep(1.0)
        
        avg = 0
        points = 5
        while (points > 0):
            try:
                vin = self.pri_voltage.getMeasurement()		
                vout = self.sec_voltage.getMeasurement()
                iin = self.pri_current.getMeasurement()
                iout = self.sec_current.getMeasurement()
                dataPoint = ((vout * iout)/(vin * iin)) * 100.0
                self.logger.info("    Efficiency: %f", dataPoint)
                avg += dataPoint
                points -= 1
                time.sleep(0.2)
            except:
                self.logger.exception("Invalid data point, retrying")
                points -=1 # basically disable this as it will go on forever - need to think of a better way
        
        try:	
            output = avg / 5.0
        
            self.logger.info("    Avg Efficiency: %f", output)
        except:
            self.logger.exception("Efficiency Test Exception")
    
if __name__ == '__main__':
    test = t_AMPED()

