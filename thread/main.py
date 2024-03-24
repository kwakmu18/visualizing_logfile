import drawGraph, logData, makeGraph
import threading, os, serial, networkx as nx
import tkinter as tk
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
        self.stopButton = tk.Button(self.frame1, text="STOP", font=self.font, command=self.stopButtonPressed)
        self.resetLayoutButton = tk.Button(self.frame1, text="Reset Layout", font=self.font, command=self.resetLayoutButtonPressed)
        self.activateButton = tk.Button(self.frame1, text="Deactivate Node", font=self.font, command = self.activateButtonPressed)
        self.startButton.place(x=0, y=100, width=200, height=50)
        self.stopButton.place(x=200, y=100, width=200, height=50)
        self.resetLayoutButton.place(x=0, y=150, width=200, height=50)
        self.activateButton.place(x=200, y=150, width=200, height=50)
        self.stopButton["state"] = "disabled"
        self.resetLayoutButton["state"] = "disabled"
        self.activateButton["state"] = "disabled"
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
        self.stopButton["state"] = "active"
    def stopButtonPressed(self):
        self.ld.event.set()
    def resetLayoutButtonPressed(self):
        self.ld.neighborPos = nx.spring_layout(self.ld.entireG)
        self.dg.drawNeighborGraph()
    def activateButtonPressed(self):
        pass
TkinterUI()