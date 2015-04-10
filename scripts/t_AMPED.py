import sys
import time
import struct
import csv

import serial
import numpy as np

sys.path.append('..')
from labtronyx import Base_Script

class t_AMPED(Base_Script):
    
    test_info = {
        'name': "AMPED v2.2 Test Suite",
        'version': 1.0
    }
    
    def open(self):
        # Manually load some instruments
        try:
            conv = self.instr.findInstrument(resID='COM39')[0] # COM15 for the nice RS-485 converters
            conv.loadDriver('UPEL.AMPED.m_BMS')
            self.logger.debug("Registered AMPED BMS on COM39")
            
            load = self.instr.findInstrument(resID='COM46')[0]
            load.loadDriver('BK_Precision.Load.m_85XX')
            self.logger.debug("Registered BK Load on COM46")
        except:
            pass
            
        # Instruments
        self.requireInstrument('DMM - Primary Voltage', 'pri_voltage', deviceSerial='MY48005640') #'123F12106')
        self.requireInstrument('DMM - Primary Current', 'pri_current', deviceSerial='123D12535')
        self.requireInstrument('DMM - Secondary Voltage', 'sec_voltage', deviceSerial='MY48005608') #'123E12681')
        self.requireInstrument('DMM - Secondary Current', 'sec_current', deviceSerial='123F12106') #'123G11250')
        self.requireInstrument('Source - Primary', 'pri_source', deviceSerial='602078010696820011')
        self.requireInstrument('Source - Secondary', 'sec_source', deviceSerial='00257')
        self.requireInstrument('AMPED Converter', 'conv', driver='models.UPEL.AMPED.m_BMS')
        self.requireInstrument('Load - Secondary', 'load', driver='models.BK_Precision.Load.m_85XX')
        
        # Tests
        self.registerTest('Startup', 'startup')
        #self.registerTest('Identify', 'test_Identify') # Identify is now done during startup
        self.registerTest('Calibrate Secondary Voltage', 'test_CalibrateSecVoltage')
        self.registerTest('Calibrate Primary Voltage', 'test_CalibratePriVoltage')
        self.registerTest('Calibrate Current Sensor', 'test_CalibrateCurrent')
        self.registerTest('Closed Loop Regulation', 'test_ClosedLoopRegulation')
        self.registerTest('Test Efficiency', 'test_Efficiency')
        self.registerTest('Shutdown', 'shutdown')
    
    def startup(self):
        try:
            # Configuration
            #self.pri_current.reset()
            #self.sec_current.reset()
            #time.sleep(3.0)
            
            self.logger.debug("Setting Instrument Functions...")
            self.pri_voltage.setFunction_DC_Voltage()
            self.pri_current.setFunction_DC_Current()
            self.sec_voltage.setFunction_DC_Voltage()
            self.sec_current.setFunction_DC_Current()
            
            time.sleep(0.5)
            self.pri_current.setRange_Manual()
            self.sec_current.setRange_Manual()
            
            time.sleep(0.5)
            self.pri_current.setRange(20)
            self.sec_current.setRange(20)
            
            self.pri_source.powerOff()
            self.pri_source.setVoltage(3.5)
            self.pri_source.setCurrent(10.0)
            self.sec_source.powerOff()
            self.sec_source.setVoltage(12.0)
            self.sec_source.setCurrent(3.0)
            time.sleep(1.0)

            self.logger.info("Powering On...")
            
            # Power on primary
            self.pri_source.powerOn()
            time.sleep(1.0)
            
            # Power on secondary
            self.sec_source.powerOn()
            time.sleep(2.0)
            
            # Initial setup of converter
            # Issue an identify command to get the connected module
            self.convAddress = self.conv.identify()
            if self.convAddress is not None:
                self.logger.info("Identified module: %i", self.convAddress)
            else:
                self.convAddress = 0xFA
                self.logger.info("Unable to identify, defaulting to broadcast")
            
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

    def test_Identify(self):
        identify_addr = self.conv.identify()

        if identify_addr is not None:
            self.logger.info("Identified module: %i", identify_addr)
            return True
        
        else:
            self.logger.info("No response")
            return False
        
    def readCalibration(self):
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
                        calibrationData[addr] = row[1:]
                    except:
                        self.logger.exception("Error while reading CSV row: %s" % row)
                        return False
        except IOError:
            # File doesn't exist
            pass
        
        return calibrationData
    
    def writeCalibration(self, calibrationData):
        #=======================================================================
        # Write data to CSV
        #=======================================================================
        try:
            f = open('calibrationData.csv', 'w+')
        except:
            f = open('calibrationDataTemp_' + int(time.time()) + '.csv', 'w+')
            
        try:
            writer = csv.writer(f)
            for addr, data in calibrationData.items():
                writer.writerow([addr] + list(data))
                    
        except:
            self.logger.exception("Error writing data for [%s] to file: %s" % (addr, str(data)))
            return False
        
        finally: 
            f.close()

        return True

    def test_CalibrateSecVoltage(self):
        if self.convAddress is None or self.convAddress == 0xFA:
            self.logger.error("Unable to identify a module to calibrate.")
            return False
            
        else:
            calibrationData = self.readCalibration()
            calDevice = calibrationData.get(self.convAddress, [1.0, 0.0, 1.0, 0.0, 1.0, 0.0])
            
            res = self.cal_SecVoltage()
            if len(res) == 2:
                calDevice[0] = res[0]
                calDevice[1] = res[1]
            else:
                return False

            calibrationData[self.convAddress] = calDevice
            self.writeCalibration(calibrationData)
            
        return True
    
    def test_CalibratePriVoltage(self):
        if self.convAddress is None or self.convAddress == 0xFA:
            self.logger.error("Unable to identify a module to calibrate.")
            return False
            
        else:
            calibrationData = self.readCalibration()
            calDevice = calibrationData.get(self.convAddress, [1.0, 0.0, 1.0, 0.0, 1.0, 0.0])
            
            res = self.cal_PriVoltage()
            if len(res) == 2:
                calDevice[2] = res[0]
                calDevice[3] = res[1]
            else:
                return False

            calibrationData[self.convAddress] = calDevice
            self.writeCalibration(calibrationData)
            
        return True
    
    def test_CalibrateCurrent(self):
        if self.convAddress is None or self.convAddress == 0xFA:
            self.logger.error("Unable to identify a module to calibrate.")
            return False
            
        else:
            calibrationData = self.readCalibration()
            calDevice = calibrationData.get(self.convAddress, [1.0, 0.0, 1.0, 0.0, 1.0, 0.0])
            
            res = self.cal_CurrentSensor()
            if len(res) == 2:
                calDevice[4] = res[0]
                calDevice[5] = res[1]
            else:
                return False

            calibrationData[self.convAddress] = calDevice
            self.writeCalibration(calibrationData)
            
        return True
                    
    #def test_Calibrate(self):
        #=======================================================================
        # Run Calibration scripts
        #=======================================================================
