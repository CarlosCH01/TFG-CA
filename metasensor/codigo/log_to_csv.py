import os
import re
import traceback

import constants as CTS


class Buffer:
    """ Implementation of a buffer to convert from log to csv format """
    def __init__(self, uid):
        self.uid = uid
        self.buffer = {"timestamp": '',
                       "accx": '', "accy": '', "accz": '',
                       "gyrx": '', "gyry": '', "gyrz": '', 
                       "magx": '', "magy": '', "magz": '' }

    def isEmpty(self, magnitude=None):
        if magnitude is None:
            return self.buffer["timestamp"] == ''
            
        if magnitude in ("acc","gyr","mag"):
            # metawear sends these magnitudes in packets of 3. So, if
            # x coordinate exists, the rest are assumed to exist
            return self.buffer[magnitude + "x"] == ''
        else:
            return self.buffer[magnitude] == ''

    def flush(self):
        for k in self.buffer.keys(): 
            self.buffer[k] = '' 

    def update(self, info):
        """ 
        Updates the buffer with new info from the log file
        Format of this info: [timestamp in 100ths of sec] magnitude: (X,Y,Z)
        """
        magnitude = info[15:18]
        new_content = info[info.find("(") + 1 : info.find(")")].split(",")

        self.buffer["timestamp"] = info[1:13]

        if self.isEmpty(magnitude):
            # data can be one single value or a 3-dimensional vector
            if len(new_content) > 1:
                self.buffer[magnitude + "x"] = new_content[0]
                self.buffer[magnitude + "y"] = new_content[1]
                self.buffer[magnitude + "z"] = new_content[2]
            else:
                self.buffer[magnitude] = new_content
        else:
            # compute the mean of the current value and the new one
            if len(new_content) > 1:
                for i, coord in enumerate(("x","y","z")):
                    self.buffer[magnitude + coord] = "%.4f" % ( (float(self.buffer[magnitude + coord]) + float(new_content[i]))/2 )
            else:
                self.buffer[magnitude] = "%.4f" % ( (float(self.buffer[magnitude]) + float(new_content))/2 )

    def toCSV(self):
        return "{},{},{},{},{},{},{},{},{},{},{}\n"\
                    .format(self.buffer["timestamp"],
                            self.buffer["accx"], self.buffer["accy"], self.buffer["accz"], \
                            self.buffer["gyrx"], self.buffer["gyry"], self.buffer["gyrz"], \
                            self.buffer["magx"], self.buffer["magy"], self.buffer["magz"],
                            self.uid)

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
    file_destination = CTS.CSV_DIR + file_origin.replace(".log",".csv")

    if os.path.exists(file_destination):
        print("\nThere is already a CSV for this log file. Please delete it and rerun this script to proceed.")
        quit()

    with open(CTS.LOG_DIR + file_origin) as logfile:
        # log file header: UID padded with zeroes to the left until three digits + \n
        # pick only the UID (not newline) and discard padding zeroes
        line = logfile.readline()
        uid = line[:3].lstrip("0")
        buffer = Buffer(uid)
        old_timestamp = 0
        line = ""

        with open(file_destination,"w") as csvfile:
            try:
                csvfile.write("TIMESTAMP,ACCX,ACCY,ACCZ,GYRX,GYRY,GYRZ,MAGX,MAGY,MAGZ,UID\n")

                while line is not None:
                    line = logfile.readline()
                    timestamp = int(line[1:13])

                    if timestamp == 999999999999:
                        break

                    # write buffer contents and flush it when new timestamp is reached
                    if timestamp > old_timestamp and not buffer.isEmpty():
                        csvfile.write(buffer.toCSV())
                        buffer.flush()

                    # fill buffer with log values
                    buffer.update(line)

                    # update register
                    old_timestamp = timestamp

            except:
                traceback.print_exc()
                print("Error processing file, closing file descriptors...")