# What is Metawear?

Metawear is a sensor device which can measure the following magnitudes: magnetic field, acceleration, rotation speed, light intensity (and others). It transfers the measured data to a Bluetooth device, such as a laptop. In addition to raw sensor data, it is able to perform computations in order to provide absolute orientation or act like a compass, among others, based on its own data.

# How to interact with a Metawear

## The Metawear class

This class is provided by de Python Metawear SDK and is the core of the interaction. It is instantiated by passing the MAC address of the device. Then, call the connect() method, which is a handy wrapper of some underlying C++ SDK calls:

``` python
device = Metawear("AA:BB:CC:DD:EE:FF")
device.connect()
print("Connected to " + d.address + " over " + ("USB" if d.usb.is_connected else "BLE"))
```

On success, we will be able to retrieve information relative to the connection and the Metawear will be listening for commands. On error, the underlying C++ SDK will abort the program.

## The State class

This abstract class groups in a single entity the interactions we will be having with the device. It receives de Metawear instance previously created and an optional file descriptor to log data. It also defines a callback to be used by children classes