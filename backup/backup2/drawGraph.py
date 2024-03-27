import tkinter as tk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import makeGraph
import netgraph
from matplotlib import gridspec

class DrawGraph:
    def __init__(self, ld):
        self.ld = ld
        self.ld.dg = self
        self.selectedNode = 1
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

        self.fig = plt.figure(figsize=(15,10))
        spec = gridspec.GridSpec(ncols=2, nrows=1, width_ratios=[1,5])
        self.ax1 = self.fig.add_subplot(spec[0])
        self.ax2 = self.fig.add_subplot(spec[1])
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

        self.fig.canvas.mpl_connect('button_press_event', self.clickEvent)
        self.fig.canvas.mpl_connect('button_release_event', self.releaseEvent)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame2)
        self.canvas.draw()

        #Canvas 위젯 생성 및 그래프 출력
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack()
        self.window.mainloop()


    def clickEvent(self, event):
        for node in self.ld.neighborPos.keys():
            x,y = self.ld.neighborPos[node]
            if (x-event.xdata)**2 + (y-event.ydata)**2<=0.02:
                self.originalX = x
                self.originalY = y
                self.selectedNode = int(node)
                return

    def releaseEvent(self, event):
        if self.selectedNode==None or self.mode.get()==2: return
        if (self.originalX - event.xdata)**2 + (self.originalY - event.ydata)**2 > 0.0005:return
        makeGraph.makeNeighborGraph(self.ld, self.selectedNode)
        if self.mode.get()==0:
            makeGraph.makeRootGraph(self.ld, self.selectedNode)
            self.drawRootGraph()
        else:
            self.drawNeighborGraph()
        
        self.changeLabel()
        self.originalX = None
        self.originalY = None

    def changeLabel(self):
        if self.selectedNode == None: return
        self.nodeInfoLabel["text"] = f"{self.selectedNode}번 노드\n"
        self.nodeInfoLabel["text"] += f"{self.ld.NODE_TYPE[self.ld.node_type[self.selectedNode]]}\n"
        if self.ld.NODE_TYPE[self.ld.node_type[self.selectedNode]]=="Sensor" and self.selectedNode in self.ld.prr.keys():
            self.nodeInfoLabel["text"] += f"{int(self.ld.prr[self.selectedNode][0]*10000/self.ld.prr[self.selectedNode][1])-1}"
            self.nodeInfoLabel["text"] += f"({self.ld.prr[self.selectedNode][0]}/{self.ld.prr[self.selectedNode][1]})"

    def drawNeighborGraph(self):
        self.ax2.clear()
        self.node_color = nx.get_node_attributes(self.ld.neighborG, 'color').values()
        self.weight = nx.get_edge_attributes(self.ld.neighborG, 'weight')
        self.nodecolor = {node:"tab:"+nodecolor for node,nodecolor in zip(self.ld.neighborG.nodes, self.node_color)}
        self.I = netgraph.InteractiveGraph(self.ld.neighborG,
                                edge_layout='curved',
                                edge_layout_kwargs=dict(k=0.025),
                                node_layout=self.ld.neighborPos,
                                node_labels=dict(zip(self.ld.neighborG.nodes,self.ld.neighborG.nodes)),
                                node_label_bbox=dict(fc="lightgreen", ec="black", boxstyle="square", lw=3),
                                node_size=3   ,
                                node_color=self.nodecolor,
                                edge_labels=self.weight,
                                scale=(3,3),
                                annotations = {x:self.ld.annotation[x] for x in self.ld.neighborG.edges},
                                edge_width = 1,
                                arrows = True,
                                ax=self.ax2,
        )
        self.canvas.draw()
        return

    def drawRootGraph(self):
        G = self.ld.rootG if self.mode.get()==0 else self.ld.entireG
        self.ax2.clear()
        self.node_color = nx.get_node_attributes(G, 'color').values()
        self.weight = nx.get_edge_attributes(G, 'weight')
        self.nodecolor = {node:"tab:"+nodecolor for node,nodecolor in zip(G.nodes, self.node_color)}
        self.I = netgraph.InteractiveGraph(G,
                                node_layout=self.ld.neighborPos,
                                node_labels=dict(zip(G.nodes,G.nodes)),
                                node_label_bbox=dict(fc="lightgreen", ec="black", boxstyle="square", lw=3),
                                node_size=3   ,
                                node_color=self.nodecolor,
                                edge_labels=self.weight,
                                scale=(100,100),
                                annotations = {x:self.ld.annotation[x] for x in G.edges},
                                edge_width = 1,
                                arrows=True,
                                ax=self.ax2
        )
        self.canvas.draw()
        return

    def radioButtonPressed(self):
        if self.mode.get()==0:
            makeGraph.makeRootGraph(self.ld, self.selectedNode)
            self.drawRootGraph()
        elif self.mode.get()==1:
            makeGraph.makeNeighborGraph(self.ld, self.selectedNode)
            self.drawNeighborGraph()
        else:
            self.drawRootGraph()
            self.nodeInfoLabel["text"] = "Entire Map"
        return

    def terminate(self):
        self.ld.event.set()
        self.window.destroy()