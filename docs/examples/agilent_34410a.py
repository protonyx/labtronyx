import labtronyx

# Enable debug logging
labtronyx.logConsole()

# Instantiate an InstrumentManager
im = labtronyx.InstrumentManager(rpc=False)

# Find the instrument by model number
dev_list = im.findInstruments(deviceModel="34410A")
dev = dev_list[0]

# Open the instrument
dev.open()

print(dev.getProperties())

print(dev.getMode())