#===============================================================================
#         z1 = self.cal_SecVoltage()
#         z2 = self.cal_PriVoltage()
#         z3 = self.cal_CurrentSensor()
# 
#         fmt = " {0:20} | {1:15} | {2:15}"
#         self.logger.info("-"*50)
#         self.logger.info("CALIBRATION SUMMARY:")
#         self.logger.info("-"*50)
#         self.logger.info(fmt.format('Sensor', 'Gain', 'Offset'))
#         self.logger.info("-"*50)
#         self.logger.info(fmt.format('Secondary Voltage', z1[0], z1[1]))
#         self.logger.info(fmt.format('Primary Voltage', z2[0], z2[1]))
#         self.logger.info(fmt.format('Current', z3[0], z3[1]))
#         self.logger.info("-"*50)
#             
#         z = list(z1) + list(z2) + list(z3)
# 
#         calibrationData[self.convAddress] = z
#===============================================================================

    def cal_linearRegression(self, x, y):
        """
        Calculate the linear regression
        """
        detect_outliers = False
        
        # Phase 1 Polyfit
        xp1 = np.array(x)
        yp1 = np.array(y)
        z = np.polyfit(xp1, yp1, 1)

        if detect_outliers == True:
            # Outlier Removal
            outliers = []
            for i, pt in enumerate(x):
                # Calculate the point on the best-fit line
                reg = (pt * z[0]) - z[1]
                # Remove points that are far away from the line
                if abs(reg - y[i]) > 20:
                    outliers.append(i)
                    
            outliers.sort(reverse=True)
            for i in outliers:
                # Remove the outliers from the dataset, starting with the higher indicies
                x.delete(i)
                y.delete(i)
                
            # Run the polyfit again with the filtered data
            xp2 = np.array(x)
            yp2 = np.array(y)
            z = np.polyfit(xp2, yp2, 1)
        
        return z
    
    def cal_SecVoltage(self):
        self.logger.info("Calibrating Secondary Voltage")
        #=======================================================================
        # Test Spinup
        #=======================================================================
        self.load.powerOff()
        self.pri_source.setVoltage(3.5)
        self.sec_source.setVoltage(12.0)
        self.pri_source.powerOn()
        self.sec_source.powerOn()

        # Converter configuration
        self.conv.resetStatus(self.convAddress)
        
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
        steps = [minVoltage + stepWidth*pt for pt in range(num_operatingPoints+1)]
        sampleIndex = 0
        
        fmt = "| {0:7} | {1:16} | {2:16} | {3:16} |"
        self.logger.info("-"*68)
        self.logger.info(fmt.format('Sample', 'Operating Point', 'Multimeter', 'Converter'))
        self.logger.info("-"*68)
        
        self.sec_source.setVoltage(minVoltage)
        time.sleep(0.1)

        for opPoint in steps:
            self.sec_source.setVoltage(opPoint)
            time.sleep(2.0)
            
            for desired_x in range(num_dataPoints):
                try:
                    _, dataPoint_m, _, _, _ = self.conv.getData(self.convAddress)
                except:
                    status = self.conv.getLastStatus()
                    self.logger.error("Converter reported status: %i", status)
                    
                sampleIndex += 1
                
                try:
                    dataPoint = self.sec_voltage.getMeasurement()
                except:
                    dataPoint = 0
                    
                if dataPoint_m == 0 or dataPoint == 0:
                    self.logger.info(fmt.format(sampleIndex, opPoint, "INVALID", "INVALID"))
                else:
                    self.logger.info(fmt.format(sampleIndex, opPoint, dataPoint, dataPoint_m))
                    x.append(dataPoint)
                    y.append(dataPoint_m)
                                     
                time.sleep(0.25)
        
        self.logger.info("-"*68)
        
        self.logger.info("Running Linear Regression...")
        
        z = self.cal_linearRegression(x, y)
        
        self.logger.info("Gain: %f" % z[0])
        self.logger.info("Offset: %f" % z[1])
        
        # Set Secondary Source to nominal 12.0 V
        self.sec_source.setVoltage(12.0)

        # Calibration with no voltage on the primary side will cause a converter fault
        self.conv.resetStatus(self.convAddress)
        
        return z
    
    def cal_PriVoltage(self):
        self.logger.info("Calibrating Primary Voltage")
        #=======================================================================
        # Test Spinup
        #=======================================================================
        self.load.powerOff()
        self.pri_source.setVoltage(3.5)
        self.sec_source.setVoltage(12.0)
        self.pri_source.powerOn()
        self.sec_source.powerOn()
        
        # Converter configuration
        self.conv.resetStatus(self.convAddress)
        
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
        steps = [minVoltage + stepWidth*pt for pt in range(num_operatingPoints+1)]
        sampleIndex = 0
        
        fmt = "| {0:7} | {1:16} | {2:16} | {3:16} |"
        self.logger.info("-"*68)
        self.logger.info(fmt.format('Sample', 'Operating Point', 'Multimeter', 'Converter'))
        self.logger.info("-"*68)
        
        for opPoint in steps:
            self.pri_source.setVoltage(opPoint)
            time.sleep(2.0)
            
            for desired_x in range(num_dataPoints):
                _, _, dataPoint_m, _, _ = self.conv.getData(self.convAddress)
                sampleIndex += 1
                
                try:
                    dataPoint = self.pri_voltage.getMeasurement()
                except:
                    dataPoint = 0
                    
                if dataPoint_m == 0 or dataPoint == 0:
                    self.logger.info(fmt.format(sampleIndex, opPoint, "INVALID", "INVALID"))
                else:
                    self.logger.info(fmt.format(sampleIndex, opPoint, dataPoint, dataPoint_m))
                    x.append(dataPoint)
                    y.append(dataPoint_m)
                                     
                time.sleep(0.25)
                
        self.logger.info("-"*68)
        
        self.logger.info("Running Linear Regression...")
        
        z = self.cal_linearRegression(x, y)
        
        self.logger.info("Gain: %f" % z[0])
        self.logger.info("Offset: %f" % z[1])

        # Calibration with no voltage on the secondary side will cause a converter fault
        self.conv.resetStatus(self.convAddress)
        
        return z
    
    def cal_CurrentSensor(self):
        self.logger.info("Calibrating Current Sensor")
        #=======================================================================
        # Test Spinup
        #=======================================================================
        self.sec_source.setVoltage(14.0)
        self.sec_source.powerOn()
        
        self.pri_source.setVoltage(3.5)
        self.pri_source.powerOn()
        
        self.load.powerOff()
        self.load.SetMode('cc') # Constant Current 
        self.load.SetCCCurrent(0.0)
        self.load.powerOn()
        
        # Converter configuration
        self.conv.resetStatus(self.convAddress)
        self.conv.enableSampling(self.convAddress)
        self.conv.shutoff_wdt(self.convAddress)
        
        self.conv.enableSwitching_open(self.convAddress)
        
        # Allow converter to start switching
        time.sleep(5.0)

        self.conv.close_loop(self.convAddress)

        # Check converter status
        
        status = self.conv.getLastStatus()
        
        #=======================================================================
        # Calibration Parameters
        #=======================================================================
        minCurrent = 0.0
        maxCurrent = 1.6
        
        num_operatingPoints = 8
        num_dataPoints = 3
        
        #=======================================================================
        # Test Variables
        #=======================================================================
        x = []
        y = []
        
        stepWidth = (maxCurrent - minCurrent) / num_operatingPoints
        steps = [minCurrent + stepWidth*pt for pt in range(num_operatingPoints+1)]
        sampleIndex = 0
        
        fmt = "| {0:7} | {1:16} | {2:16} | {3:16} |"
        self.logger.info("-"*68)
        self.logger.info(fmt.format('Sample', 'Operating Point', 'Multimeter', 'Converter'))
        self.logger.info("-"*68)

        for opPoint in steps:
            self.load.SetCCCurrent(opPoint)
            #self.conv.set_phaseAngle(self.convAddress, long(opPoint))
            time.sleep(2.0)
            
            for desired_x in range(num_dataPoints):
                _, _, _, dataPoint_m, _ = self.conv.getData(self.convAddress)
                sampleIndex += 1
                
                try:
                    dataPoint = self.pri_current.getMeasurement()
                except:
                    dataPoint = 0
                    
                if dataPoint_m == 0 or dataPoint == 0:
                    self.logger.info(fmt.format(sampleIndex, opPoint, "INVALID", "INVALID"))
                else:
                    self.logger.info(fmt.format(sampleIndex, opPoint, dataPoint, dataPoint_m))
                    x.append(dataPoint)
                    y.append(dataPoint_m)
                    
                time.sleep(0.25)
        
        self.logger.info("-"*68)
        
        self.logger.info("Running Linear Regression...")
        
        z = self.cal_linearRegression(x, y)
        
        self.logger.info("Gain: %f" % z[0])
        self.logger.info("Offset: %f" % z[1])
        
        # stop the power flow
        self.conv.set_phaseAngle(self.convAddress, 0x0000)
        self.conv.disableSwitching(self.convAddress)

        time.sleep(1.0)
        self.load.powerOff()

        self.conv.resetStatus(self.convAddress)
        
        return z
    
    def test_ClosedLoopRegulation(self):
        self.logger.info("--- TEST 4 / CLOSED LOOP REGULATION ---")
        #===============================================================================
        # Test 4 - Closed Loop Regulation
        #===============================================================================
        
        # Set instruments into known state
        self.sec_source.setVoltage(13.0)
        self.sec_source.powerOn()
        
        self.pri_source.setVoltage(3.6)
        self.pri_source.powerOn()
        
        self.load.powerOff()
        self.load.SetMode('cc') # Constant Voltage 
        self.load.SetCCCurrent(1.0)
        self.load.powerOn()
        
        time.sleep(1.0)
        
        # setup the converter again since power might have dropped out when the load was turned on
        self.conv.resetStatus(self.convAddress)
        self.conv.enableSampling(self.convAddress)
        self.conv.shutoff_wdt(self.convAddress)
        
        desiredSet = 14.5
        desiredSet_conv = 3332 #int(desiredSet * z1[0])# - int(z1[1])
        
        #self.conv.set_vRef(convAddress, desiredSet_conv)
        self.conv.enableSwitching_open(self.convAddress)
        
        # Allow converter to start switching
        time.sleep(2.0)

        self.conv.close_loop(self.convAddress)

        time.sleep(1.0)
        
        # Measure output voltage
        avg = 0
        vout = 0
        vout_avg = 0
        points = 10
        points_valid = points
        while (points > 0):
            try:	
                dataPoint = self.sec_voltage.getMeasurement()
                _, vout, _, _, status = self.conv.getData(self.convAddress)
                self.logger.info("    MM: %f", dataPoint)
                self.logger.info("    Conv: %i", vout)
                self.logger.debug("    Status: %s", str(status).encode('hex'))
                avg += dataPoint
                vout_avg += vout
                points -= 1
                time.sleep(0.2)
            
            except:
                self.logger.exception("Invalid data point, retrying")
                points -=1 # temporary to basically disable this as it will go on forever - need to think of a better way
                points_valid -= 1
        
        # setting converter back to open loop
        self.conv.disableSwitching(self.convAddress)

        time.sleep(1.0)
        self.load.powerOff()
        
        output = avg / points_valid
        vout_avg = vout_avg / points_valid
        self.logger.info("    MM AVG: [%f]", output)
        self.logger.info("    Conv AVG: [%f]", vout_avg)
        
        pct_error = (abs(output - desiredSet)/desiredSet) * 100.0
        self.logger.info("    PERCENT ERROR (MM): [%f]", pct_error)
        pct_error = (abs(vout_avg - desiredSet_conv)/desiredSet_conv) * 100.0
        self.logger.info("    PERCENT ERROR (Conv): [%f]", pct_error)

        return True
    
    def test_Efficiency(self):
        #===============================================================================
        # Test 5 - Efficiency
        #===============================================================================
        self.logger.info("--- TEST 5 / EFFICIENCY ---")
        
        # Set instruments into known state
        self.sec_source.setVoltage(13.0)
        self.sec_source.powerOn()
        
        self.pri_source.setVoltage(3.6)
        self.pri_source.powerOn()
        
        self.load.powerOff()
        self.load.SetMode('cc') # Constant Current 
        self.load.SetCCCurrent(1.0)
        self.load.powerOn()
        
        # setup the converter again since power might have dropped out when the load was turned on
        self.conv.resetStatus(self.convAddress)
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

        self.conv.disableSwitching(self.convAddress)

        time.sleep(1.0)
        self.load.powerOff()
        
        try:	
            output = avg / 5.0
        
            self.logger.info("    Avg Efficiency: %f", output)
        except:
            self.logger.exception("Efficiency Test Exception")

        return True
    
if __name__ == '__main__':
    test = t_AMPED()

