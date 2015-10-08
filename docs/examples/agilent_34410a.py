import labtronyx

# Enable debug logging
labtronyx.logConsole()

# Instantiate an InstrumentManager
im = labtronyx.InstrumentManager()

# Find the instrument by model number
dev_list = im.findInstruments(deviceVendor="Agilent", deviceModel="34410A")
dev = dev_list[0]

# Open the instrument
with dev:
    # Disable the front panel
    dev.disableFrontPanel()

    # Set the text on the front panel
    dev.frontPanelText("PRIMARY VOLT", "measuring...")

    # Set the mode to DC Voltage
    dev.setMode('DC Voltage')

    # Set the sample count to 10
    dev.setSampleCount(10)

    # Measure the input
    data = dev.getMeasurement()

    # Check for errors
    dev.checkForError()