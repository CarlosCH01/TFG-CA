from time import sleep
from threading import Event
from mbientlab.metawear import MetaWear, libmetawear, parse_value, cbindings


class State:
    # init
    def __init__(self, device):
        self.device = device
        self.cb_acc = cbindings.FnVoid_VoidP_DataP(self.data_handler_acc)
        self.cb_gyr = cbindings.FnVoid_VoidP_DataP(self.data_handler_gyr)
        self.cb_mag = cbindings.FnVoid_VoidP_DataP(self.data_handler_mag)
        self.cb_read_config = cbindings.FnVoid_VoidP_VoidP_Int(self.read_config)
        self.processor = None

    # what to do with sensor generated data
    def data_handler_acc(self, ctx, data):
        #print(data.contents.epoch)
        values = parse_value(data)
        print("acc: (%.4f,%.4f,%.4f)" % (values.x, values.y, values.z))

    def data_handler_gyr(self, ctx, data):
        values = parse_value(data)
        print("gyr: (%.4f,%.4f,%.4f)" % (values.x, values.y, values.z))

    def data_handler_mag(self, ctx, data):
        values = parse_value(data)
        print("mag: (%.4f,%.4f,%.4f)" % (values.x, values.y, values.z))

    def read_config(self, ctx, board, data):
        print("gyro output data rate: " + parse_value(data))

    def setup(self):
        # ble settings
        libmetawear.mbl_mw_settings_set_connection_parameters(self.device.board, 7.5, 7.5, 0, 6000)
        sleep(1.5)

        # setup mag
        libmetawear.mbl_mw_mag_bmm150_stop(self.device.board)
        libmetawear.mbl_mw_mag_bmm150_set_preset(self.device.board, cbindings.MagBmm150Preset.REGULAR)

        # get acc signal
        acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.device.board)
        # get gyro signal - MMRS ONLY
        gyr = libmetawear.mbl_mw_gyro_bmi270_get_rotation_data_signal(self.device.board)
        # get mag signal
        mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(self.device.board)

        libmetawear.mbl_mw_datasignal_subscribe(acc, None, self.cb_acc)
        libmetawear.mbl_mw_datasignal_subscribe(gyr, None, self.cb_gyr)
        libmetawear.mbl_mw_datasignal_subscribe(mag, None, self.cb_mag)

    def start(self):
        # start gyro sampling - MMS ONLY
        libmetawear.mbl_mw_gyro_bmi270_enable_rotation_sampling(self.device.board)
        # start acc sampling
        libmetawear.mbl_mw_acc_enable_acceleration_sampling(self.device.board)
        # start mag sampling
        libmetawear.mbl_mw_mag_bmm150_enable_b_field_sampling(self.device.board)
        # start gyro
        libmetawear.mbl_mw_gyro_bmi270_start(self.device.board)
        # start acc
        libmetawear.mbl_mw_acc_start(self.device.board)
        # start mag
        libmetawear.mbl_mw_mag_bmm150_start(self.device.board)

    def stop(self):
        # stop gyroscope sampling
        libmetawear.mbl_mw_gyro_bmi270_stop(self.device.board)
        libmetawear.mbl_mw_gyro_bmi270_disable_rotation_sampling(self.device.board)

        # stop acceleration sampling
        libmetawear.mbl_mw_acc_stop(self.device.board)
        libmetawear.mbl_mw_acc_disable_acceleration_sampling(self.device.board)

        # stop magnetometer sampling
        libmetawear.mbl_mw_mag_bmm150_stop(self.device.board)
        libmetawear.mbl_mw_mag_bmm150_disable_b_field_sampling(self.device.board)

        acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.device.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(acc)

        gyro = libmetawear.mbl_mw_gyro_bmi270_get_rotation_data_signal(self.device.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(gyro)

        mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(self.device.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(mag)

        libmetawear.mbl_mw_debug_disconnect(self.device.board)

    def read_config(self, sensor):
        if sensor == "gyr":
            libmetawear.mbl_mw_gyro_bmi270_read_config(self.device.board, None, self.cb_read_config)


if __name__ == "__main__":
    d = MetaWear("EE:A0:EE:0F:CC:3E")
    d.connect()
    print("Connected to " + d.address + " over " + ("USB" if d.usb.is_connected else "BLE"))
    state = State(d)
    print("setup...")
    state.setup()
    print("start")
    state.start()
    sleep(1)
    print("stop...")
    state.stop()
