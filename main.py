import drawGraph, logData, makeGraph
import threading, os, serial, netgraph, subprocess, networkx as nx
import tkinter as tk
import tkinter.messagebox as msgbox
import ttkbootstrap as ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import gridspec
import faulthandler; faulthandler.enable()

        # ------------------------------------------------- Constants ----------------------------------------------- #
PORT = "/dev/ttyUSB0"
BAUD_RATE = 57600
SOCKET_IP = "192.168.0.177"
SOCKET_PORT = 8001
        # ------------------------------------------------- Constants ----------------------------------------------- #

class TkinterUI:
    def __init__(self):
        # ------------------------------------------------ Configure UI ------------------------------------------------ #
        self.window = ttk.Window(themename="minty")
        self.mode = tk.IntVar(value=2)

        self.ld = logData.LogData("log.txt", SOCKET_IP, SOCKET_PORT, self)
        self.dg = drawGraph.DrawGraph(self, self.ld)

        self.window.geometry("1920x1080")
        self.window.protocol("WM_DELETE_WINDOW", self.terminate)
        self.window.title("NetworkX Graph")
        self.buttonFrame = ttk.LabelFrame(self.window, text="Buttons", labelanchor="n") # button
        self.buttonFrame.place(x=10, y=800, width=380, height=190)

        self.graphFrame = ttk.LabelFrame(self.window, text="Graph", labelanchor="n") # graph
        self.graphFrame.place(x=10, y=10, width=1890, height=780)

        self.logFrame = ttk.LabelFrame(self.window, text="Log Information", labelanchor="n") # log
        self.logFrame.place(x=800, y=800, width=1100, height=190)

        self.infoFrame = ttk.LabelFrame(self.window, text="Selected Node", labelanchor="n") # Node Information
        self.infoFrame.place(x=400, y=800, width=390, height=190)

        self.nodeIDFrame = ttk.LabelFrame(self.infoFrame, text="Node ID", labelanchor="n")
        self.nodeIDFrame.place(x=80, y=10, width=100, height=100)

        self.nodeTypeFrame = ttk.LabelFrame(self.infoFrame, text="Node Type", labelanchor="n")
        self.nodeTypeFrame.place(x=200, y=10, width=100, height=100)

        self.lbox = tk.Listbox(self.logFrame, bd=1)
        self.lbox.place(x=10, y=0, width=1060, height=150)
        self.vscroll = ttk.Scrollbar(self.logFrame, orient="vertical")
        self.hscroll = ttk.Scrollbar(self.logFrame, orient="horizontal")
        self.vscroll.config(command=self.lbox.yview)
        self.hscroll.config(command=self.lbox.xview)
        self.vscroll.place(x=1070, y=0, width=20, height=150)
        self.hscroll.place(x=10,y=150, width=1070, height=20)
        self.lbox.config(xscrollcommand=self.hscroll.set, yscrollcommand=self.vscroll.set)

        self.modeRadio1 = ttk.Radiobutton(self.buttonFrame, text="root node", variable=self.mode, value=0, command=self.radioButtonPressed)
        self.modeRadio1.place(x=80, y=7)
        self.modeRadio2 = ttk.Radiobutton(self.buttonFrame, text="neighbor", variable=self.mode, value=1, command=self.radioButtonPressed)
        self.modeRadio2.place(x=80, y=27)
        self.modeRadio3 = ttk.Radiobutton(self.buttonFrame, text="entire map", variable=self.mode, value=2, command=self.radioButtonPressed)
        self.modeRadio3.place(x=200, y=7)
        self.modeRadio4 = ttk.Radiobutton(self.buttonFrame, text="network result", variable=self.mode, value=3, command=self.radioButtonPressed)
        self.modeRadio4.place(x=200, y=27)

        self.modeRadio1["state"] = "disabled"
        self.modeRadio2["state"] = "disabled"
        self.modeRadio3["state"] = "disabled"
        self.modeRadio4["state"] = "disabled"

        self.startButton = ttk.Button(self.buttonFrame, text="START", command=self.startButtonPressed)
        self.configButton = ttk.Button(self.buttonFrame, text="Configuration", command=self.configButtonPressed)
        self.resetLayoutButton = ttk.Button(self.buttonFrame, text="Reset Layout",  command=self.resetLayoutButtonPressed)
        self.activateButton = ttk.Button(self.buttonFrame, text="Deactivate Node",  command = self.activateButtonPressed)

        self.startButton.place(x=10, y=50, width=175, height=50)
        self.configButton.place(x=185, y=50, width=175, height=50)
        self.resetLayoutButton.place(x=10, y=100, width=175, height=50)
        self.activateButton.place(x=185, y=100, width=175, height=50)

        self.resetLayoutButton["state"] = "disabled"
        self.activateButton["state"] = "disabled"

        self.isReset = tk.BooleanVar()
        self.isDebug = tk.BooleanVar()
        self.logFileName = tk.StringVar()

        self.prrLabel = ttk.Label(self.infoFrame, text="Node PRR")
        self.prrLabel.place(x=10, y=110, width=150, height=20)

        self.prrProgressBar = ttk.Floodgauge(self.infoFrame, variable=self.ld.maxSequence, mask="{}%"+"(0/0)")
        self.prrProgressBar.place(x=10, y=130, width=370, height=20)

        self.nodeTypeLabel = ttk.Label(self.nodeTypeFrame, text="", justify="center", font=(ttk.font.BOLD, 11))
        self.nodeTypeLabel.place(x=0, y=20, width=90, height=40)

        # ------------------------------------------------ Configure UI ------------------------------------------------ #

        # ----------------------------------------------- Configure Canvas --------------------------------------------- #
        self.fig = plt.figure(figsize=(15,10))
        spec = gridspec.GridSpec(ncols=2, nrows=1, width_ratios=[1,5])
        self.ax1 = self.fig.add_subplot(spec[0])
        self.ax2 = self.fig.add_subplot(spec[1])

        self.nodeIDFig, self.nodeIDAx = plt.subplots(1,1)
        self.nodeIDAx.set_axis_off()
        self.nodeG = nx.Graph()

        node_proxy_artists = []
        for i in range(1,len(self.ld.NODE_COLOR)):
            if self.ld.NODE_TYPE[i] in ["ACTUATOR", "SENSOR"]: continue
            proxy = plt.Line2D(
                [], [],
                linestyle='None',
                color=self.ld.NODE_COLOR[i],
                marker='o',
                markersize=8,
                label=self.ld.NODE_TYPE[i]
            )
            node_proxy_artists.append(proxy)

        node_legend = self.ax1.legend(handles=node_proxy_artists, loc='upper left', title='Nodes')
        self.ax1.add_artist(node_legend)
        self.ax1.set_axis_off()
        self.ax2.set_axis_off()
        self.statusText = self.ax2.text(0.5, 0.5, "PRESS START BUTTON TO START")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graphFrame)
        self.canvas.draw_idle()

        #Canvas 위젯 생성 및 그래프 출력
        self.canvas.get_tk_widget().pack()
        
        self.nodeIDCanvas = FigureCanvasTkAgg(self.nodeIDFig, master=self.nodeIDFrame)
        self.nodeIDCanvas.draw_idle()
        self.nodeIDCanvas.get_tk_widget().pack()

        self.window.mainloop()

        # ----------------------------------------------- Configure Canvas --------------------------------------------- #

    def radioButtonPressed(self):
        if self.mode.get()==0:
            makeGraph.makeRootGraph(self.ld, self.dg.selectedNode)
            self.dg.drawRootGraph()
        elif self.mode.get()==1:
            makeGraph.makeNeighborGraph(self.ld, self.dg.selectedNode)
            self.dg.drawNeighborGraph()
        elif self.mode.get()==3:
            self.dg.drawNetworkGraph()
        else:
            self.dg.drawRootGraph()
        return

    def terminate(self):
        self.ld.event.set()
        self.window.destroy()
        self.ld.sock.close()
    def terminateTop(self):
        self.ld.logfile_name = self.logFileName.get()
        self.top.destroy()

    def startButtonPressed(self):
        if not self.isDebug.get():
            try:
                serial.Serial(PORT, BAUD_RATE).close()
            except serial.serialutil.SerialException:
                msgbox.showwarning("ERROR", "Device is not ready.")
                return
            serialThread = threading.Thread(target=self.ld.serial)
            self.socketThread = threading.Thread(target=self.ld.socketCommunication)
        else:
            serialThread = threading.Thread(target=self.ld.logfile)
            self.socketThread = threading.Thread(target=self.ld.socketCommunication)
        if self.isReset.get():
            try:
                os.remove(self.logFileName.get())
                with open(self.logFileName.get(), "w") as f: pass
            except FileNotFoundError:
                with open(self.logFileName.get(), "w") as f: pass
        serialThread.start()
        self.statusText.set_text("STARTED")
        self.canvas.draw_idle()
        self.startButton["state"] = "disabled"
        self.configButton["state"] = "disabled"
    def configButtonPressed(self):
        self.top = ttk.Toplevel(self.window)
        self.top.protocol("WM_DELETE_WINDOW", self.terminateTop)
        self.window.protocol("WM_DELETE_WINDOW", self.terminate)
        self.top.attributes("-topmost", 1)
        self.top.geometry("800x600")
        self.top.title("Configuration")
        self.contiki_path, self.node_cnt, self.node_id, self.node_type, self.data_cnt = (tk.StringVar() for _ in range(5))
        contiki_path_label = ttk.Label(self.top, text="Contiki-NG Path : ")
        self.contiki_path_input = ttk.Entry(self.top, textvariable = self.contiki_path)
        node_cnt_label = ttk.Label(self.top, text="Node Cnt : ")
        self.node_cnt_input = ttk.Entry(self.top, textvariable=self.node_cnt)
        node_id_label = ttk.Label(self.top, text="Node ID : ")
        node_id_input = ttk.Entry(self.top, textvariable=self.node_id)
        node_type_label = ttk.Label(self.top, text="Node Type : ")
        node_type_input = ttk.Combobox(self.top, values=["AP", "ROUTER", "SENSOR", "VSENSOR"], textvariable=self.node_type)
        data_cnt_label = ttk.Label(self.top, text="Data Cnt : ")
        self.data_cnt_input = ttk.Entry(self.top, textvariable=self.data_cnt)
        reset_check = ttk.Checkbutton(self.top, text="Reset Logfile", variable=self.isReset, onvalue=1, offvalue=0)
        debugging_check = ttk.Checkbutton(self.top, text="Debugging Mode", variable=self.isDebug, onvalue=1, offvalue=0)
        logfile_name_label = ttk.Label(self.top, text="Logfile Name : ")
        logfile_name_input = ttk.Entry(self.top, textvariable=self.logFileName)

        self.contiki_path_input.insert(0, "/home/mckkk119/CNLAB_EV/contiki-ng")
        self.node_cnt_input.insert(0, "4")
        node_id_input.insert(0, "1")
        self.data_cnt_input.insert(0, "100")
        node_type_input.insert(0, "AP")

        contiki_path_label.place(x=10, y=20)
        self.contiki_path_input.place(x=130, y=15, width=260, height=35)
        node_cnt_label.place(x=10, y=60)
        self.node_cnt_input.place(x=130, y=55, width=260, height=35)
        node_id_label.place(x=10, y=100)
        node_id_input.place(x=130, y=95, width=260, height=35)
        node_type_label.place(x=10, y=140)
        node_type_input.place(x=130, y=135, width=260, height=35)
        data_cnt_label.place(x=10, y=175)
        self.data_cnt_input.place(x=130, y=170, width=260, height=35)
        reset_check.place(x=410, y=10, height=35)
        debugging_check.place(x=550, y=10, height=35)
        logfile_name_label.place(x=410, y=50)
        logfile_name_input.place(x=530, y=45, width=260, height=35)

        uploadButton = tk.Button(self.top, text="Upload to node", command=self.upload)
        uploadButton.place(x=10, y=215, width=380, height=70)

        self.uploadLog = tk.Listbox(self.top)
        self.uploadLog.place(x=10, y=300, width=760, height=260)

        vscroll = ttk.Scrollbar(self.top, orient="vertical", bootstyle="default")
        hscroll = ttk.Scrollbar(self.top, orient="horizontal", bootstyle="default")
        vscroll.config(command=self.uploadLog.yview)
        hscroll.config(command=self.uploadLog.xview)
        vscroll.place(x=770, y=300, width=20, height=260)
        hscroll.place(x=10,y=560, width=760, height=20)
        self.uploadLog.config(xscrollcommand=hscroll.set, yscrollcommand=vscroll.set)

    def upload(self):
        if not self.isDebug.get():
            try:
                serial.Serial(PORT, BAUD_RATE).close()
            except serial.serialutil.SerialException:
                msgbox.showwarning("ERROR", "Device is not ready.\n or please execute with root permission.")
                return
        if self.contiki_path.get()=="" or self.node_cnt.get()=="" \
            or self.node_id.get()=="" or self.node_type.get()=="" or self.data_cnt.get()=="":
            msgbox.showwarning("ERROR", "Make sure all boxes are filled.")
            return
        if self.node_id.get() > self.node_cnt.get():
             msgbox.showwarning("ERROR", f"Node ID {self.node_id.get()} is bigger than node cnt {self.node_cnt.get()}.")
             return
        try:
            content = ""
            with open(self.contiki_path.get()+"/os/contiki-main.c", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.find("#define NODE_ID")!=-1:
                        content += f"#define NODE_ID {self.node_id.get()}\n"
                    elif line.find("#define NODE_TYPE")!=-1:
                        content += f"#define NODE_TYPE {self.node_type.get()}\n"
                    else:
                        content += line
            with open(self.contiki_path.get()+"/os/contiki-main.c", "w") as f:
                f.write(content)

            content = ""
            with open(self.contiki_path.get()+"/os/net/mac/tsch/cnlab-protocol.c", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.find("#define NUMBER_OF_DATA ")!=-1:
                        content += f"#define NUMBER_OF_DATA {self.data_cnt.get()}    //---mkkim0723: MUSTBE = NUMBER_OF_SENSOR_DATA in node.c\n"
                    else:
                        content += line
            with open(self.contiki_path.get()+"/os/net/mac/tsch/cnlab-protocol.c", "w") as f:
                f.write(content)

            content = ""
            with open(self.contiki_path.get()+"/../CNLAB_PROTOCOL_DOWNLINK/node.c", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.find("#define NUMBER_OF_SENSOR_DATA")!=-1:
                        content += f"#define NUMBER_OF_SENSOR_DATA  {self.data_cnt.get()}        //---MUSTBE = NUMBER_OF_DATA in cnlab-protocol.c\n"
                    else:
                        content += line
            with open(self.contiki_path.get()+"/../CNLAB_PROTOCOL_DOWNLINK/node.c", "w") as f:
                f.write(content)
            
            content = ""
            with open(self.contiki_path.get()+"/os/sys/node-id.h", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.find("#define NUMBER_OF_NODES  ")!=-1:
                        content += f"#define NUMBER_OF_NODES  {self.node_cnt.get()}\n"
                    else:
                        content += line
            with open(self.contiki_path.get()+"/os/sys/node-id.h", "w") as f:
                f.write(content)
        except FileNotFoundError:
            msgbox.showwarning("ERROR", "Contiki-NG Path is wrong.")
            return
        cwd = f"{self.contiki_path.get()}" + "/../CNLAB_PROTOCOL_DOWNLINK" + ("_AP" if self.node_type.get()=="AP" else "")
        cmd = ["make", "TARGET=zoul"]
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1, text=True, cwd=cwd) as proc:
            while True:
                line = proc.stdout.readline()
                if not line:break
                self.appendLog(line)
        cmd = ["sudo", "make", "TARGET=zoul", "ap.upload" if self.node_type.get()=="AP" else "node.upload", "PORT=/dev/ttyUSB0"]
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1, text=True, cwd=cwd) as proc:
            while True:
                line = proc.stdout.readline()
                if not line:break
                self.appendLog(line)
        self.node_cnt_input["state"] = "disabled"
        self.contiki_path_input["state"] = "disabled"
        self.data_cnt_input["state"] = "disabled"
    def appendLog(self, line):
        self.uploadLog.insert(tk.END, line)
        self.uploadLog.update()
        self.uploadLog.see(tk.END)

    def resetLayoutButtonPressed(self):
        self.ld.neighborPos = nx.spring_layout(self.ld.entireG)
        if self.mode.get()==0:
            makeGraph.makeRootGraph(self.ld, self.dg.selectedNode)
            self.dg.drawRootGraph()
        elif self.mode.get()==1:
            makeGraph.makeNeighborGraph(self.ld, self.dg.selectedNode)
            self.dg.drawNeighborGraph()
        elif self.mode.get()==3:
            self.dg.drawNetworkGraph()
        else:
            self.dg.drawRootGraph()

    def activateButtonPressed(self):
        if self.isDebug.get(): 
            msgbox.showwarning("ERROR", "Can't use on DEBUG MODE.")
            return
        if self.ld.activate[self.dg.selectedNode]:
            self.activateButton["text"] = "Activate Node"
            self.ld.activate[self.dg.selectedNode] = False
            self.ld.fd.write(f"VS-OFF {self.dg.selectedNode}".encode()+b"\x7F")
        else:
            self.activateButton["text"] = "Deactivate Node"
            self.ld.activate[self.dg.selectedNode] = True
            self.ld.fd.write(f"VS-ON {self.dg.selectedNode}".encode()+b"\x7F")
        if self.mode.get()==0:
            self.dg.drawRootGraph()
        elif self.mode.get()==1:
            self.dg.drawNeighborGraph()
        elif self.mode.get()==3:
            self.dg.drawNetworkGraph()
        else:
            self.dg.drawRootGraph()

        

    def drawInfo(self):
        self.nodeIDAx.clear()
        self.nodeG.clear()
        self.nodeG.add_node(self.dg.selectedNode)

        I1 = netgraph.InteractiveGraph(self.nodeG,
                                node_labels=dict(zip(self.nodeG.nodes,[self.dg.selectedNode])),
                                node_label_bbox=dict(fc="lightgreen", ec="black", boxstyle="square", lw=3),
                                node_size=6,
                                node_color={node:"tab:"+(self.ld.NODE_COLOR[self.ld.node_type[node]]) for node in self.nodeG.nodes},
                                ax=self.nodeIDAx,
        )
        label = self.ld.NODE_TYPE[self.ld.node_type[self.dg.selectedNode]]
        self.nodeTypeLabel["text"] = "VSENSOR" if label.startswith("VSENSOR") else label
        self.nodeIDCanvas.draw_idle()

if __name__ == "__main__":
    TkinterUI()
