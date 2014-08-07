Models
======

Models are responsible for high-level communication with devices. They should
not make system driver calls. Models can send and recieve commands from the
device using a controller, but the physical communication protocol is
transparent to the model. For instruments that use the same command set but are
capable of communicating over a variety of protocols (Serial, Ethernet, CAN,
etc.), the same model can be used without needing knowledge of the underlying
controller.

 If a function returns an object that is not serializable, the function name
    must be prefixed with '_' in order to deny access to RPC clients who try to
    call that function. RPC servers can only serialize the following types:
    - str & unicode
    - int, long & float
    - bool
    - None
    - list & tuple
    - dict
    
        Models are responsible for managing resources properties. A
    request to getResources should return a serializable dictionary with these
    keys:
        - 'id': How the resource will be identified when a load call is made
        - 'uuid': A UUID string for reference only
        - 'controller': The module name for the controller
        - 'driver': The module name for the currently loaded model, None if not loaded
        - 'port': If RPC Server port, if it is running
        - 'deviceVendor': The device vendor
        - 'deviceModel': The device model number
        - 'deviceSerial': The device serial number
        - 'deviceFirmware': The device firmware revision
        - 'deviceType': The device type from the model