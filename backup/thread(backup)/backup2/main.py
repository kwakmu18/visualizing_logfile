import drawGraph, logData
import threading
import time
import os

FILENAME = "log.txt"

while True:
    line = input("reset logfile? (Y/N) > ")
    if line == "Y":
        try:os.remove(FILENAME)
        except FileNotFoundError:
            pass
        with open(FILENAME, "w") as f:
             pass
        break
    elif line == "N":
        break
ld = logData.LogData(FILENAME)

#serialThread = threading.Thread(target=ld.serial)
serialThread = threading.Thread(target=ld.logfile)
serialThread.start()
dg = drawGraph.DrawGraph(ld)