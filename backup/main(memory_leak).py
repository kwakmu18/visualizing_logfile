import tkinter as tk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logData, makeGraph
import netgraph

originalX,originalY,selectedNode = None,None,None
def clickEvent(event):
    global originalX,originalY,selectedNode
    for node in logData.neighborPos.keys():
        x,y = logData.neighborPos[node]
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
        drawRootGraph(logData.rootG)
    else:drawNeighborGraph()
    originalX,originalY,selectedNode = None,None,None

def changeLabel(index):
    global label
    if index==logData.ROOT_NODE: label["text"]="map\n \n "
    else:
        label["text"] = f"{index}번 노드\n{logData.TYPE_STR[logData.node_type[index]]}\n"
        label["text"] += (f"PRR = {logData.prr[index]}") if logData.node_type[index] == 2 else " "

def drawNeighborGraph():
    global canvas_widget
    plt.close()
    if canvas_widget!=None: canvas_widget.destroy()
    fig, (ax1,ax2) = plt.subplots(1,2,width_ratios=[1,10],figsize=(18,10))
    node_color = nx.get_node_attributes(logData.neighborG, 'color').values()
    weight = nx.get_edge_attributes(logData.neighborG, 'weight')
    nodecolor = {node:"tab:"+nodecolor for node,nodecolor in zip(logData.neighborG.nodes, node_color)}
    I = netgraph.InteractiveGraph(logData.neighborG,
                              edge_layout='curved',
                              edge_layout_kwargs=dict(k=0.025),
                              node_layout=logData.neighborPos,
                              node_labels=dict(zip(logData.neighborG.nodes,logData.neighborG.nodes)),
                              node_label_bbox=dict(fc="lightgreen", ec="black", boxstyle="square", lw=3),
                              node_size=3   ,
                              node_color=nodecolor,
                              edge_labels=weight,
                              scale=(3,3),
                              annotations = {x:logData.annotation[x] for x in logData.neighborG.edges},
                              edge_width = 1,
                              arrows = True,
                              ax=ax2,
    )
    fig.canvas.mpl_connect('button_press_event', clickEvent)
    fig.canvas.mpl_connect('button_release_event', releaseEvent)
    node_proxy_artists = []
    for i in range(1,len(logData.NODE_COLOR)):
        proxy = plt.Line2D(
            [], [],
            linestyle='None',
            color=logData.NODE_COLOR[i],
            marker='o',
            markersize=8,
            label=logData.TYPE_STR[i]
        )
        node_proxy_artists.append(proxy)

    node_legend = ax1.legend(handles=node_proxy_artists, loc='upper left', title='Nodes')
    ax1.add_artist(node_legend)
    ax1.set_axis_off()
    canvas = FigureCanvasTkAgg(fig, master=frame2)
    canvas.draw()

    # Canvas 위젯 생성 및 그래프 출력
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack()
    window.mainloop()
    

def drawRootGraph(G:nx.Graph):
    global canvas_widget
    plt.close()
    if canvas_widget!=None: canvas_widget.destroy()
    fig, (ax1,ax2) = plt.subplots(1,2,width_ratios=[1,10],figsize=(18,10))
    node_color = nx.get_node_attributes(G, 'color').values()
    weight = nx.get_edge_attributes(G, 'weight')
    nodecolor = {node:"tab:"+nodecolor for node,nodecolor in zip(G.nodes, node_color)}
    I = netgraph.InteractiveGraph(G,
                              node_layout=logData.neighborPos,
                              node_labels=dict(zip(G.nodes,G.nodes)),
                              node_label_bbox=dict(fc="lightgreen", ec="black", boxstyle="square", lw=3),
                              node_size=3   ,
                              node_color=nodecolor,
                              edge_labels=weight,
                              scale=(100,100),
                              annotations = {x:logData.annotation[x] for x in G.edges},
                              edge_width = 1,
                              arrows=True,
                              ax=ax2
    )

    canvas = FigureCanvasTkAgg(fig, master=frame2)
    canvas.draw()
    fig.canvas.mpl_connect('button_press_event', clickEvent)
    fig.canvas.mpl_connect('button_release_event', releaseEvent)
    node_proxy_artists = []
    for i in range(1,len(logData.NODE_COLOR)):
        proxy = plt.Line2D(
            [], [],
            linestyle='None',
            color=logData.NODE_COLOR[i],
            marker='o',
            markersize=8,
            label=logData.TYPE_STR[i]
        )
        node_proxy_artists.append(proxy)

    node_legend = ax1.legend(handles=node_proxy_artists, loc='upper left', title='Nodes')
    ax1.add_artist(node_legend)
    ax1.set_axis_off()
    # Canvas 위젯 생성 및 그래프 출력
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack()
    window.mainloop()
    

def radioButtonPressed():
    if mode.get()==0:
        makeGraph.makeRootGraph(node_number)
        drawRootGraph(logData.rootG)
    elif mode.get()==1:
        makeGraph.makeNeighborGraph(node_number)
        drawNeighborGraph()
    else:
        drawRootGraph(logData.entireG)

# tkinter 윈도우 생성
window = tk.Tk()
window.title("NetworkX Graph")
mode = tk.IntVar(value=2) # root vs neighbor

node_number = 2
canvas_widget, canvas_widget2 = None, None
font = ("Pretendard", 12)
# 그래프를 그릴 Figure 객체 생성

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

# tkinter 메인 루프 실행
logData.neighborG = logData.G
logData.neighborPos = logData.pos#nx.spring_layout(logData.neighborG)
drawRootGraph(logData.entireG)
window.mainloop()