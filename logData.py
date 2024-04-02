import networkx as nx
import re
from time import sleep
import threading, serial
import tkinter as tk

def extract(text):
    pattern = r'\((.*?)\)'  # 괄호 안에 있는 값을 추출하기 위한 정규 표현식
    matches = re.findall(pattern, text)  # 정규 표현식과 문자열을 매칭하여 값들을 추출
    
    return matches

class LogData:
    # Class initialize
    def __init__(self, filename, data_cnt, main):
        self.node_cnt = 1
        self.rootG = nx.DiGraph()
        self.entireG = nx.DiGraph()
        self.neighborG = nx.DiGraph()
        self.ranks = {}
        self.annotation = {}
        self.prr = {}
        self.event = threading.Event()
        self.ROOT_NODE = 1
        self.LOGFILE_NAME = filename
        self.NODE_TYPE = [None, "AP", "SENSOR", "ACTUATOR", "ROUTER", "VSENSOR", "DEACTIVATED"]
        self.NODE_COLOR = [None, "red", "blue", "green", "cyan", "orange", "grey"]
        self.NODE_EDGECOLOR = ["white", "white", "black", "white", "white", "black"]
        self.maxSequence = tk.IntVar(value=0)
        self.main = main
        self.data_cnt = data_cnt

    def nodeInfo(self, line:str):
        sections = extract(line)
        root_id, root_type, root_level, root_rank, root_parent_id = map(int, sections[0].split(","))
        self.ranks[root_id] = root_rank
        self.node_type[root_id] = root_type
        self.parent[root_id] = root_parent_id
        for section in sections[1:]:
            child_id, child_level, child_incoming, child_outgoing = map(int, section.split(","))
            self.incoming[root_id][child_id]=child_incoming
            self.outgoing[root_id][child_id]=child_outgoing

    def graphInfo(self):
        for i in range(1, self.node_cnt+1):
            self.entireG.add_node(i)#, name=i, color=self.NODE_COLOR[self.node_type[i]], edge_color=self.NODE_EDGECOLOR[self.node_type[i]])
            self.rootG.add_node(i)#, name=i,color=self.NODE_COLOR[self.node_type[i]], edge_color=self.NODE_EDGECOLOR[self.node_type[i]])
            for j in range(i+1, self.node_cnt+1):
                if i==j or self.outgoing[i][j]==0: continue
                self.entireG.add_edge(i, j, color="red")#, weight=incoming[i][j] if incoming[i][j]!=0 else outgoing[i][j])
                self.entireG.add_edge(j, i, color="blue")

        self.pos = nx.spring_layout(self.entireG)
        self.neighborPos = self.pos

        self.annotation = {i:self.NODE_TYPE[self.node_type[i]] for i in range(1,self.node_cnt+1)}
        for i in range(1, self.node_cnt+1):
            for j in range(1, self.node_cnt+1):
                self.annotation[(i, j)] = dict(s="%d/%d"%(self.incoming[i][j], self.outgoing[i][j]), color="red")
    def logfile(self):
        sleep(3)
        f = open(self.LOGFILE_NAME, "r")
        while True:
            if self.event.is_set():return
            line = f.readline()
            if len(line)==0: 
                sleep(1)
                continue
            self.processLine(line)
    # Serial Communication
    def serial(self):
        sleep(3)
        PORT = "/dev/ttyUSB0"
        BAUD_RATE = 57600
        f = open(self.LOGFILE_NAME, "w")
        try:
            fd = serial.Serial(PORT, BAUD_RATE)
        except serial.serialutil.SerialException:
            self.appendLog("Unable to open serial device")
            self.event.set()
            return
        self.appendLog("PORT OPEN SUCCESS")
        while True:
            if not fd.readable(): continue
            line = fd.readline().decode()
            self.appendLog(line)
            f.write(line); f.flush()
            if line.find("ZZIOT_READY")!=-1: 
                fd.write(b"START\x7F")
                break
        self.appendLog("Server sent START command")

        while True:
            if not fd.readable(): sleep(0.5)
            line = fd.readline().decode()
            f.write(line); f.flush()
            self.processLine(line)
        
    def processLine(self, line):
        self.appendLog(line)
        if line.find("add new NBR")!=-1:
            self.node_cnt += 1
            self.main.statusText.set_text(f"{self.node_cnt} nodes standby")
            self.main.canvas.draw_idle()
        elif line.find("all PROBE_PRR packets sent")!=-1:
            self.incoming = [[0 for _ in range(self.node_cnt+1)] for _ in range(self.node_cnt+1)]
            self.outgoing = [[0 for _ in range(self.node_cnt+1)] for _ in range(self.node_cnt+1)]
            self.parent = [0 for _ in range(self.node_cnt+1)]
            self.node_type = [0 for _ in range(self.node_cnt+1)]
            self.child_cnt = [0 for _ in range(self.node_cnt+1)]
            self.activate = [True for _ in range(self.node_cnt+1)]
            self.main.statusText.set_text(f"{self.node_cnt} nodes ready")
            self.main.canvas.draw_idle()
        elif line.startswith("[N]") or line.startswith("[+]"):
            self.nodeInfo(line)
        elif line.find("===END-OF-NI===")!=-1:
            self.graphInfo()
            self.main.resetLayoutButton["state"] = "active"
            self.main.modeRadio1["state"] = "active"
            self.main.modeRadio2["state"] = "active"
            self.main.modeRadio3["state"] = "active"
            self.main.statusText.set_text("Graph is ready to draw\nPress a radio button on the left side.")
            self.main.canvas.draw_idle()
        elif line.startswith("[V]"):
            line = line.split(":")
            index = int(line[1])
            now = int(line[2].split("V")[0])
            if index not in self.prr.keys():
                self.prr[index] = [1, now]
                return
            self.maxSequence.set(max(int(now/self.data_cnt*100), self.maxSequence.get()))
            self.prr[index][0]+=1
            self.prr[index][1]=now
            self.dg.changeLabel()
        elif line.startswith("[D]"):
            line = line.split(":")
            index = int(line[2])
            now = int(line[3])
            if index not in self.prr.keys():
                self.prr[index] = [1, now]
                return
            self.maxSequence.set(max(now, self.maxSequence.get()))
            self.prr[index][0]+=1
            self.prr[index][1]=now
            self.dg.changeLabel()
    def appendLog(self, line):
        self.main.lbox.insert(tk.END, line)
        self.main.lbox.update()
        self.main.lbox.see(tk.END)
