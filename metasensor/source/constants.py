MAGNITUDES = ("Acceleration", "Gyroscope", "Magnetic field", "Battery")
MAGNITUDES_ABBR = ("acc", "gyr", "mag", "bat")
TRI_AXIS_MAGS = ("acc", "gyr", "mag")

BASE_DIR = "/home/sergio/Documentos/uni/TFG/TFG-CA/metasensor/"
LOG_DIR = BASE_DIR + "logs/log/"
CSV_DIR = BASE_DIR + "logs/csv/"

ALREADY_EXISTS_ERR_MSG = "\nThere is already a CSV for this log file. Press W for overwriting it. Press any other key to exit.\n"
NOT_NUM_TIMESTAMP_ERR_MSG = "Unexpected error: non-numeric timestamp\nClosing file descriptors and exiting..."

SPLIT_INTERVAL_MS = 500

RAW_COLUMN_NAMES = ("TIMESTAMP","UID","ACCX","ACCY","ACCZ","GYRX","GYRY","GYRZ","MAGX","MAGY","MAGZ")
BASIC_CSV_HEADER = "TIMESTAMP,UID"
STATISTICS = ("MEAN", "STD", "MEDIAN", "MIN", "MAX")