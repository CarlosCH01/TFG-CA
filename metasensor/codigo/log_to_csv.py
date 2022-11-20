class Buffer:
    def __init__(self):
        self.buffer = {"acc": ['','',''], "gyr": ['','',''], "mag": ['','','']}

    def isFull(self):
        return self.buffer["acc"] is not None \
            and self.buffer["gyr"] is not None \
            and self.buffer["mag"] is not None
    
    def flush(self):
        self.buffer["acc"] = ['','','']
        self.buffer["gyr"] = ['','','']
        self.buffer["mag"] = ['','','']

    def toCSV(self):
        return "{},{},{},{},{},{},{},{},{}".format(self.buffer["acc"][0], self.buffer["acc"][1], self.buffer["acc"][2], \
                                                   self.buffer["gyr"][0], self.buffer["gyr"][1], self.buffer["gyr"][2], \
                                                   self.buffer["mag"][0], self.buffer["mag"][1], self.buffer["mag"][2], )

    def __getitem__(self, key):
        return self.buffer[key]


logfile = open("sensor_log.log")
csvfile = open("sensor_log.csv", "w")
buffer = Buffer()
old_line = ""

csvfile.write("ACCX,ACCY,ACCZ,GYRX,GYRY,GYRZ,MAGX,MAGY,MAGZ")

for line in logfile:
    if line[1:13] > old_line[1:13]:
        # save buffer
        # flush buffer
        pass
    buffer[line[15:18]] = line[line.find("(")+1:line.find(")")].split(",")
    old_line = line


pepe = []


csvfile.close()
logfile.close()