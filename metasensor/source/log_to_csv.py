import numpy as np
import os
import pandas as pd
import re
import sys

import constants as CTS

class Buffer:
    """ Implementation of a buffer to convert from log to other formats """
    def __init__(self, uid, magnitudes):
        self.uid = uid
        # 'magnitudes' sets the magnitudes to measure and their *order*
        self.magnitudes = magnitudes
        self.timestamp = 0
        self.buffer = {}
        self.flush()

    def isEmpty(self, magnitude=None):
        if magnitude is None:
            return self.timestamp == 0
            
        if magnitude in CTS.TRI_AXIS_MAGS:
            # metawear sends these magnitudes in packets of 3. So, if
            # x coordinate exists, the rest are assumed to exist
            return np.isnan(self.buffer[magnitude][0])
        
        return np.isnan(self.buffer[magnitude])

    def flush(self):
        self.timestamp = 0
        for m in self.magnitudes:
            self.buffer[m] = [np.nan, np.nan, np.nan] if m in CTS.TRI_AXIS_MAGS else np.nan

    def update(self, info):
        """ 
        Updates the buffer with new info from the log file
        Format of this info: [timestamp in millisecs] magnitude: (X,Y,Z) | N
        """
        magnitude   = info[ info.find("]") + 2 : info.find(":") ]
        # TODO: ADAPTAR PARA CUANDO SOLO HAYA UN VALOR EN VEZ DE TRES
        new_content = info[ info.find("(") + 1 : info.find(")") ].split(",")

        self.timestamp = int(info[ info.find("[") + 1 : info.find("]") ])

        if self.isEmpty(magnitude):
            # data can be one single value or a 3-dimensional vector
            if magnitude in CTS.TRI_AXIS_MAGS:
                for i in range(3):
                    self.buffer[magnitude][i] = float(new_content[i])
            else:
                self.buffer[magnitude] = float(new_content)
        else:
            # compute the mean of the current value and the new one
            if magnitude in CTS.TRI_AXIS_MAGS:
                for i in range(3):
                    self.buffer[magnitude][i] = (self.buffer[magnitude][i] + float(new_content[i]))/2
            else:
                self.buffer[magnitude] = (self.buffer[magnitude] + float(new_content))/2

    def toList(self):
        res = [self.timestamp, self.uid]
        for m in self.magnitudes:
            if type(self.buffer[m]) == list:
                res.extend(self.buffer[m])
            else:
                res.append(self.buffer[m])
        return res

    def __getitem__(self, key):
        return self.buffer[key]

    def __setitem__(self, key, item):
        self.buffer[key] = item

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return self.toList()


def set_file_origin():
    """ Returns the name of the log file to convert """
    files = os.listdir(CTS.LOG_DIR)
    for i, f in enumerate(files):
        print(i+1, f)

    log_file_index = ""
    while not log_file_index.isdigit() or int(log_file_index) - 1 not in range(len(files)):
        log_file_index = input("Select a file from the list: ")

    return files[int(log_file_index) - 1]

def read_header(fd):
    # log file header:
    # pick only the UID (not newline) and discard padding zeroes
    header = fd.readline().split(",")
    uid = header[-1].replace("\n", "").lstrip("0")
    magnitudes = header[:-1]

    # store current position, read first timestamp and restore pointer
    p = fd.tell()
    ref_line = fd.readline()
    reference = int(ref_line[ref_line.find("[")+1:ref_line.find("]")])
    fd.seek(p)

    return uid, magnitudes, reference

def generate_column_names(magnitudes) -> str:
    cols = generate_raw_header(magnitudes)
    for s in CTS.STATISTICS:
        for m in range(2, len(cols)):
            cols[m] += "_" + s
    return re.sub("\[|\]|\s|'", "", str(cols))

def generate_raw_header(magnitudes) -> list:
    header = CTS.BASIC_CSV_HEADER
    for m in magnitudes:
        if m in CTS.TRI_AXIS_MAGS:
            for c in "XYZ":
                header += f",{m.upper()}{c}"
        else:
            header += "," + m.upper()
    return header.split(",")

def compute_statistics(csv_path, column_names, chunk):
    """ Condense a piece of data into required statistics and append to the destination file """

    data_aggregator = pd.DataFrame(chunk, columns=column_names).drop(["TIMESTAMP","UID"], axis=1)

    stats = data_aggregator.mean(numeric_only=True).to_list()
    stats.extend(data_aggregator.std(numeric_only=True).to_list())
    stats.extend(data_aggregator.min(numeric_only=True).to_list())
    stats.extend(data_aggregator.median(numeric_only=True).to_list())
    stats.extend(data_aggregator.max(numeric_only=True).to_list())
    
    # remove square brackets and spaces from the string representation of a list
    stats = re.sub("\[|\]|\s", "", str(stats))
    
    with open(csv_path, "a") as csv_file:
        # write down first timestamp and the UID for reference and the statistics
        print(f"{chunk[0][0]},{chunk[0][1]},{stats}", file=csv_file)


if __name__ == "__main__":
    file_origin = set_file_origin()
    csv_path = CTS.CSV_DIR + file_origin.replace(".log",".csv")

    # prompting the user to overwrite existing file (W) or abort (any other key)
    if os.path.exists(csv_path) and input(CTS.ALREADY_EXISTS_ERR_MSG).upper() != "W":
        quit()

    # container of rows from which a DataFrame will be created
    chunk = []

    with open(CTS.LOG_DIR + file_origin) as log_file:
        uid, magnitudes, reference = read_header(log_file)
        buffer = Buffer(uid, magnitudes)
        raw_header = generate_raw_header(magnitudes)

        with open(csv_path, "w") as csv_file:
            # remove parentheses, spaces and quotes from the string representation of a tuple
            print(generate_column_names(magnitudes), file=csv_file)

        line = log_file.readline()

        while len(line) > 0:
            buffer.update(line)
            chunk.append(buffer.toList())

            try:
                timestamp = int(buffer.timestamp)
            except:
                print("Unexpected error: non-numeric timestamp", file=sys.stderr)
                print("Closing file descriptors and exiting...", file=sys.stderr)
                break

            # computing statistics every "split interval" milliseconds
            if timestamp >= reference + CTS.SPLIT_INTERVAL_MS:
                reference = timestamp
                compute_statistics(csv_path, raw_header, chunk)
                chunk = []

            buffer.flush()
            line = log_file.readline()

        # store the remaining data
        compute_statistics(csv_path, raw_header, chunk)