import os
import sys
import time
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


def mean(list1, list2):
    """ Computes the mean of two lists. Truncates to the shortest list length """
    res = []
    for i in range(min(len(list1), len(list2))):
        res.append("%.4f" % ((float(list1[i]) + float(list2[i]))/2) )
    return res

def set_file_origin():
    """ Returns the name of the log file to convert """
    files = os.listdir(CTS.LOG_DIR)
    for i, f in enumerate(files):
        print(i+1, f)

    logfile_index = ""
    while not logfile_index.isdigit() or int(logfile_index) - 1 not in range(len(files)):
        logfile_index = input("Select a file from the list: ")

    return files[int(logfile_index) - 1]

def progress_bar(total, position):

    # setup toolbar
    sys.stdout.write("[%s]" % (" " * 100))
    sys.stdout.flush()
    sys.stdout.write("\b" * (100+1)) # return to start of line, after '['

    for i in range(position // total * 100):
        # update the bar
        sys.stdout.write("-")
        sys.stdout.flush()

    sys.stdout.write("]\n") # this ends the progress bar


if __name__ == "__main__":
    file_origin = set_file_origin()
    logfile = open(CTS.LOG_DIR + file_origin)
    csvfile = open(CTS.CSV_DIR + file_origin.replace("log", "csv") , "w")
    csvfile.write("ACCX,ACCY,ACCZ,GYRX,GYRY,GYRZ,MAGX,MAGY,MAGZ,UID\n")

    # log file header: UID padded with zeroes to the left until three digits + \n
    # pick only the UID (not newline) and discard padding zeroes
    uid = logfile.readline()[:3].lstrip("0")
    logfile_size = os.stat(CTS.LOG_DIR + file_origin).st_size

    buffer = Buffer(uid)
    old_line = "[000000000000]"

    try:
        for line in logfile:
            #print("{:.2f}".forma(logfile.tell() / logfile_size * 100), end="")
            #progress_bar(logfile_size, logfile.tell())
            time.sleep(0.1)
            timestamp = line[1:13]
            old_timestamp = old_line[1:13]

            # did we reach last record? Then write and quit
            if timestamp == "999999999999":
                if not buffer.isEmpty():
                    csvfile.write(buffer.toCSV())
                break

            # write buffer contents and flush it when new timestamp is reached
            if timestamp > old_timestamp and not buffer.isEmpty():
                csvfile.write(buffer.toCSV())
                buffer.flush()

            # fill buffer with log values
            magnitude = line[15:18]
            new_content = line[line.find("(") + 1 : line.find(")")].split(",")
            if buffer.isEmpty(magnitude):
                buffer[magnitude] = new_content
            else:
                buffer[magnitude] = mean(buffer[magnitude], new_content)
            old_line = line
    except:
        traceback.print_exc()
        print("Error processing file, closing file descriptors...")

    csvfile.close()
    logfile.close()