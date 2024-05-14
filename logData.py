import networkx as nx
from time import sleep
import threading, serial, socket, re
import tkinter as tk

def extract(text):
    pattern = r'\((.*?)\)'  # 괄호 안에 있는 값을 추출하기 위한 정규 표현식
    matches = re.findall(pattern, text)  # 정규 표현식과 문자열을 매칭하여 값들을 추출
    
    return matches

class LogData:
    # Class initialize
    def __init__(self, filename, socket_ip, socket_port, main):
        self.node_cnt = 1
        self.rootG = nx.DiGraph()
        self.entireG = nx.DiGraph()
        self.neighborG = nx.DiGraph()
        self.networkG = nx.DiGraph()
        self.ranks = {}
        self.annotation = {}
        self.prr = {2:[0,1]}
        self.event = threading.Event()
        self.socketConnected = False
        self.logfile_name = filename
        self.ROOT_NODE = 1
        self.NODE_TYPE = [None, "AP", "SENSOR", "ACTUATOR", "ROUTER", "VSENSOR-ACTIVATED", "VSENSOR-DEACTIVATED"]
        self.NODE_COLOR = [None, "red", "blue", "green", "cyan", "orange", "grey"]
        self.maxSequence = tk.IntVar(value=0)
        self.main = main
        self.socket_ip = socket_ip
        self.socket_port = socket_port
        self.spattern = r"\[S\]:(\d{1,}):(\d{1,})DA(\d{2}.\d{2})(\d{2}\.\d{2})(\d{2}\.\d{2})(\d{1,4})EN"
        self.vpattern = r"\[V\]:(\d{1}):(\d{1,})VIRTUAL-SENSOR"

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
            self.entireG.add_node(i)
            self.rootG.add_node(i)
            self.networkG.add_node(i)
            if i!=1:
                if self.incoming[i][self.parent[i]]==0:
                    prr1 = self.outgoing[self.parent[i]][i]
                    prr2 = self.incoming[self.parent[i]][i]
                else:
                    prr1 = self.incoming[i][self.parent[i]]
                    prr2 = self.outgoing[i][self.parent[i]]
                self.networkG.add_weighted_edges_from([(self.parent[i],i,prr1)],color="red")
                self.networkG.add_weighted_edges_from([(i,self.parent[i],prr2)], color="blue")
            for j in range(i+1, self.node_cnt+1):
                if i==j or self.outgoing[i][j]==0: continue
                self.entireG.add_edge(i, j, color="red")
                self.entireG.add_edge(j, i, color="blue")
        self.neighborPos = nx.spring_layout(self.entireG)

        self.annotation = {i:self.NODE_TYPE[self.node_type[i]] for i in range(1,self.node_cnt+1)}
        for i in range(1, self.node_cnt+1):
            for j in range(1, self.node_cnt+1):
                self.annotation[(i, j)] = dict(s="%d/%d"%(self.incoming[i][j], self.outgoing[i][j]), color="red")
    def logfile(self):
        sleep(3)
        f = open(self.logfile_name, "r")
        while True:
            if self.event.is_set():return
            line = f.readline()[:-1]
            if len(line)==0: 
                sleep(1)
                continue
            self.processLine(line)
    # Serial Communication
    def serial(self):
        sleep(3)
        PORT = "/dev/ttyUSB0"
        BAUD_RATE = 57600
        f = open(self.logfile_name, "w")
        try:
            self.fd = serial.Serial(PORT, BAUD_RATE)
        except serial.serialutil.SerialException:
            self.appendLog("Unable to open serial device")
            self.event.set()
            return
        self.appendLog("PORT OPEN SUCCESS")
        while True:
            if not self.fd.readable(): continue
            line = self.fd.readline().decode()[:-1]
            self.appendLog(line)
            f.write(line); f.flush()
            if line.find("ZZIOT_READY")!=-1: 
                self.fd.write(b"START\x7F")
                break

        while True:
            if not self.fd.readable(): sleep(0.5)
            line = self.fd.readline().decode()[:-1]
            f.write(line); f.flush()
            self.processLine(line)
        
    def processLine(self, line):
        if line == "":return
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
            self.prr = {id:[0,1] for id in range(self.node_cnt+1)}
            self.main.statusText.set_text(f"{self.node_cnt} nodes ready")
            self.main.canvas.draw_idle()
        elif line.startswith("[N]") or line.startswith("[+]"):
            self.nodeInfo(line)
        elif line.find("===END-OF-NI===")!=-1:
            self.graphInfo()
            if not self.main.isDebug.get(): self.main.socketThread.start()
            self.main.resetLayoutButton["state"] = "active"
            self.main.modeRadio1["state"] = "active"
            self.main.modeRadio2["state"] = "active"
            self.main.modeRadio3["state"] = "active"
            self.main.modeRadio4["state"] = "active"
            self.main.configButton["state"] = "disabled"
            self.main.statusText.set_text("Graph is ready to draw\nPress a radio button on the left side.")
            self.main.canvas.draw_idle()
        elif line.find("DATA-PACKET")!=-1:
            source = re.search(r"source=\((\d+)\): num-of-data=\((\d+)\)", line)
            self.prr[int(source.group(1))][0] = int(source.group(2))
        elif line.startswith("[V]"):
            matches = re.search(self.vpattern, line)
            index = int(matches.group(1))
            now = int(matches.group(2))
            self.prr[index][1]=now
            self.changeLabel(index)            

        elif line.startswith("[S]"):
            matches = re.search(self.spattern, line)
            index = int(matches.group(1))
            now = int(matches.group(2))
            so2 = float(matches.group(3))
            no2 = float(matches.group(4))
            nh3 = float(matches.group(5))
            co2 = int(matches.group(6))
            self.prr[index][1]=now
            self.changeLabel(index, [so2,no2,nh3,co2])
            if self.socketConnected: self.conn.send(("%d %f %f %f %d")%(index, so2, no2, nh3, co2).encode())

    def appendLog(self, line):
        self.main.lbox.insert(tk.END, line)
        self.main.lbox.update()
        self.main.lbox.see(tk.END)

    def changeLabel(self, index, datas=[0,0,0,0]):
        if self.NODE_TYPE[self.node_type[self.dg.selectedNode]] in ["VSENSOR-ACTIVATED", "VSENSOR-DEACTIVATED", "SENSOR"]:
            self.maxSequence.set(int(self.prr[index][0]/self.prr[index][1]*100))
            self.main.prrProgressBar.configure(mask="{}%"+f"({self.prr[self.dg.selectedNode][0]}/{self.prr[self.dg.selectedNode][1]})")
            if self.NODE_TYPE[self.node_type[self.dg.selectedNode]] == "SENSOR":
                self.main.so2DataLabel["text"] = "%05.2f"%datas[0]
                self.main.no2DataLabel["text"] = "%05.2f"%datas[1]
                self.main.nh3DataLabel["text"] = "%05.2f"%datas[2]
                self.main.co2DataLabel["text"] = "%04d"%datas[3]
                #self.main.canvas.draw_idle()
            else:
                self.main.so2DataLabel["text"] = "00.00"
                self.main.no2DataLabel["text"] = "00.00"
                self.main.nh3DataLabel["text"] = "00.00"
                self.main.co2DataLabel["text"] = "0000"
    
    # Socket Communication
    def socketCommunication(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ("192.168.0.159", self.socket_port)

        self.sock.bind(server_address)
        self.sock.setblocking(False)
        self.sock.listen(1)
        while True:
            try:
                self.conn, client_address = self.sock.accept()
                break
            except BlockingIOError:
                continue
        self.socketConnected = True
        print(client_address)

        while True:
            if self.event.is_set():break
            try:
                data = eval(self.conn.recv(1024).decode())[1]
                if data=="on":
                    print("SENSOR ON")
                    if self.activate[4]: continue
                    self.dg.selectedNode = 4
                    self.main.activateButtonPressed(ai=True)
                elif data=="off":
                    print("SENSOR OFF")
                    if not self.activate[4]: continue
                    self.dg.selectedNode = 4
                    self.main.activateButtonPressed(ai=True)
            except BlockingIOError:
                continue
            except Exception:
                continue