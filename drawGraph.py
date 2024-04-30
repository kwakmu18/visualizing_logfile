import networkx as nx
import makeGraph
import netgraph
class DrawGraph:
    def __init__(self, main, ld):
        self.ld = ld
        self.ld.dg = self
        self.selectedNode = 2
        self.main = main

    def clickEvent(self, event):
        for node in self.ld.neighborPos.keys():
            x,y = self.ld.neighborPos[node]
            if (x-event.xdata)**2 + (y-event.ydata)**2<=0.02:
                self.originalX = x
                self.originalY = y
                self.selectedNode = int(node)
                return

    def releaseEvent(self, event):
        if self.selectedNode==None: return
        if self.ld.NODE_TYPE[self.ld.node_type[self.selectedNode]] in ["VSENSOR-ACTIVATED", "SENSOR"]:
            self.main.activateButton["state"] = "active"
            self.main.prrProgressBar.configure(mask="{}%"+f"({self.ld.prr[self.selectedNode][0]}/{self.ld.prr[self.selectedNode][1]})")
            self.ld.maxSequence.set(int(self.ld.prr[self.selectedNode][0]/self.ld.prr[self.selectedNode][1]*100))
            if self.ld.activate[self.selectedNode]:
                self.main.activateButton["text"] = "Deactivate Node"
            else:
                self.main.activateButton["text"] = "Activate Node"
        else:
            self.main.activateButton["state"] = "disabled"
            self.ld.maxSequence.set(0)
            self.main.prrProgressBar.configure(mask="{}%"+f"(0/0)")
        self.main.drawInfo()
        if self.main.mode.get()==2 or self.main.mode.get()==3: return
        if (self.originalX - event.xdata)**2 + (self.originalY - event.ydata)**2 > 0.0005:return
        makeGraph.makeNeighborGraph(self.ld, self.selectedNode)
        if self.main.mode.get()==0:
            makeGraph.makeRootGraph(self.ld, self.selectedNode)
            self.drawRootGraph()
        else:
            self.drawNeighborGraph()

        
        self.originalX = None
        self.originalY = None

    def drawNeighborGraph(self):
        self.main.ax2.clear()
        self.main.fig.canvas.mpl_connect('button_press_event', self.clickEvent)
        self.main.fig.canvas.mpl_connect('button_release_event', self.releaseEvent)
        self.I = netgraph.InteractiveGraph(self.ld.neighborG,
                                node_layout=self.ld.neighborPos,
                                node_labels=dict(zip(self.ld.neighborG.nodes,self.ld.neighborG.nodes)),
                                node_label_bbox=dict(fc="lightgreen", ec="black", boxstyle="square", lw=3),
                                node_size=6   ,
                                node_color={node:"tab:"+(self.ld.NODE_COLOR[self.ld.node_type[node]] if self.ld.activate[node] else "grey") for node in self.ld.neighborG.nodes},
                                edge_labels=nx.get_edge_attributes(self.ld.neighborG, 'weight'),
                                edge_label_position=0.8,
                                edge_label_fontdict = {"fontsize":9.5,"bbox":{"alpha":0}},
                                edge_color=nx.get_edge_attributes(self.ld.neighborG, 'color'),
                                scale=(3,3),
                                annotations = {x:self.ld.annotation[x] for x in self.ld.neighborG.edges},
                                edge_width = 1,
                                arrows = True,
                                ax=self.main.ax2,
        )
        self.main.canvas.draw_idle()
        return

    def drawRootGraph(self):
        G = self.ld.rootG if self.main.mode.get()==0 else self.ld.entireG
        self.main.fig.canvas.mpl_connect('button_press_event', self.clickEvent)
        self.main.fig.canvas.mpl_connect('button_release_event', self.releaseEvent)
        self.main.ax2.clear()
        self.I = netgraph.InteractiveGraph(G,
                                node_layout=self.ld.neighborPos,
                                node_labels=dict(zip(G.nodes,G.nodes)),
                                node_label_bbox=dict(fc="lightgreen", ec="black", boxstyle="square", lw=3),
                                node_size=6   ,
                                node_color={node:"tab:"+(self.ld.NODE_COLOR[self.ld.node_type[node]] if self.ld.activate[node] else "grey") for node in G.nodes},
                                edge_labels=nx.get_edge_attributes(G, 'weight'),
                                edge_label_position=0.8,
                                edge_label_fontdict = {"fontsize":9.5,"bbox":{"alpha":0}},
                                edge_color=nx.get_edge_attributes(G, 'color'),
                                scale=(3,3),
                                annotations = {x:self.ld.annotation[x] for x in G.edges},
                                edge_width = 1,
                                arrows=True,
                                ax=self.main.ax2
        )
        self.main.canvas.draw_idle()
        return

    def drawNetworkGraph(self):
        self.main.fig.canvas.mpl_connect('button_press_event', self.clickEvent)
        self.main.fig.canvas.mpl_connect('button_release_event', self.releaseEvent)
        self.main.ax2.clear()
        self.I = netgraph.InteractiveGraph(self.ld.networkG,
                                node_layout=self.ld.neighborPos,
                                node_labels=dict(zip(self.ld.networkG.nodes,self.ld.networkG.nodes)),
                                node_label_bbox=dict(fc="lightgreen", ec="black", boxstyle="square", lw=3),
                                node_size=6   ,
                                node_color={node:"tab:"+(self.ld.NODE_COLOR[self.ld.node_type[node]] if self.ld.activate[node] else "grey") for node in self.ld.networkG.nodes},
                                edge_labels=nx.get_edge_attributes(self.ld.networkG, 'weight'),
                                edge_label_position=0.8,
                                edge_label_fontdict = {"fontsize":9.5,"bbox":{"alpha":0}},
                                edge_color=nx.get_edge_attributes(self.ld.networkG, 'color'),
                                scale=(3,3),
                                annotations = {x:self.ld.annotation[x] for x in self.ld.networkG.edges},
                                edge_width = 1,
                                arrows=True,
                                ax=self.main.ax2
        )
        self.main.canvas.draw_idle()
        return