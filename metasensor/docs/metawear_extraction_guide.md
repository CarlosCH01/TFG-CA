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

This class groups in a single entity all the interactions we will be having with the device. It receives de Metawear instance previously created, an optional file descriptor to log data to and several flags for each type of supported sensor, all defaulted to false. On instantiation, it defines internal callbacks to be used when logging data.

### Connection handlers

When streaming data, we have to provide a callback function to the framework, in which we define what to do with incoming data. In this case, all sensors will write the 3 axis readings as well as the timestamp to the provided log file:

```python
def data_handler_XXX(self, ctx, data):
    values = parse_value(data)
    print("[%d] XXX: (%.4f,%.4f,%.4f)" % (data.contents.epoch, 
                                values.x, values.y, values.z),
            file=self.logfile)
```

### Connection setup

Without regarding the type of data to be measured, the `setup()` method sets the connection parameters with the recommended values. Then, we can set up each sensor connection by subscribing to it:

``` python
def _setup_XXX(self):
    # get signal
    signal = libmetawear.mbl_mw_XXX_get_YYY_data_signal(self.device.board)
    # subscribe to sensor
    libmetawear.mbl_mw_datasignal_subscribe(signal, None, self.callback_XXX)
```

### Start streaming

Activating the sensors is as easy as enabling sampling and starting them up:
``` python
def _start_XXX(self):
    # start sampling
    libmetawear.mbl_mw_XXX_enable_YYY_sampling(self.device.board)
    # start sensor
    libmetawear.mbl_mw_XXX_start(self.device.board)
```

### Stop streaming

When we collected all data needed, cancel the connection stopping the sensor, disabling sampling and, finally, unsubscribing to the sensor:
``` python
    def _stop_XXX(self): 
        # stop sampling
        libmetawear.mbl_mw_XXX_stop(self.device.board)
        libmetawear.mbl_mw_XXX_disable_YYY_sampling(self.device.board)
        # unsubscribe
        signal = libmetawear.mbl_mw_XXX_get_YYY_data_signal(self.device.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(signal)
```

### Closing connection

`libmetawear.mbl_mw_debug_disconnect(self.device.board)` will flush the current configuration, thus allowing a clean setup next time.