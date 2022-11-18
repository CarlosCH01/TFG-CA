from time import sleep
from threading import Event
from mbientlab.metawear import MetaWear, libmetawear, parse_value, cbindings


class State:
    # init
    def __init__(self, device):
        self.device = device
        self.callback = cbindings.FnVoid_VoidP_DataP(self.data_handler)
        self.processor = None
        self.magnitude1 = cbindings.SensorFusionData.CORRECTED_GYRO

    # what to do with sensor generated data
    def data_handler(self, ctx, data):
        values = parse_value(data, n_elem = 3)
        print("gyro; (%.4f,%.4f,%.4f), acc: (%.4f,%.4f,%.4f), mag: (%.4f,%.4f,%.4f)" % \
            (values[0].x, values[0].y, values[0].z, values[1].x, values[1].y, values[1].z, values[2].x, values[2].y, values[2].z))

    def setup(self):
        # ble settings
        libmetawear.mbl_mw_settings_set_connection_parameters(self.device.board, 7.5, 7.5, 0, 6000)
        sleep(1.5)

        ########
        # events
        e = Event()
        # processor callback fxn
        def processor_created(context, pointer):
            self.processor = pointer
            e.set()
        # processor fxn ptr
        fn_wrapper = cbindings.FnVoid_VoidP_VoidP(processor_created)
        ########

        # set sensor fusion mode
        libmetawear.mbl_mw_sensor_fusion_set_mode(self.device.board, cbindings.SensorFusionMode.NDOF)
        libmetawear.mbl_mw_sensor_fusion_set_acc_range(self.device.board, cbindings.SensorFusionAccRange._4G)
        libmetawear.mbl_mw_sensor_fusion_set_gyro_range(self.device.board, cbindings.SensorFusionGyroRange._2000DPS)
        libmetawear.mbl_mw_sensor_fusion_write_config(self.device.board)

        signal1 = libmetawear.mbl_mw_sensor_fusion_get_data_signal(self.device.board, self.magnitude1)
        signal_acc = libmetawear.mbl_mw_sensor_fusion_get_data_signal(self.device.board, cbindings.SensorFusionData.CORRECTED_ACC)
        signal_mag = libmetawear.mbl_mw_sensor_fusion_get_data_signal(self.device.board, cbindings.SensorFusionData.CORRECTED_MAG)

        signals = (cbindings.c_void_p * 1)()
        signals[0] = signal1
        libmetawear.mbl_mw_dataprocessor_fuser_create(signal_acc, signals, 1, None, fn_wrapper)
        # wait for fuser to be created
        e.wait()
        libmetawear.mbl_mw_dataprocessor_fuser_create(signal_mag, signals, 2, None, fn_wrapper)
        # wait for fuser to be created
        e.wait()

        #libmetawear.mbl_mw_datasignal_subscribe(signal1, None, self.callback)
        libmetawear.mbl_mw_datasignal_subscribe(self.processor, None, self.callback)

    def start(self):
        libmetawear.mbl_mw_sensor_fusion_enable_data(self.device.board, self.magnitude1)
        libmetawear.mbl_mw_sensor_fusion_enable_data(self.device.board, cbindings.SensorFusionData.CORRECTED_ACC)
        libmetawear.mbl_mw_sensor_fusion_enable_data(self.device.board, cbindings.SensorFusionData.CORRECTED_MAG)
        print("error gordo, ¿qué pasa?")
        libmetawear.mbl_mw_sensor_fusion_start(self.device.board)

    def stop(self):
        libmetawear.mbl_mw_sensor_fusion_stop(self.device.board)

        signal1 = libmetawear.mbl_mw_sensor_fusion_get_data_signal(self.device.board, self.magnitude1)
        libmetawear.mbl_mw_datasignal_unsubscribe(signal1)
        signal2 = libmetawear.mbl_mw_sensor_fusion_get_data_signal(self.device.board,cbindings.SensorFusionData.CORRECTED_ACC)
        libmetawear.mbl_mw_datasignal_unsubscribe(signal2)
        signal3 = libmetawear.mbl_mw_sensor_fusion_get_data_signal(self.device.board, cbindings.SensorFusionData.CORRECTED_MAG)
        libmetawear.mbl_mw_datasignal_unsubscribe(signal3)
        libmetawear.mbl_mw_debug_disconnect(self.device.board)

if __name__ == "__main__":
    d = MetaWear("EE:A0:EE:0F:CC:3E")
    d.connect()
    print("Connected to " + d.address + " over " + ("USB" if d.usb.is_connected else "BLE"))
    state = State(d)
    print("setup...")
    state.setup()
    print("start")
    state.start()
    sleep(5)
    print("stop...")
    state.stop()
