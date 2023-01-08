from datetime import datetime
import sys
import time
import tkinter as tk
import traceback

from mbientlab.metawear import MetaWear, libmetawear, parse_value, cbindings
import constants as CTS


class State:
    # init
    def __init__(self, device, gyr=True, acc=True, mag=True, log=None):
        self.device = device
        self.cb_acc = cbindings.FnVoid_VoidP_DataP(self.data_handler_acc)
        self.cb_gyr = cbindings.FnVoid_VoidP_DataP(self.data_handler_gyr)
        self.cb_mag = cbindings.FnVoid_VoidP_DataP(self.data_handler_mag)
        self.read_gyr = gyr
        self.read_acc = acc
        self.read_mag = mag
        self.logfile = log


    # HANDLERS - what to do with sensor generated data
    def data_handler_acc(self, ctx, data):
        values = parse_value(data)
        # print axis values and milliseconds since epoch
        print("[%d] acc: (%.4f,%.4f,%.4f)" % (data.contents.epoch, values.x, values.y, values.z), file=self.logfile)

    def data_handler_gyr(self, ctx, data):
        values = parse_value(data)
        print("[%d] gyr: (%.4f,%.4f,%.4f)" % (data.contents.epoch, values.x, values.y, values.z), file=self.logfile)

    def data_handler_mag(self, ctx, data):
        values = parse_value(data)
        print("[%d] mag: (%.4f,%.4f,%.4f)" % (data.contents.epoch, values.x, values.y, values.z), file=self.logfile)


    # SETUP ROUTINES - setup sensors and subscribe
    def setup(self):
        # ble settings
        libmetawear.mbl_mw_settings_set_connection_parameters(self.device.board, 7.5, 7.5, 0, 6000)
        time.sleep(1.5)
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

    def disconnect(self):
        libmetawear.mbl_mw_debug_disconnect(self.device.board)


def set_user_id():
    """ Function to set a 3-character-long-alphanumeric ID """
    user = ""
    while len(user) not in range(1,4) or not user.isalnum():
        user = input("Current user ID (1 to 3 characters): ")
    return user.zfill(3)

def set_measure_time():
    time = input("Measure time in seconds (default 600): ")
    return int(time) if time.isdigit() else 600

def set_measure_magnitudes():
    """ Prompt the user to select the magnitudes to measure """
    window = tk.Tk()
    window.title("Magnitudes to measure")
    window.geometry("300x300")

    # define one variable for each measurable magnitude
    vars = [tk.BooleanVar(value=True) for _ in range(len(CTS.MAGNITUDES))]
    # battery measurement is off by default
    vars[-1].set(False)

    def close_window():
        window.destroy()

    # display checkbuttons for each magnitude
    for i in range(len(CTS.MAGNITUDES)):
        tk.Checkbutton(window, 
                        text=CTS.MAGNITUDES[i],
                        variable=vars[i],
                        justify="left").pack(side=tk.TOP, anchor=tk.W)

    tk.Button(window, 
                text="Go!", 
                command=close_window).pack(side=tk.TOP, anchor=tk.W)
    
    window.mainloop()
    
    # merge the abbreviated names of the magnitudes with the decisions of the user
    return dict(zip(
            CTS.MAGNITUDES_ABBR, 
            [v.get() for v in vars]
        ))


if __name__ == "__main__":

    user = set_user_id()
    measure_time = set_measure_time()
    params = set_measure_magnitudes()
    
    create_log = False
    header = ""
    logfile = None
    state = None

    # instantiate a Metawear object and set a callback for disconnection event
    d = MetaWear("EE:A0:EE:0F:CC:3E")
    d.on_disconnect = lambda status: print("disconnecting, " + str(status))
    try:
        d.connect()
    except:
        print("Exception during connection")
        traceback.print_exc()
        quit()
    
    print("Connected to " + d.address + " over " + ("USB" if d.usb.is_connected else "BLE"))

    # fill header with the magnitudes the user wants to measure
    for magnitude in CTS.MAGNITUDES_ABBR:
        if params[magnitude]:
            create_log = True
            header += magnitude + ","

    if create_log:
        header += user
        logfile = open(CTS.LOG_DIR + "{}_{}.log".format(user, datetime.now().strftime("%Y%m%d_%H%M%S")), "w")
        # log file header: /(magnitude,)+UID\n/
        print(header, file=logfile)

    try:
        state = State(d, acc=params["acc"], gyr=params["gyr"], mag=params["mag"], log=logfile)

        print("setup...")
        state.setup()

        print("start...")
        state.start()

        # working animation
        for i in range(measure_time):
            sys.stdout.write(" [")
            sys.stdout.write(" " * (i % 5))
            sys.stdout.write("*")
            sys.stdout.write(" " * (4 - (i % 5)))
            sys.stdout.write("] {} s".format(i))
            sys.stdout.write("\b" * 15)
            sys.stdout.flush()
            time.sleep(1)

        print("stop..." + " " * 15)
        state.stop()
        state.disconnect()

    except Exception as e:
        print("Error! Stopping and disconnecting...")
        if state:
            state.stop()
            state.disconnect()
        traceback.print_exc()

    finally:
        if logfile:
            print("Closing file...")
            logfile.close()
        d.disconnect()
