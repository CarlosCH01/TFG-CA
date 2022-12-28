import os
import pandas as pd
import sys
import traceback

import constants as CTS


class Buffer:
    """ Implementation of a buffer to convert from log to csv format """
    def __init__(self, uid):
        self.uid = uid
        self.buffer = {"timestamp": 0,
                       "accx": 0.0, "accy": 0.0, "accz": 0.0,
                       "gyrx": 0.0, "gyry": 0.0, "gyrz": 0.0, 
                       "magx": 0.0, "magy": 0.0, "magz": 0.0 }

    def isEmpty(self, magnitude=None):
        if magnitude is None:
            return self.buffer["timestamp"] == 0
            
        if magnitude in ("acc","gyr","mag"):
            # metawear sends these magnitudes in packets of 3. So, if
            # x coordinate exists, the rest are assumed to exist
            return self.buffer[magnitude + "x"] == 0.0
        else:
            return self.buffer[magnitude] == 0.0

    def flush(self):
        for k in self.buffer.keys(): 
            self.buffer[k] = 0.0

    def update(self, info):
        """ 
        Updates the buffer with new info from the log file
        Format of this info: [timestamp in 100ths of sec] magnitude: (X,Y,Z)
        """
        magnitude = info[15:18]
        new_content = info[info.find("(") + 1 : info.find(")")].split(",")

        self.buffer["timestamp"] = int(info[1:13])

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
    reference = int(fd.readline()[1:13])
    # return to the start of the first log line
    fd.seek(p)

    return uid, reference

if __name__ == "__main__":
    file_origin = set_file_origin()
    logfile_size = os.stat(CTS.LOG_DIR + file_origin).st_size
    csv_counter = 0
    #baseCSVDirectory = CTS.CSV_DIR + file_origin.replace(".log","/")
    #baseCSVName = baseCSVDirectory + "las_stats.csv"
    base_csv_name = CTS.CSV_DIR + file_origin.replace(".log",".csv")
    column_names = ["TIMESTAMP","ACCX","ACCY","ACCZ","GYRX","GYRY","GYRZ","MAGX","MAGY","MAGZ","UID"]

    if os.path.exists(base_csv_name) and input(CTS.ALREADY_EXISTS_ERR_MSG).upper() != "W":
        quit()

    '''header = "ACCX,ACCY,ACCZ,GYRX,GYRY,GYRZ,MAGX,MAGY,MAGZ,UID\n"
    with open(baseCSVName, "w") as csvfile:
        csvfile.write(header)'''
    
    '''# DataFrame to be used to compute statistcs
    dataAggregator = pd.DataFrame(columns=["TIMESTAMP","ACCX","ACCY","ACCZ","GYRX","GYRY","GYRZ","MAGX","MAGY","MAGZ","UID"])
    dataAggregator.set_index("TIMESTAMP", inplace=True)'''
    # list of rows to be inserted each second in the DataFrame
    chunk = []

    with open(CTS.LOG_DIR + file_origin) as logfile:
        uid, reference = get_id_reference(logfile)
        buffer = Buffer(uid)
        old_timestamp = 0
        line = logfile.readline()

        #try:
        while len(line) > 0:
            buffer.update(line)
            chunk.append(buffer.toList())

            try:
                timestamp = int(buffer["timestamp"])
            except:
                print("Unexpected error: non-numeric timestamp", file=sys.stderr)
                print("Closing file descriptors and exiting...", file=sys.stderr)
                break

            if timestamp >= reference + 100:
                reference = timestamp
                data_aggregator = pd.DataFrame(chunk, columns=column_names)
                data_aggregator.set_index("TIMESTAMP", inplace=True)
                chunk = []
                with open(base_csv_name, "a") as csv_file:
                    data_aggregator.describe().to_csv(csv_file, header=False)

            buffer.flush()
            line = logfile.readline()

        data_aggregator = pd.DataFrame(chunk, columns=column_names)
        data_aggregator.set_index("TIMESTAMP", inplace=True)
        '''print(data_aggregator)
        print(data_aggregator.drop("UID",axis=1).agg(["mean","std","min","max"]))
        print(data_aggregator.corr())'''
        with open(base_csv_name, "a") as csv_file: 
            data_aggregator.describe().to_csv(csv_file, header=False)

























            '''# fill buffer with log values
                buffer.update(line)

                timestamp = int(buffer["timestamp"])

                # write buffer contents and flush it when new timestamp is reached
                if timestamp > old_timestamp and not buffer.isEmpty():
                    #res += buffer.toCSV()
                    chunk.append(buffer.toList())
                    buffer.flush()

                # check whether at least one second has passed
                if timestamp >= reference + 100:
                    reference = timestamp
                    
                    dataAggregator = pd.DataFrame(chunk, 
                                columns=["TIMESTAMP","ACCX","ACCY","ACCZ","GYRX","GYRY","GYRZ","MAGX","MAGY","MAGZ","UID"])
                    dataAggregator.set_index("TIMESTAMP", inplace=True)
                    if timestamp
                        print(dataAggregator.head())
                        print(dataAggregator.describe())
                        print(dataAggregator.info())

                    with open(baseCSVName, "a") as csvfile:
                        csvfile.write("chunk size: " + str(len(res)) + "\n")
                    res = ""

                # update register
                old_timestamp = timestamp

                line = logfile.readline()
            '''
            '''with open(baseCSVName, "a") as csvfile:
                csvfile.write("chunk size: " + str(len(res)) + "\n")
                '''
        #except:
        #    traceback.print_exc()
        #    print("Error processing file, closing file descriptors...")