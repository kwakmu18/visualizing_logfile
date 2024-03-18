import drawGraph
import threading
import time
from logData import ld

def refreshPrr():
    while True:
        if ld.event.is_set():return
        time.sleep(0.5)
        drawGraph.prrText.set_text(ld.prrStr)
        drawGraph.canvas.draw()

thread1 = threading.Thread(target=ld.serial)
thread1.start()

ld.getNodeInfo()
if ld.event.is_set():
    exit()
print("get node data done")
ld.getTreeInfo()
print("get tree info done")

thread2 = threading.Thread(target=ld.getNodeData)
thread2.start()
thread3 = threading.Thread(target=refreshPrr)
thread3.start()
drawGraph.init()
print("drawing graph...")
drawGraph.start()