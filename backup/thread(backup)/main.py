import drawGraph, logData, makeGraph
import threading, os, serial, networkx as nx
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import gridspec

        # ------------------------------------------------- Constants ----------------------------------------------- #
FILENAME = "log.txt"
PORT = "/dev/ttyUSB0"
BAUD_RATE = 57600
DEBUG_MODE = True
        # ------------------------------------------------- Constants ----------------------------------------------- #

class TkinterUI:
    def __init__(self):
        # ------------------------------------------------ Configure UI ------------------------------------------------ #
        self.window = tk.Tk()
        self.font = ("Pretendard", 12)
        self.mode = tk.IntVar(value=2)

        self.window.geometry("1920x1080")
        self.window.protocol("WM_DELETE_WINDOW", self.terminate)
        self.window.title("NetworkX Graph")

        self.frame1 = tk.Frame(self.window) # button & node info
        self.frame1.place(x=0, y=0, width=400, height=300)

        self.frame2 = tk.Frame(self.window) # graph
        self.frame2.place(x=400, y=0, width=1520, height=1080)

        self.frame3 = tk.Frame(self.window) # log
        self.frame3.place(x=0, y=300, width=400, height=780)

        self.vscroll = tk.Scrollbar(self.frame3, orient="vertical")
        self.hscroll = tk.Scrollbar(self.frame3, orient="horizontal")
        self.lbox = tk.Listbox(self.frame3, xscrollcommand=self.hscroll.set, yscrollcommand=self.vscroll.set, width=200, height=500)
        self.vscroll.config(command=self.lbox.yview)
        self.hscroll.config(command=self.lbox.xview)
        self.lbox.pack(); self.vscroll.pack(side="right", fill="y"); self.hscroll.pack()

        self.modeRadio1 = tk.Radiobutton(self.frame1, text="root node", font=self.font, variable=self.mode, value=0, command=self.radioButtonPressed)
        self.modeRadio1.place(x=50, y=275)
        self.modeRadio2 = tk.Radiobutton(self.frame1, text="neighbor", font=self.font, variable=self.mode, value=1, command=self.radioButtonPressed)
        self.modeRadio2.place(x=150, y=275)
        self.modeRadio3 = tk.Radiobutton(self.frame1, text="entire map", font=self.font, variable=self.mode, value=2, command=self.radioButtonPressed)
        self.modeRadio3.place(x=250, y=275)

        self.nodeInfoLabel = tk.Label(self.frame1, text="Entire Map", font=self.font)
        self.nodeInfoLabel.place(x=170, y=10)

        self.startButton = tk.Button(self.frame1, text="START", font=self.font, command=self.startButtonPressed)
        self.menuButton = tk.Menubutton(self.frame1, text="Menu", font=self.font, relief="raised")
        self.resetLayoutButton = tk.Button(self.frame1, text="Reset Layout", font=self.font, command=self.resetLayoutButtonPressed)
        self.activateButton = tk.Button(self.frame1, text="Deactivate Node", font=self.font, command = self.activateButtonPressed)

        self.startButton.place(x=0, y=100, width=200, height=50)
        self.menuButton.place(x=200, y=100, width=200, height=50)
        self.resetLayoutButton.place(x=0, y=150, width=200, height=50)
        self.activateButton.place(x=200, y=150, width=200, height=50)

        self.resetLayoutButton["state"] = "disabled"
        self.activateButton["state"] = "disabled"

        self.menu = tk.Menu(self.menuButton, tearoff=0, relief="flat")
        self.menu.add_command(label="Binary Upload", command=self.binaryUpload)
        self.menuButton["menu"] = self.menu

        self.isReset = tk.IntVar()
        self.resetLogCheckBox = tk.Checkbutton(self.frame1, text="reset log file", font=self.font, variable=self.isReset)
        self.resetLogCheckBox.place(x=0, y=225)
        # ------------------------------------------------ Configure UI ------------------------------------------------ #


        # ----------------------------------------------- Configure Canvas --------------------------------------------- #
        self.fig = plt.figure(figsize=(15,10))
        spec = gridspec.GridSpec(ncols=2, nrows=1, width_ratios=[1,5])
        self.ax1 = self.fig.add_subplot(spec[0])
        self.ax2 = self.fig.add_subplot(spec[1])

        self.ld = logData.LogData(FILENAME, self)
        self.dg = drawGraph.DrawGraph(self, self.ld)

        node_proxy_artists = []
        for i in range(1,len(self.ld.NODE_COLOR)):
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
        self.statusText = self.ax2.text(0.5, 0.5, "ZZIOT READY")

        self.fig.canvas.mpl_connect('button_press_event', self.dg.clickEvent)
        self.fig.canvas.mpl_connect('button_release_event', self.dg.releaseEvent)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame2)
        self.canvas.draw()

        #Canvas 위젯 생성 및 그래프 출력
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack()
        self.window.mainloop()

        # ----------------------------------------------- Configure Canvas --------------------------------------------- #

    def radioButtonPressed(self):
        if self.mode.get()==0:
            makeGraph.makeRootGraph(self.ld, self.dg.selectedNode)
            self.dg.drawRootGraph()
        elif self.mode.get()==1:
            makeGraph.makeNeighborGraph(self.ld, self.dg.selectedNode)
            self.dg.drawNeighborGraph()
        else:
            self.dg.drawRootGraph()
            self.nodeInfoLabel["text"] = "Entire Map"
        return

    def terminate(self):
        self.ld.event.set()
        self.window.destroy()

    def startButtonPressed(self):
        if self.isReset.get():
            os.remove(FILENAME)
            with open(FILENAME, "w") as f:
                pass
        if not DEBUG_MODE:
            try:
                serial.Serial(PORT, BAUD_RATE)
            except serial.serialutil.SerialException:
                msgbox.showwarning("ERROR", "Device is not ready.")
                return
            serialThread = threading.Thread(target=self.ld.serial)
        else:
            serialThread = threading.Thread(target=self.ld.logfile)
        serialThread.start()
        self.startButton["state"] = "disabled"
    def binaryUpload(self):
        top = tk.Toplevel(self.window)
        top.geometry("400x300")
        top.title("Binary Upload")
        self.contiki_path, self.node_cnt, self.actuator_id, self.node_id, self.node_type, self.data_cnt = \
            (tk.StringVar() for _ in range(6))
        contiki_path_label = tk.Label(top, text="Contiki-NG Path : ", font=self.font)
        contiki_path_input = tk.Entry(top, textvariable = self.contiki_path)
        node_cnt_label = tk.Label(top, text="Node Cnt : ", font=self.font)
        node_cnt_input = tk.Entry(top, textvariable=self.node_cnt)
        actuator_id_label = tk.Label(top, text="Actuator ID : ", font=self.font)
        actuator_id_input = tk.Entry(top, textvariable=self.actuator_id)
        node_id_label = tk.Label(top, text="Node ID : ", font=self.font)
        node_id_input = tk.Entry(top, textvariable=self.node_id)
        node_type_label = tk.Label(top, text="Node Type : ", font=self.font)
        node_type_input = ttk.Combobox(top, values=self.ld.NODE_TYPE[1:], textvariable=self.node_type)
        data_cnt_label = tk.Label(top, text="Data Cnt : ", font=self.font)
        data_cnt_input = tk.Entry(top, textvariable=self.data_cnt)

        contiki_path_input.insert(0, "/home/mckkk119/CNLAB_EV/contiki-ng")
        node_cnt_input.insert(0, "4")
        actuator_id_input.insert(0, "3")
        node_id_input.insert(0, "1")
        data_cnt_input.insert(0, "100")
        node_type_input.insert(0, "AP")

        contiki_path_label.place(x=10, y=10)
        contiki_path_input.place(x=120, y=10, width=260, height=25)
        node_cnt_label.place(x=10, y=45)
        node_cnt_input.place(x=120, y=45, width=260, height=25)
        actuator_id_label.place(x=10, y=80)
        actuator_id_input.place(x=120, y=80, width=260, height=25)
        node_id_label.place(x=10, y=115)
        node_id_input.place(x=120, y=115, width=260, height=25)
        node_type_label.place(x=10, y=150)
        node_type_input.place(x=120, y=150, width=260, height=25)
        data_cnt_label.place(x=10, y=185)
        data_cnt_input.place(x=120, y=185, width=260, height=25)

        uploadButton = tk.Button(top, text="Upload to node", command=self.upload, font=self.font)
        uploadButton.place(x=10, y=220, width=380, height=70)
    def upload(self):
        if not DEBUG_MODE:
            try:
                serial.Serial(PORT, BAUD_RATE)
            except serial.serialutil.SerialException:
                msgbox.showwarning("ERROR", "Device is not ready.")
                return
        if self.contiki_path.get()=="" or self.node_cnt.get()=="" or self.actuator_id.get()=="" \
            or self.node_id.get()=="" or self.node_type.get()=="" or self.data_cnt.get()=="":
            msgbox.showwarning("ERROR", "Make sure all boxes are filled.")
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
                    elif line.find("uint8_t actuator_node_id = ")!=-1:
                        content += f"uint8_t actuator_node_id = {self.actuator_id.get()};\n"
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
        
        if os.system(f"cd {self.contiki_path.get()}" + "CNLAB_PROTOCOL_DOWNLINK" + "_AP" if self.node_type.get()=="AP" else "" \
                  + "; make TARGET=zoul; make TARGET=zoul" + " ap.upload" if self.node_type.get()=="AP" else " node.upload" \
                    + " PORT=/dev/ttyUSB0")==0:
            msgbox.showinfo("Info", "Node Upload Success!")
        else:
            msgbox.showwarning("ERROR", "Node Upload Failed.")

    def resetLayoutButtonPressed(self):
        self.ld.neighborPos = nx.spring_layout(self.ld.entireG)
        self.dg.drawNeighborGraph()

    def activateButtonPressed(self):
        pass
TkinterUI()