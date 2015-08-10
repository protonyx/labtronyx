import labtronyx

import time
# Enable debug logging
labtronyx.logConsole()

# Instantiate an InstrumentManager
im = labtronyx.InstrumentManager(rpc=False)

# Find the instrument by model number
dev_list = im.findInstruments(deviceModel="34410A")
dev = dev_list[0]

# Open the instrument
with dev:

    dev.disableFrontPanel()

    dev.frontPanelText("PRIMARY VOLT", "measuring...")

    dev.setMode('DC Voltage')

    dev.setSampleCount(10)

    data = dev.getMeasurement()

    dev.checkForError()