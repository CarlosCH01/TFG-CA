import os
import re
import traceback

import constants as CTS


class Buffer:
    """ Implementation of a buffer to convert from log to csv format """
    def __init__(self, uid):
        self.uid = uid
        self.buffer = {"acc": ['','',''], "gyr": ['','',''], "mag": ['','','']}

    def isEmpty(self, magnitude=None):
        empty = True
        if magnitude is None:
            for m in self.buffer.keys():
                for i in self.buffer[m]:
                    if i != '':
                        empty = False
        else:
            for i in self.buffer[magnitude]:
                if i != '':
                    empty = False
        return empty

    def flush(self):
        self.buffer["acc"] = ['','','']
        self.buffer["gyr"] = ['','','']
        self.buffer["mag"] = ['','','']

    def update(self, info):
        """ 
        Updates the buffer with new info from the log file
        Format of this info: [timestamp in 100ths of sec] magnitude: (X,Y,Z)
        """
        magnitude = info[15:18]
        new_content = info[info.find("(") + 1 : info.find(")")].split(",")

        if self.isEmpty(magnitude):
            self.buffer[magnitude] = new_content
        else:
            # compute the mean of the current value and the new one
            self.buffer[magnitude] = list( map(
                                            lambda a,b: "%.4f" % ((float(a)+float(b))/2), 
                                            self.buffer[magnitude], 
                                            new_content
                                            ) )

    def toCSV(self):
        return "{},{},{},{},{},{},{},{},{},{}\n"\
                    .format(self.buffer["acc"][0], self.buffer["acc"][1], self.buffer["acc"][2], \
                            self.buffer["gyr"][0], self.buffer["gyr"][1], self.buffer["gyr"][2], \
                            self.buffer["mag"][0], self.buffer["mag"][1], self.buffer["mag"][2],
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
    baseCSVDirectory = CTS.CSV_DIR + file_origin.replace(".log","/")

    if os.path.isdir(baseCSVDirectory):
        print("\nThere is already a CSV for this log file. Please delete it and rerun this script to proceed.")
        quit()

    os.mkdir(baseCSVDirectory)

    with open(CTS.LOG_DIR + file_origin) as logfile:
        res = "ACCX,ACCY,ACCZ,GYRX,GYRY,GYRZ,MAGX,MAGY,MAGZ,UID\n"
        uid, reference = get_id_reference(logfile)
        buffer = Buffer(uid)
        old_timestamp = 0
        line = ""

        try:
            while line is not None:
                line = logfile.readline()

                timestamp = int(line[1:13])
                #print(res[-25:])
                # write buffer contents and flush it when new timestamp is reached
                if timestamp > old_timestamp and not buffer.isEmpty():
                    res += buffer.toCSV()
                    buffer.flush()

                # check whether at least one second has passed
                if timestamp >= reference + 100:
                    reference = timestamp
                    csv_counter += 1
                    baseCSVName = baseCSVDirectory + f"{csv_counter}.csv"

                    # in case of end of log
                    if timestamp == 999999999999:
                        if not buffer.isEmpty():
                            res += buffer.toCSV()
                        with open(baseCSVName, "w") as csvfile:
                            csvfile.write(res)
                        break

                    with open(baseCSVName, "w") as csvfile:
                        csvfile.write(res)
                    res = "ACCX,ACCY,ACCZ,GYRX,GYRY,GYRZ,MAGX,MAGY,MAGZ,UID\n"

                # fill buffer with log values
                buffer.update(line)

                # update register
                old_timestamp = timestamp

        except:
            traceback.print_exc()
            print("Error processing file, closing file descriptors...")