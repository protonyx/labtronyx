import time
import struct
import serial

import numpy as np

from InstrumentControl import InstrumentControl

def set_load(value):
    print "USER: SET LOAD TO CV %s V" % value
    test = raw_input("Press [ENTER] when completed...")

class t_AMPED(object):
    
    calibrationData = {}
    
    def open(self):
        
        instr = InstrumentControl()
        
        self.pri_voltage = instr.getInstrument_serial("123F12106")
        self.pri_current = instr.getInstrument_serial("343B12138")
        self.pri_source = instr.getInstrument_serial("602078010696820011")
        self.sec_voltage = instr.getInstrument_serial("123E12681")
        self.sec_current = instr.getInstrument_serial("123G11250")
        self.sec_source = instr.getInstrument_serial("00257")
        
        conv_uuid = instr.findResource('localhost', 'COM3')[0] # COM15 for the nice RS-485 converters
        instr.loadModel(conv_uuid, 'models.UPEL.AMPED.BMS', 'm_BMS')
        self.conv = instr.getInstrument(conv_uuid)
        
        load_uuid = instr.findResource('localhost', 'COM4')[0]
        instr.loadModel(conv_uuid, 'models.BK_Precision.Load.m_85XX', 'm_85XX')
        self.load = instr.getInstrument(load_uuid)
        
        print "---------- AMPED v2.2 Test Suite ----------"
        
        self.convAddress = input("What device address is being calibrated? ")
        self.conv.setAddress = self.convAddress
        
        #===============================================================================
        # Read data from CSV
        #===============================================================================
        import csv
        
        try:
            with open('calibrationData.csv', 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    try:
                        addr = int(row[0])
                        self.calibrationData[addr] = row[1:]
                    except:
                        print "Error while reading CSV row: %s" % row
        except:
            pass

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
        print "Powering on..."
        self.sec_source.powerOn()
        time.sleep(2.0)
        
        # Initial setup of converter
        
        #convAddress = conv_identify()
        #print "Address received from module is 0x%02X" %convAddress
        
        self.conv.calibrate(1, 1)
        self.conv.enableSampling(convAddress)
        self.conv.shutoff_wdt(convAddress)
        
        test = raw_input("Press [ENTER] after ensuring board is programmed ...")
        test = raw_input("Press [ENTER] after ensuring load is turned OFF ...")
    
    def close(self):
        #===============================================================================
        # Closing everything
        #===============================================================================
        # turn off so there's no voltage present when disconnecting/connecting modules
        self.conv.disableSwitching(convAddress)
        
        time.sleep(1.0)
        
        self.pri_source.powerOff()
        self.sec_source.powerOff()
        
        test = raw_input("Press [ENTER] after turning the load off ...")
        test = raw_input("Press [ENTER] to exit...")
        
        #===============================================================================
        # Write data to CSV
        #===============================================================================
    
        print "Testing finished, writing data to file"
        
        with open('calibrationData.csv', 'a') as f:
            writer = csv.writer(f)
            for addr, data in self.calibrationData.items():
                try:
                    writer.writerow([addr] + list(data))
                except:
                    print "Error writing data for [%s] to file: %s" % (addr, str(data))
    
    def test_SecVoltageCalibration(self):
        #===============================================================================
        # Test 1 - Secondary Voltage Calibration
        #===============================================================================
        print "---------- TEST 1 / SEC VOLTAGE CALIBRATION ----------"
        
        # Set other instruments into known state
        self.load.powerOff()
        self.pri_source.powerOff()
        
        # Sec Voltage
        #  -Sweep operating points
        maxVoltage = 16.2
        startingVoltage = 13.5
        points = 6
        dataPointsPerPoint = 10
        x = []
        y = []
        vout_avg = 0
        dataPoint_avg = 0
        dataPointsPerPointValid = dataPointsPerPoint
        numFailures = 0
        
        stepWidth = (maxVoltage - startingVoltage) / points
        steps = [startingVoltage + stepWidth*pt for pt in range(points+1)]
        
        self.sec_source.setVoltage(startingVoltage)
        time.sleep(0.1)
        
        for opPoint in steps:
            self.sec_source.setVoltage(opPoint)
            print "   Operating Point: %f V" % opPoint
            time.sleep(3.0)
            vout_avg = 0
            dataPoint_avg = 0
            for desired_x in range(dataPointsPerPoint):
                _, vout, _, _, _ = conv_getData(convAddress)
                try:
                    dataPoint = self.sec_voltage.getMeasurement()
                except:
                    dataPoint = 0
                if vout == 0 or dataPoint == 0:
                    dataPointsPerPointValid -= 1
                    numFailures += 1
                else:
                    vout_avg += vout
                    dataPoint_avg += dataPoint
                print "    Multimeter: %f V" % dataPoint
                print "    Converter: %i (raw)" % vout
                time.sleep(0.25)
                
            if dataPointsPerPointValid > dataPointsPerPoint/2:
                vout_avg = vout_avg/dataPointsPerPointValid
                dataPoint_avg = dataPoint_avg/dataPointsPerPointValid
                x.append(vout_avg)
                y.append(dataPoint_avg)
            else:
                print "Bad Data. Reading not included at operating point: %f V" %opPoint
        
        x=np.array(x)
        y=np.array(y)
        z1 = np.polyfit(y, x, 1)
        
        print "  Gain: %f" % z1[0]
        print "  Offset: %f" % z1[1]
        print "Number of Failures: %f " %numFailures
        
        # Set Secondary Source to nominal 12.0 V
        self.sec_source.setVoltage(12.0)
    
    def test_PriVoltageCalibration(self):
        #===============================================================================
        # Test 2 - Primary Voltage Calibration
        #===============================================================================
        print "---------- TEST 2 / PRI VOLTAGE CALIBRATION ----------"
        
        # Set other instruments into known state
        self.load.powerOff()
        self.pri_source.powerOff()
        self.sec_source.setVoltage(12.0)
        
        # Pri Voltage
        #  -Sweep operating points
        maxVoltage = 4.2
        startingVoltage = 3.0
        ##points = 6 # to-do: set this to a higher value after testing the code
        ##dataPointsPerPoint = 5
        x = []
        y = []
        vout_avg = 0
        dataPoint_avg = 0
        dataPointsPerPointValid = dataPointsPerPoint
        numFailures = 0
        
        stepWidth = (maxVoltage - startingVoltage) / points
        steps = [startingVoltage + stepWidth*pt for pt in range(points+1)]
        
        self.pri_source.setVoltage(startingVoltage)
        
        time.sleep(0.1)
        
        for opPoint in steps:
            self.pri_source.setVoltage(opPoint)
            print "   Operating Point: %f V" % opPoint
            time.sleep(1.0)
            vout_avg = 0
            vin_avg = 0
            dataPoint_avg = 0
            for desired_x in range(dataPointsPerPoint):
                _, _, vin, _, _ = conv_getData(convAddress)
                try:
                    dataPoint = self.pri_voltage.getMeasurement()
                except:
                    dataPoint = 0
                if vin == 0 or dataPoint == 0:
                    dataPointsPerPointValid -= 1
                    numFailures += 1
                else:
                    vin_avg += vin
                    dataPoint_avg += dataPoint
                print "    Multimeter: %f V" % dataPoint
                print "    Converter: %i (raw)" % vin
                time.sleep(0.25)
                
            if dataPointsPerPointValid > dataPointsPerPoint/2:
                vin_avg = vin_avg/dataPointsPerPointValid
                dataPoint_avg = dataPoint_avg/dataPointsPerPointValid
                x.append(vin_avg)
                y.append(dataPoint_avg)
            else:
                print x
                print y
                print "Bad Data. Reading not included at operating point: %f V" %opPoint
        
        x=np.array(x)
        y=np.array(y)
        
        z2 = np.polyfit(y, x, 1)
        
        print "  Gain: %f" % z2[0]
        print "  Offset: %f" % z2[1]
        print "Number of Failures: %f " %numFailures
    
    
    def test_CurrentSensorCalibration(self):
        #===============================================================================
        # Test 3 - Current Sensor Calibration
        #===============================================================================
        print "---------- TEST 3 / CURRENT SENSOR CALIBRATION ----------"
        
        # Set other instruments into known state
        self.sec_source.setVoltage(14.0)
        self.sec_source.powerOn()
        
        self.pri_source.setVoltage(3.5)
        self.pri_source.powerOn()
        
        self.load.powerOff()
        self.load.SetMode('cv') # Constant Voltage 
        self.load.SetCVVoltage(13.5)
        self.load.powerOn()
        
        # setup the converter again since power might have dropped out when the load was turned on
        self.conv.resetStatus(convAddress)
        time.sleep(0.2)
        self.conv.calibrate(convAddress)
        time.sleep(0.2)
        self.conv.enableSampling(convAddress)
        time.sleep(0.2)
        self.conv.shutoff_wdt(convAddress)
        time.sleep(0.2)
        self.conv.enableSwitching(convAddress)
        
        # Allow converter to start switching
        time.sleep(2.0)
        
        _, _, _, _, status = self.conv.getData(convAddress)
        
        #  -Sweep operating points
        maxPhase = 1100 # absolute maximum is 1152 (75 ns)
        startingPhase = 0
        ##points = 8
        ##dataPointsPerPoint = 2
        x = []
        y = []
        iin_avg = 0
        dataPoint_avg = 0
        dataPointsPerPointValid = dataPointsPerPoint
        numFailures = 0
        
        stepWidth = (maxPhase - startingPhase) / points
        steps = [startingPhase + stepWidth*pt for pt in range(points+1)]
        
        for opPoint in steps:
            conv_set_phase_angle(convAddress, long(opPoint))
            print "   Operating Point: %i (phase units)" % opPoint
            time.sleep(0.75)
            iin_avg = 0
            dataPoint_avg = 0
            for desired_x in range(dataPointsPerPoint):
                _, _, _, iin, _ = conv_getData(convAddress)
                try:
                    dataPoint = self.pri_current.getMeasurement()
                except:
                    dataPoint = 0
                if iin == 0 or dataPoint == 0:
                    dataPointsPerPointValid -= 1
                    numFailures += 1
                else:
                    iin_avg += iin
                    dataPoint_avg += dataPoint
                print "    Multimeter: %f A" % dataPoint
                print "    Converter: %i (raw)" % iin
                time.sleep(0.25)
        
            # Consider the data valid if at least half the expected data points are okay    
            if dataPointsPerPointValid > dataPointsPerPoint/2:
                iin_avg = iin_avg/dataPointsPerPointValid
                dataPoint_avg = dataPoint_avg/dataPointsPerPointValid
                x.append(iin_avg)
                y.append(dataPoint_avg)
            else:
                print "Bad Data. Reading not included at operating point: %i" %opPoint
        
        try:
            x=np.array(x)
            y=np.array(y)
            z3 = np.polyfit(y, x, 1)
        except:
            z3 = np.array([0,0])
            
        print "  Gain: %f" % z3[0]
        print "  Offset: %f" % z3[1]
        print "Number of Failures: %f " %numFailures
        
        # stop the power flow
        conv_set_phase_angle(convAddress, 0x0000)
        conv_disable_switching(convAddress)
        _, _, _, _, status = conv_getData(convAddress)
    
    
    def test_ClosedLoopRegulation(self):
        #===============================================================================
        # Test 4 - Closed Loop Regulation
        #===============================================================================
        print "---------- TEST 4 / CLOSED LOOP REGULATION ----------"
        
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
        self.conv.resetStatus(convAddress)
        time.sleep(0.2)
        self.conv.calibrate(convAddress)
        time.sleep(0.2)
        self.conv.enableSampling(convAddress)
        time.sleep(0.2)
        self.conv.shutoff_wdt(convAddress)
        time.sleep(0.2)
        
        desiredSet = 15.0
        desiredSet_conv = int(desiredSet * z1[0])# - int(z1[1])
        
        print "Setting CONV to [%i]" % desiredSet_conv
        time.sleep(0.2)
        self.conv.set_vRef(convAddress, desiredSet_conv)
        time.sleep(0.2)
        self.conv.setMode_closedloop(convAddress)
        time.sleep(0.2)
        self.conv.enableSwitching(convAddress)
        
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
        		_, vout, _, _, _ = conv_getData(convAddress)
        		print "    MM: %f" % (dataPoint)
        		print "    Conv: %i" % (vout)
        		avg += dataPoint
        		vout_avg += vout
        		points -= 1
        		time.sleep(0.2)
        	except:
        		print "Invalid data point, retrying"
        		points -=1 # temporary to basically disable this as it will go on forever - need to think of a better way
        		points_valid -= 1
        		pass
        
        # setting converter back to open loop
        self.conv.setMode_openloop(convAddress)
        
        output = avg / points_valid
        vout_avg = vout_avg / points_valid
        print "    MM AVG: [%f]" % output
        print "    Conv AVG: [%f]" % vout_avg
        
        pct_error = (abs(output - desiredSet)/desiredSet) * 100.0
        print "    PERCENT ERROR (MM): [%f]" % pct_error
        pct_error = (abs(vout_avg - desiredSet_conv)/desiredSet_conv) * 100.0
        print "    PERCENT ERROR (Conv): [%f]" % pct_error
    
    def test_Efficiency(self):
        #===============================================================================
        # Test 5 - Efficiency
        #===============================================================================
        print "---------- TEST 5 / EFFICIENCY ----------"
        
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
        self.conv.resetStatus(convAddress)
        time.sleep(0.2)
        self.conv.calibrate(convAddress)
        time.sleep(0.2)
        self.conv.enableSampling(convAddress)
        time.sleep(0.2)
        self.conv.shutoff_wdt(convAddress)
        time.sleep(0.2)
        self.conv.enableSwitching(convAddress)
        
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
        		print "    Efficiency: %f" % (dataPoint)
        		avg += dataPoint
        		points -= 1
        		time.sleep(0.2)
        	except Exception as e:
        		print "Invalid data point, retrying"
        		print e.message
        		points -=1 # basically disable this as it will go on forever - need to think of a better way
        
        try:	
            output = avg / 5.0
        
            print "    Avg Efficiency: %f" % output
        except:
            print "Efficiency Test Error"
    
if __name__ == '__main__':
    test = t_AMPED()
    test.open()
    
    test.close()

