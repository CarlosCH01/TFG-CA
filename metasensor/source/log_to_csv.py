import numpy as np
import os
import pandas as pd
import re
import sys

import constants as CTS

class Buffer:
    """ Implementation of a buffer to convert from log to csv format """
    def __init__(self, uid):
        self.uid = uid
        self.buffer = {"timestamp": 0,
                       "accx": np.nan, "accy": np.nan, "accz": np.nan,
                       "gyrx": np.nan, "gyry": np.nan, "gyrz": np.nan, 
                       "magx": np.nan, "magy": np.nan, "magz": np.nan }

    def isEmpty(self, magnitude=None):
        if magnitude is None:
            return self.buffer["timestamp"] == 0
            
        if magnitude in ("acc","gyr","mag"):
            # metawear sends these magnitudes in packets of 3. So, if
            # x coordinate exists, the rest are assumed to exist
            return np.isnan(self.buffer[magnitude + "x"])
        else:
            return np.isnan(self.buffer[magnitude])

    def flush(self):
        for k in self.buffer.keys(): 
            self.buffer[k] = np.nan

    def update(self, info):
        """ 
        Updates the buffer with new info from the log file
        Format of this info: [timestamp in millisecs] magnitude: (X,Y,Z) | N
        """
        magnitude   = info[ info.find("]") + 2 : info.find(":") ]
        new_content = info[ info.find("(") + 1 : info.find(")") ].split(",")

        self.buffer["timestamp"] = int(info[ info.find("[") + 1 : info.find("]") ])

        if self.isEmpty(magnitude):
            # data can be one single value or a 3-dimensional vector
            if len(new_content) == 3:
                self.buffer[magnitude + "x"] = float(new_content[0])
                self.buffer[magnitude + "y"] = float(new_content[1])
                self.buffer[magnitude + "z"] = float(new_content[2])
            else:
                self.buffer[magnitude] = float(new_content)
        else:
            # compute the mean of the current value and the new one
            if len(new_content) == 3:
                for i, coord in enumerate(("x","y","z")):
                    self.buffer[magnitude + coord] = (self.buffer[magnitude + coord] + float(new_content[i]))/2
            else:
                self.buffer[magnitude] = (self.buffer[magnitude] + float(new_content))/2

    def toCSV(self):
        return "{},{},{},{},{},{},{},{},{},{},{}\n"\
                    .format(self.buffer["timestamp"],
                            self.buffer["accx"], self.buffer["accy"], self.buffer["accz"], \
                            self.buffer["gyrx"], self.buffer["gyry"], self.buffer["gyrz"], \
                            self.buffer["magx"], self.buffer["magy"], self.buffer["magz"],
                            self.uid)

    def toDataFrame(self):
        res = pd.DataFrame([self.buffer["timestamp"], 
                             self.buffer["accx"], self.buffer["accy"], self.buffer["accz"], 
                             self.buffer["gyrx"], self.buffer["gyry"], self.buffer["gyrz"], 
                             self.buffer["magx"], self.buffer["magy"], self.buffer["magz"],
                             self.uid],
                             columns=["TIMESTAMP","ACCX","ACCY","ACCZ","GYRX","GYRY","GYRZ","MAGX","MAGY","MAGZ","UID"])
        res.set_index("TIMESTAMP", inplace=True)
        return res

    def toList(self):
        return [self.buffer["timestamp"], 
                self.buffer["accx"], self.buffer["accy"], self.buffer["accz"], 
                self.buffer["gyrx"], self.buffer["gyry"], self.buffer["gyrz"], 
                self.buffer["magx"], self.buffer["magy"], self.buffer["magz"],
                self.uid]

    def __getitem__(self, key):
        return self.buffer[key]

    def __setitem__(self, key, item):
        self.buffer[key] = item

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return self.toCSV()


def set_file_origin():
    """ Returns the name of the log file to convert """
    files = os.listdir(CTS.LOG_DIR)
    for i, f in enumerate(files):
        print(i+1, f)

    logfile_index = ""
    while not logfile_index.isdigit() or int(logfile_index) - 1 not in range(len(files)):
        logfile_index = input("Select a file from the list: ")

    return files[int(logfile_index) - 1]

def get_id_reference(fd):
    # log file header: UID padded with zeroes to the left until three digits + \n
    # pick only the UID (not newline) and discard padding zeroes
    line = fd.readline()
    uid = line[:3].lstrip("0")
    # store current position
    p = fd.tell()
    # set the first timestamp as a reference
    reference = int(fd.readline()[CTS.START_OF_TIMESTAMP:CTS.END_OF_TIMESTAMP])
    # return to the start of the first log line
    fd.seek(p)

    return uid, reference

def compute_statistics(base_csv_name, column_names, chunk):

    data_aggregator = pd.DataFrame(chunk, columns=column_names).drop(["TIMESTAMP","UID"], axis=1)

    stats = data_aggregator.mean(numeric_only=True).to_list()
    stats.extend(data_aggregator.std(numeric_only=True).to_list())
    stats.extend(data_aggregator.min(numeric_only=True).to_list())
    stats.extend(data_aggregator.median(numeric_only=True).to_list())
    stats.extend(data_aggregator.max(numeric_only=True).to_list())
    
    # remove square brackets and spaces from the string representation of a list
    stats = re.sub("\[|\]|\s", "", str(stats))
    
    with open(base_csv_name, "a") as csv_file:
        # write down first timestamp and the UID for reference and the statistics
        print(f"{chunk[0][0]},{stats},{chunk[0][-1]}", file=csv_file)


if __name__ == "__main__":
    file_origin = set_file_origin()
    logfile_size = os.stat(CTS.LOG_DIR + file_origin).st_size
    base_csv_name = CTS.CSV_DIR + file_origin.replace(".log",".csv")

    # prompting the user to overwrite existing file (W) or abort (any other key)
    if os.path.exists(base_csv_name) and input(CTS.ALREADY_EXISTS_ERR_MSG).upper() != "W":
        quit()

    with open(base_csv_name, "w") as csvfile:
        # remove parentheses, spaces and quotes from the string representation of a tuple
        print(re.sub("\(|\)|\s|'", "", str(CTS.COLUMN_NAMES)), file=csvfile)

    # list of rows to be inserted each second into a DataFrame
    chunk = []

    with open(CTS.LOG_DIR + file_origin) as logfile:
        uid, reference = get_id_reference(logfile)
        buffer = Buffer(uid)
        old_timestamp = 0
        line = logfile.readline()

        while len(line) > 0:
            buffer.update(line)
            chunk.append(buffer.toList())

            try:
                timestamp = int(buffer["timestamp"])
            except:
                print("Unexpected error: non-numeric timestamp", file=sys.stderr)
                print("Closing file descriptors and exiting...", file=sys.stderr)
                break

            # computing statistics every "split interval" milliseconds
            if timestamp >= reference + CTS.SPLIT_INTERVAL_MS:
                reference = timestamp
                compute_statistics(base_csv_name, CTS.RAW_COLUMN_NAMES, chunk)
                chunk = []

            buffer.flush()
            line = logfile.readline()

        # store the remaining data
        compute_statistics(base_csv_name, CTS.RAW_COLUMN_NAMES, chunk)