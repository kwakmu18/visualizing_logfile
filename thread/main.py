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

ld.getNodeInfo()
print("get node data done")
ld.getTreeInfo()
print("get tree info done")

thread1 = threading.Thread(target=ld.getNodeData)
thread1.start()
thread2 = threading.Thread(target=refreshPrr)
thread2.start()
drawGraph.init()
print("drawing graph...")
drawGraph.start()