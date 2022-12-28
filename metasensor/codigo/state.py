import time

from mbientlab.metawear import libmetawear, parse_value, cbindings

class State:
    # init
    def __init__(self, device, log=None):
        self.device = device
        self.logfile = log
        self.callback = cbindings.FnVoid_VoidP_DataP(self.data_handler)

    # HANDLER - what to do with sensor generated data
    def data_handler(self, ctx, data):
        values = parse_value(data)
        # print axis values and milliseconds since epoch
        print("[%d] acc: (%.4f,%.4f,%.4f)" % (data.contents.epoch, values.x, values.y, values.z), file=self.logfile)

    # SETUP ROUTINE - setup sensors and subscribe
    def setup(self):
        # ble settings
        libmetawear.mbl_mw_settings_set_connection_parameters(self.device.board, 7.5, 7.5, 0, 6000)
        time.sleep(1.5)
        pass

    # START ROUTINE - start sensors
    def start(self):
        pass

    # STOP ROUTINE - stop sensors and unsubscribe
    def stop(self):
        pass

    def disconnect(self):
        libmetawear.mbl_mw_debug_disconnect(self.device.board)