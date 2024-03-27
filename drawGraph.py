import networkx as nx
import makeGraph
import netgraph
class DrawGraph:
    def __init__(self, tk, ld):
        self.ld = ld
        self.ld.dg = self
        self.selectedNode = 1
        self.font = ("Pretendard", 12)
        self.tk = tk

    def clickEvent(self, event):
        for node in self.ld.neighborPos.keys():
            x,y = self.ld.neighborPos[node]
            if (x-event.xdata)**2 + (y-event.ydata)**2<=0.02:
                self.originalX = x
                self.originalY = y
                self.selectedNode = int(node)
                return

    def releaseEvent(self, event):
        if self.selectedNode==None or self.tk.mode.get()==2: return
        if (self.originalX - event.xdata)**2 + (self.originalY - event.ydata)**2 > 0.0005:return
        makeGraph.makeNeighborGraph(self.ld, self.selectedNode)
        if self.tk.mode.get()==0:
            makeGraph.makeRootGraph(self.ld, self.selectedNode)
            self.drawRootGraph()
        else:
            self.drawNeighborGraph()
        
        if self.ld.NODE_TYPE[self.ld.node_type[self.selectedNode]]=="VSENSOR":
            self.tk.activateButton["state"] = "active"
            if self.ld.activate[self.selectedNode]:
                self.tk.activateButton["text"] = "Deactivate Node"
            else:
                self.tk.activateButton["text"] = "Activate Node"
        else:
            self.tk.activateButton["state"] = "disabled"

        self.changeLabel()
        self.originalX = None
        self.originalY = None

    def changeLabel(self):
        if self.selectedNode == None: return
        try:
            self.tk.nodeInfoLabel["text"] = f"{self.selectedNode}번 노드\n"
            self.tk.nodeInfoLabel["text"] += f"{self.ld.NODE_TYPE[self.ld.node_type[self.selectedNode]]}\n"
            if self.ld.NODE_TYPE[self.ld.node_type[self.selectedNode]]=="VSENSOR" and self.selectedNode in self.ld.prr.keys():
                self.tk.nodeInfoLabel["text"] += f"{int(self.ld.prr[self.selectedNode][0]*10000/self.ld.prr[self.selectedNode][1])-1}"
                self.tk.nodeInfoLabel["text"] += f"({self.ld.prr[self.selectedNode][0]}/{self.ld.prr[self.selectedNode][1]})"
        except KeyError:
            self.changeLabel()

    def drawNeighborGraph(self):
        self.tk.ax2.clear()
        self.tk.fig.canvas.mpl_connect('button_press_event', self.clickEvent)
        self.tk.fig.canvas.mpl_connect('button_release_event', self.releaseEvent)
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
                                ax=self.tk.ax2,
        )
        self.tk.canvas.draw_idle()
        return

    def drawRootGraph(self):
        G = self.ld.rootG if self.tk.mode.get()==0 else self.ld.entireG
        self.tk.ax2.clear()
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
                                ax=self.tk.ax2
        )
        self.tk.canvas.draw_idle()
        return
