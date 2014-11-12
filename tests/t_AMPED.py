import time
import struct
import serial

import numpy as np

def set_load(value):
    print "USER: SET LOAD TO CV %s V" % value
    test = raw_input("Press [ENTER] when completed...")

class t_AMPED(object):
    
    def open(self):
        conv_uuid = instr.findResource('localhost', 'COM3') # COM15 for the nice RS-485 converters
        instr.loadModel(conv_uuid, 'UPEL.AMPED.BMS', 'm_BMS')
        
        conv = instr.getInstrument(conv_uuid)
        
        #===============================================================================
        # Read data from CSV
        #===============================================================================
        import csv
        
        calibrationData = {}
        
        try:
            with open('calibrationData.csv', 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    try:
                        addr = int(row[0])
                        calibrationData[addr] = row[1:]
                    except:
                        print "Error while reading CSV row: %s" % row
        except:
            pass
                    
        print "---------- AMPED v2.2 Test Suite ----------"
        
        convAddress = input("What device address is being calibrated? ")
        
        from InstrumentControl import InstrumentControl
        
        instr = InstrumentControl()
        
        pri_voltage = instr.getInstrument_serial("123F12106")
        pri_current = instr.getInstrument_serial("343B12138")
        pri_source = instr.getInstrument_serial("602078010696820011")
        sec_voltage = instr.getInstrument_serial("123E12681")
        sec_current = instr.getInstrument_serial("123G11250")
        sec_source = instr.getInstrument_serial("00257")
        
        # Configuration
        pri_voltage.setFunction_DC_Voltage()
        pri_current.setFunction_DC_Current()
        sec_voltage.setFunction_DC_Voltage()
        sec_current.setFunction_DC_Current()
        
        conv.open()
        
        #pri_source.powerOff()
        pri_source.setVoltage(3.0)
        pri_source.setCurrent(10.0)
        #sec_source.powerOff()
        sec_source.setVoltage(12.0)
        sec_source.setCurrent(3.0)
        time.sleep(1.0)
        
        # Power on primary
        pri_source.powerOn()
        time.sleep(1.0)
        
        # Power on secondary
        print "Powering on..."
        sec_source.powerOn()
        time.sleep(2.0)
        
        # Initial setup of converter
        
        #convAddress = conv_identify()
        #print "Address received from module is 0x%02X" %convAddress
        
        conv_calibrate(convAddress)
        conv_enableSampling(convAddress)
        conv_shutoff_wdt(convAddress)
        
        test = raw_input("Press [ENTER] after ensuring board is programmed ...")
        test = raw_input("Press [ENTER] after ensuring load is turned OFF ...")
    
    def close(self):
        #===============================================================================
        # Closing everything
        #===============================================================================
        
        conv.close()
        # turn off so there's no voltage present when disconnecting/connecting modules
        conv_disable_switching(convAddress)
        
        time.sleep(1.0)
        
        pri_source.powerOff()
        sec_source.powerOff()
        
        test = raw_input("Press [ENTER] after turning the load off ...")
        test = raw_input("Press [ENTER] to exit...")
        
        #===============================================================================
        # Write data to CSV
        #===============================================================================
    
        print "Testing finished, writing data to file"
        
        calibrationData[convAddress] = list(z1) + list(z2) + list(z3)
        
        print calibrationData[convAddress]
        
        with open('calibrationData.csv', 'a') as f:
            writer = csv.writer(f)
            for addr, data in calibrationData.items():
                try:
                    writer.writerow([addr] + list(data))
                except:
                    print "Error writing data for [%s] to file: %s" % (addr, str(data))
    
    def test_SecVoltageCalibration(self):
        #===============================================================================
        # Test 1 - Secondary Voltage Calibration
        #===============================================================================
        print "---------- TEST 1 / SEC VOLTAGE CALIBRATION ----------"
        
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
        
        sec_source.setVoltage(startingVoltage)
        time.sleep(0.1)
        
        
        for opPoint in steps:
            sec_source.setVoltage(opPoint)
            print "   Operating Point: %f V" % opPoint
            time.sleep(3.0)
            vout_avg = 0
            dataPoint_avg = 0
            for desired_x in range(dataPointsPerPoint):
                _, vout, _, _, _ = conv_getData(convAddress)
                try:
                    dataPoint = sec_voltage.getMeasurement()
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
        sec_source.setVoltage(12.0)
    
    def test_PriVoltageCalibration(self):
        #===============================================================================
        # Test 2 - Primary Voltage Calibration
        #===============================================================================
        print "---------- TEST 2 / PRI VOLTAGE CALIBRATION ----------"
        
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
        
        pri_source.setVoltage(startingVoltage)
        
        time.sleep(0.1)
        
        for opPoint in steps:
            pri_source.setVoltage(opPoint)
            print "   Operating Point: %f V" % opPoint
            time.sleep(1.0)
            vout_avg = 0
            vin_avg = 0
            dataPoint_avg = 0
            for desired_x in range(dataPointsPerPoint):
                _, _, vin, _, _ = conv_getData(convAddress)
                try:
                    dataPoint = pri_voltage.getMeasurement()
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
        
        pri_source.setVoltage(3.5)
        sec_source.setVoltage(14.0)
        # Prompt user to set load to CV (13.5 volts)
        set_load(13.5)
        
        # setup the converter again since power might have dropped out when the load was turned on
        conv_resetStatus(convAddress)
        conv_calibrate(convAddress)
        conv_enableSampling(convAddress)
        conv_shutoff_wdt(convAddress)
        
        res = conv_enable_switching(convAddress)
        if (not res):
            print "Enabled switching failed, trying again"
            conv_enable_switching(convAddress)
        
        # Allow converter to start switching
        time.sleep(2.0)
        _, _, _, _, status = conv_getData(convAddress)
        
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
                    dataPoint = pri_current.getMeasurement()
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
        pri_source.setVoltage(3.85)
        sec_source.setVoltage(13.0) # below the closed loop regulation voltage
        
        # the following is a manual process by the user
        print "USER: SET LOAD TO CC 1.0 amps"
        test = raw_input("Press [ENTER] when completed...")
        
        # setup the converter again since power might have dropped out when the load was turned on
        conv_resetStatus(convAddress)
        time.sleep(0.2)
        conv_calibrate(convAddress)
        time.sleep(0.2)
        conv_enableSampling(convAddress)
        time.sleep(0.2)
        conv_shutoff_wdt(convAddress)
        
        desiredSet = 15.0
        desiredSet_conv = int(desiredSet * z1[0])# - int(z1[1])
        
        print "Setting CONV to [%i]" % desiredSet_conv
        time.sleep(0.2)
        conv_set_vref(convAddress,desiredSet_conv)
        time.sleep(0.2)
        conv_closed_loop(convAddress)
        time.sleep(0.2)
        res = conv_enable_switching(convAddress)
        if (not res):
            print "Enabled switching failed, trying again"
            conv_enable_switching(convAddress)
        
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
        		dataPoint = sec_voltage.getMeasurement()
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
        conv_set_to_openloop_mode(convAddress)
        
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
        
        avg = 0
        points = 5
        while (points > 0):
        	try:	
        		vin = pri_voltage.getMeasurement()		
        		vout = sec_voltage.getMeasurement()
        		iin = pri_current.getMeasurement()
        		iout = sec_current.getMeasurement()
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

