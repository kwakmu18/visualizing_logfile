import tkinter as tk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import makeGraph
import netgraph
from logData import ld

fig = None
ax1, ax2 = None, None
canvas = None
I = None
node_color,weight,nodecolor = None, None, None
prrText = None
originalX,originalY,selectedNode = None,None,None
window = None
node_number = None
font = ("Pretendard", 12)
label = None

def clickEvent(event):
    global originalX,originalY,selectedNode
    for node in ld.neighborPos.keys():
        x,y = ld.neighborPos[node]
        if (x-event.xdata)**2 + (y-event.ydata)**2 <= 0.02:
            originalX,originalY,selectedNode=x,y,node
            return

def releaseEvent(event):
    global originalX,originalY,selectedNode,node_number
    if selectedNode==None or mode.get()==2:return
    if (originalX-event.xdata)**2 + (originalY-event.ydata)**2>0.0005:return
    makeGraph.makeNeighborGraph(int(selectedNode))
    node_number = int(selectedNode)
    changeLabel(int(selectedNode))
    if mode.get()==0:
        makeGraph.makeRootGraph(int(selectedNode))
        drawRootGraph(ld.rootG)
    else:drawNeighborGraph()
    originalX,originalY,selectedNode = None,None,None
    return

def changeLabel(index):
    global label
    if index==ld.ROOT_NODE: label["text"]="map\n \n "
    else:
        label["text"] = f"{index}번 노드\n{ld.NODE_TYPE[ld.node_type[index]]}\n"
        label["text"] += (f"PRR = {ld.prr[index]}") if ld.node_type[index] == 2 else " "

def start():
    global fig,ax1,ax2,canvas,I,node_color,weight,nodecolor,prrText
    node_color = nx.get_node_attributes(ld.neighborG, 'color').values()
    weight = nx.get_edge_attributes(ld.neighborG, 'weight')
    nodecolor = {node:"tab:"+nodecolor for node,nodecolor in zip(ld.neighborG.nodes, node_color)}
    I = netgraph.InteractiveGraph(ld.neighborG,
                              edge_layout='curved',
                              edge_layout_kwargs=dict(k=0.025),
                              node_layout=ld.neighborPos,
                              node_labels=dict(zip(ld.neighborG.nodes,ld.neighborG.nodes)),
                              node_label_bbox=dict(fc="lightgreen", ec="black", boxstyle="square", lw=3),
                              node_size=3   ,
                              node_color=nodecolor,
                              edge_labels=weight,
                              scale=(3,3),
                              annotations = {x:ld.annotation[x] for x in ld.neighborG.edges},
                              edge_width = 1,
                              arrows = True,
                              ax=ax2,
    )
    fig.canvas.mpl_connect('button_press_event', clickEvent)
    fig.canvas.mpl_connect('button_release_event', releaseEvent)
    node_proxy_artists = []
    for i in range(1,len(ld.NODE_COLOR)):
        proxy = plt.Line2D(
            [], [],
            linestyle='None',
            color=ld.NODE_COLOR[i],
            marker='o',
            markersize=8,
            label=ld.NODE_TYPE[i]
        )
        node_proxy_artists.append(proxy)

    node_legend = ax1.legend(handles=node_proxy_artists, loc='upper left', title='Nodes')
    ax1.add_artist(node_legend)
    ax1.set_axis_off()
    prrText = ax1.text(0.5, 0.5, "")
    canvas = FigureCanvasTkAgg(fig, master=frame2)
    canvas.draw()

    # Canvas 위젯 생성 및 그래프 출력
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack()
    window.mainloop()   

def drawNeighborGraph():
    global fig,ax1,ax2,canvas,I,node_color,weight,nodecolor
    ax2.clear()
    node_color = nx.get_node_attributes(ld.neighborG, 'color').values()
    weight = nx.get_edge_attributes(ld.neighborG, 'weight')
    nodecolor = {node:"tab:"+nodecolor for node,nodecolor in zip(ld.neighborG.nodes, node_color)}
    I = netgraph.InteractiveGraph(ld.neighborG,
                              edge_layout='curved',
                              edge_layout_kwargs=dict(k=0.025),
                              node_layout=ld.neighborPos,
                              node_labels=dict(zip(ld.neighborG.nodes,ld.neighborG.nodes)),
                              node_label_bbox=dict(fc="lightgreen", ec="black", boxstyle="square", lw=3),
                              node_size=3   ,
                              node_color=nodecolor,
                              edge_labels=weight,
                              scale=(3,3),
                              annotations = {x:ld.annotation[x] for x in ld.neighborG.edges},
                              edge_width = 1,
                              arrows = True,
                              ax=ax2,
    )
    canvas.draw()
    return

def drawRootGraph(G:nx.Graph):
    global fig,ax1,ax2,canvas,I,node_color,weight,nodecolor
    ax2.clear()
    node_color = nx.get_node_attributes(G, 'color').values()
    weight = nx.get_edge_attributes(G, 'weight')
    nodecolor = {node:"tab:"+nodecolor for node,nodecolor in zip(G.nodes, node_color)}
    I = netgraph.InteractiveGraph(G,
                              node_layout=ld.neighborPos,
                              node_labels=dict(zip(G.nodes,G.nodes)),
                              node_label_bbox=dict(fc="lightgreen", ec="black", boxstyle="square", lw=3),
                              node_size=3   ,
                              node_color=nodecolor,
                              edge_labels=weight,
                              scale=(100,100),
                              annotations = {x:ld.annotation[x] for x in G.edges},
                              edge_width = 1,
                              arrows=True,
                              ax=ax2
    )
    canvas.draw()
    return
    

def radioButtonPressed():
    if mode.get()==0:
        makeGraph.makeRootGraph(node_number)
        drawRootGraph(ld.rootG)
    elif mode.get()==1:
        makeGraph.makeNeighborGraph(node_number)
        drawNeighborGraph()
    else:
        drawRootGraph(ld.entireG)
    return

def terminate():
    ld.event.set()
    window.destroy()

def init():
    global window, mode, frame1, frame2, fig, ax1, ax2, node_number, label
    window = tk.Tk()
    window.protocol("WM_DELETE_WINDOW", terminate)
    window.title("NetworkX Graph")
    mode = tk.IntVar(value=2) # root vs neighbor

    node_number = 2

    frame1 = tk.Frame(window, width=1000, height=50)
    frame1.pack(side="top")

    frame2 = tk.Frame(window, width=1000)
    frame2.pack(side="bottom")
    label = tk.Label(frame1, text="map\n \n ", font=font)
    label.place(x=450, y=0, width=100, height=50)

    modeRadio1 = tk.Radiobutton(frame1, text="root node", font=font, variable=mode, value=0, command=radioButtonPressed, )
    modeRadio1.place(x=780, y=25)
    modeRadio2 = tk.Radiobutton(frame1, text="neighbor", font=font, variable=mode, value=1, command=radioButtonPressed)
    modeRadio2.place(x=880, y=25)
    modeRadio2 = tk.Radiobutton(frame1, text="entire map", font=font, variable=mode, value=2, command=radioButtonPressed)
    modeRadio2.place(x=680, y=25)

    ld.neighborG = ld.G
    ld.neighborPos = ld.pos#nx.spring_layout(ld.neighborG)

    fig, (ax1,ax2) = plt.subplots(1,2,width_ratios=[1,10],figsize=(18,10))