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
    def __init__(self, filename):
        self.node_cnt = 1
        self.G = nx.Graph()
        self.rootG = nx.DiGraph()
        self.neighborG = nx.Graph()
        self.entireG = None
        self.colors = []
        self.edge_colors = []
        self.pos = None
        self.neighborPos = None
        self.ranks = {}
        self.annotation = {}
        self.prr = {}
        self.event = threading.Event()
        self.ROOT_NODE = 1
        self.LOGFILE_NAME = filename
        self.F = open(self.LOGFILE_NAME, "r")
        self.NODE_TYPE = [None, "AP", "Sensor", "Actuator", "Router", "Virtual Sensor"]
        self.NODE_COLOR = [None, "red", "blue", "green", "cyan", "orange"]
        self.NODE_EDGECOLOR = ["white", "white", "black", "white", "white", "black"]
        self.maxSequence = 1
    def setDG(self, dg):
        self.dg = dg

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
        self.activate = {True for _ in range(self.node_cnt+1)}
        for i in range(1, self.node_cnt+1):
            self.G.add_node(str(i), name=i, color=self.NODE_COLOR[self.node_type[i]], edge_color=self.NODE_EDGECOLOR[self.node_type[i]])
            for j in range(i+1, self.node_cnt+1):
                if i==j or self.outgoing[i][j]==0: continue
                self.G.add_edge(str(i), str(j))#, weight=incoming[i][j] if incoming[i][j]!=0 else outgoing[i][j])
                self.G.add_edge(str(j), str(i))

        self.pos = nx.spring_layout(self.G)
        self.neighborPos = self.pos

        self.entireG = self.G.copy()

        self.G.clear()
        self.G.clear_edges()

        for i in range(2, len(self.parent)):
            self.G.add_edge(str(i), str(self.parent[i]))


        for i in range(1, self.node_cnt+1):
            self.G.add_node(str(i), name=i,color=self.NODE_COLOR[self.node_type[i]], edge_color=self.NODE_EDGECOLOR[self.node_type[i]])
            self.rootG.add_node(str(i), name=i,color=self.NODE_COLOR[self.node_type[i]], edge_color=self.NODE_EDGECOLOR[self.node_type[i]])

        self.annotation = {str(i):self.NODE_TYPE[self.node_type[i]] for i in range(1,self.node_cnt+1)}
        for i in range(1, self.node_cnt+1):
            for j in range(1, self.node_cnt+1):
                self.annotation[(str(i), str(j))] = dict(s="%d/%d"%(self.incoming[i][j], self.outgoing[i][j]), color="red")
        self.dg.drawRootGraph()
    def logfile(self):
        sleep(3)
        f = open(self.LOGFILE_NAME, "r")
        while True:
            if self.event.is_set():return
            line = f.readline()
            if len(line)==0: 
                sleep(1)
                continue
            self.processLine(line.encode())
    # Serial Communication
    def serial(self):
        sleep(3)
        PORT = "/dev/ttyUSB0"
        BAUD_RATE = 57600
        f = open(self.LOGFILE_NAME, "a")
        try:
            fd = serial.Serial(PORT, BAUD_RATE)
        except serial.serialutil.SerialException:
            print("Unable to open serial device")
            self.event.set()
            return
        print("PORT OPEN SUCCESS")
        while True:
            if not fd.readable(): continue
            line = fd.readline()
            print(f"PORT0: {line}")
            f.write(line); f.flush()
            if line.find("ZZIOT READY")!=-1: break
        
        while True:
            if input("ZZIOT is ready: start now? (Y/N): ")=="Y":break
        fd.write("START")
        print("Server sent START command")

        while True:
            if not fd.readable(): sleep(0.5)
            line = fd.readline()
            f.write(line); f.flush()
            self.processLine(line)
        
    def processLine(self, line:bytes):
        line = line.decode()
        self.dg.lbox.insert(tk.END, line)
        self.dg.lbox.update()
        self.dg.lbox.see(tk.END)
        if line.find("add new NBR")!=-1:
            self.node_cnt += 1
            self.dg.statusText.set_text(f"{self.node_cnt} nodes standby")
            self.dg.canvas.draw()
        elif line.find("all PROBE_PRR packets sent")!=-1:
            self.incoming = [[0 for _ in range(self.node_cnt+1)] for _ in range(self.node_cnt+1)]
            self.outgoing = [[0 for _ in range(self.node_cnt+1)] for _ in range(self.node_cnt+1)]
            self.parent = [0 for _ in range(self.node_cnt+1)]
            self.node_type = [0 for _ in range(self.node_cnt+1)]
            self.child_cnt = [0 for _ in range(self.node_cnt+1)]
            self.dg.statusText.set_text(f"{self.node_cnt} nodes ready")
            self.dg.canvas.draw()
        elif line.startswith("[N]") or line.startswith("[+]"):
            self.nodeInfo(line)
        elif line.find("===END-OF-NI===")!=-1:
            self.graphInfo()
        elif line.startswith("[D]"):
            line = line.split(":")
            index = int(line[2])
            now = int(line[3])
            self.maxSequence = max(self.maxSequence, now)
            if index not in self.prr.keys():
                self.prr[index] = [1, now]
                return
            self.prr[index][0]+=1
            self.prr[index][1]=now
            self.dg.changeLabel()