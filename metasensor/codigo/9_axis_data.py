from time import sleep
import traceback
from mbientlab.metawear import MetaWear, libmetawear, parse_value, cbindings


class State:
    # init
    def __init__(self, device, gyro=True, acc=True, mag=True, log=None):
        self.device = device
        self.cb_acc = cbindings.FnVoid_VoidP_DataP(self.data_handler_acc)
        self.cb_gyr = cbindings.FnVoid_VoidP_DataP(self.data_handler_gyr)
        self.cb_mag = cbindings.FnVoid_VoidP_DataP(self.data_handler_mag)
        self.read_gyr = gyro
        self.read_acc = acc
        self.read_mag = mag
        self.logfile = log


    # HANDLERS - what to do with sensor generated data
    def data_handler_acc(self, ctx, data):
        values = parse_value(data)
        # print axis values and hundreths of second since epoch
        print("[%d] acc: (%.4f,%.4f,%.4f)" % (data.contents.epoch // 10, values.x, values.y, values.z), file=self.logfile)

    def data_handler_gyr(self, ctx, data):
        values = parse_value(data)
        print("[%d] gyr: (%.4f,%.4f,%.4f)" % (data.contents.epoch // 10, values.x, values.y, values.z), file=self.logfile)

    def data_handler_mag(self, ctx, data):
        values = parse_value(data)
        print("[%d] mag: (%.4f,%.4f,%.4f)" % (data.contents.epoch // 10, values.x, values.y, values.z), file=self.logfile)


    # SETUP ROUTINES - setup sensors and subscribe
    def setup(self):
        # ble settings
        libmetawear.mbl_mw_settings_set_connection_parameters(self.device.board, 7.5, 7.5, 0, 6000)
        sleep(1.5)
        if self.read_acc: self._setup_acc()
        if self.read_gyr: self._setup_gyr()
        if self.read_mag: self._setup_mag()

    def _setup_acc(self):
        # get acc signal
        acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.device.board)
        # subscribe to accelerometer
        libmetawear.mbl_mw_datasignal_subscribe(acc, None, self.cb_acc)

    def _setup_gyr(self):
        # get gyro signal - MMRS ONLY
        gyr = libmetawear.mbl_mw_gyro_bmi270_get_rotation_data_signal(self.device.board)
        # subscribe to gyroscope
        libmetawear.mbl_mw_datasignal_subscribe(gyr, None, self.cb_gyr)

    def _setup_mag(self):
        # setup mag
        libmetawear.mbl_mw_mag_bmm150_stop(self.device.board)
        libmetawear.mbl_mw_mag_bmm150_set_preset(self.device.board, cbindings.MagBmm150Preset.REGULAR)
        # get mag signal
        mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(self.device.board)
        # subscribe to magnetometer
        libmetawear.mbl_mw_datasignal_subscribe(mag, None, self.cb_mag)


    # START ROUTINES - start sensors
    def start(self):
        if self.read_gyr: self._start_gyr()
        if self.read_acc: self._start_acc()
        if self.read_mag: self._start_mag()

    def _start_acc(self):
        # start acc sampling
        libmetawear.mbl_mw_acc_enable_acceleration_sampling(self.device.board)
        # start acc
        libmetawear.mbl_mw_acc_start(self.device.board)

    def _start_gyr(self):
        # start gyro sampling - MMS ONLY
        libmetawear.mbl_mw_gyro_bmi270_enable_rotation_sampling(self.device.board)
        # start gyro
        libmetawear.mbl_mw_gyro_bmi270_start(self.device.board)

    def _start_mag(self):
        # start mag sampling
        libmetawear.mbl_mw_mag_bmm150_enable_b_field_sampling(self.device.board)
        # start mag
        libmetawear.mbl_mw_mag_bmm150_start(self.device.board)


    # STOP ROUTINES - stop sensors and unsubscribe
    def stop(self):
        if self.read_gyr: self._stop_gyr()
        if self.read_acc: self._stop_acc()
        if self.read_mag: self._stop_mag()
        libmetawear.mbl_mw_debug_disconnect(self.device.board)

    def _stop_acc(self): 
        # stop acceleration sampling
        libmetawear.mbl_mw_acc_stop(self.device.board)
        libmetawear.mbl_mw_acc_disable_acceleration_sampling(self.device.board)
        # unsubscribe to accelerometer
        acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.device.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(acc)
    
    def _stop_gyr(self): 
        # stop gyroscope sampling
        libmetawear.mbl_mw_gyro_bmi270_stop(self.device.board)
        libmetawear.mbl_mw_gyro_bmi270_disable_rotation_sampling(self.device.board)
        # unsubscribe to gyroscope
        gyro = libmetawear.mbl_mw_gyro_bmi270_get_rotation_data_signal(self.device.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(gyro)

    def _stop_mag(self): 
        # stop magnetometer sampling
        libmetawear.mbl_mw_mag_bmm150_stop(self.device.board)
        libmetawear.mbl_mw_mag_bmm150_disable_b_field_sampling(self.device.board)
        # unsubscribe to magnetometer
        mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(self.device.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(mag)


def set_user_id():
    # force a 3-character long ID
    user = "...."
    while len(user) not in range(1,4):
        user = input("Current user ID: ")
    return user.zfill(3)

if __name__ == "__main__":
    d = MetaWear("EE:A0:EE:0F:CC:3E")
    d.connect()
    print("Connected to " + d.address + " over " + ("USB" if d.usb.is_connected else "BLE"))

    logfile = open("../logs/sensor_log.log", "w")

    # log file header: UID padded with zeroes to the left until three digits + \n
    logfile.write(set_user_id())
    logfile.write("\n")
    
    try:
        state = State(d, log=logfile)

        print("setup...")
        state.setup()

        print("start...")
        state.start()

        sleep(60)

        print("stop...")
        state.stop()

    except Exception as e:
        state.stop()
        traceback.print_exc()

    finally:
        print("[999999999999]", file=logfile)
        logfile.close()
