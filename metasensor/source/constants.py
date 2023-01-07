BASE_DIR = "/home/sergio/Documentos/uni/TFG/TFG-CA/metasensor/"
LOG_DIR = BASE_DIR + "logs/log/"
CSV_DIR = BASE_DIR + "logs/csv/"

ALREADY_EXISTS_ERR_MSG = "\nThere is already a CSV for this log file. Press W for overwriting it. Press any other key to exit and delete it, then rerun this script.\n"

SPLIT_INTERVAL_MS = 1000

START_OF_TIMESTAMP = 1
END_OF_TIMESTAMP = 14

RAW_COLUMN_NAMES = ("TIMESTAMP","ACCX","ACCY","ACCZ","GYRX","GYRY","GYRZ","MAGX","MAGY","MAGZ","UID")
COLUMN_NAMES = ("TIMESTAMP",
                "ACCX_MEAN","ACCY_MEAN","ACCZ_MEAN","GYRX_MEAN","GYRY_MEAN","GYRZ_MEAN","MAGX_MEAN","MAGY_MEAN","MAGZ_MEAN",
                "ACCX_STD","ACCY_STD","ACCZ_STD","GYRX_STD","GYRY_STD","GYRZ_STD","MAGX_STD","MAGY_STD","MAGZ_STD",
                "ACCX_MIN","ACCY_MIN","ACCZ_MIN","GYRX_MIN","GYRY_MIN","GYRZ_MIN","MAGX_MIN","MAGY_MIN","MAGZ_MIN",
                "ACCX_MEDIAN","ACCY_MEDIAN","ACCZ_MEDIAN","GYRX_MEDIAN","GYRY_MEDIAN","GYRZ_MEDIAN","MAGX_MEDIAN","MAGY_MEDIAN","MAGZ_MEDIAN",
                "ACCX_MAX","ACCY_MAX","ACCZ_MAX","GYRX_MAX","GYRY_MAX","GYRZ_MAX","MAGX_MAX","MAGY_MAX","MAGZ_MAX",
                "UID")