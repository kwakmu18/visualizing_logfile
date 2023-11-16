import tkinter as tk
import tkinter.ttk as ttk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logData, makeGraph

def nodeSelected(event):
    global canvas_widget, label, node_number
    if event.button == 1:
        for key in logData.pos.keys():
            nodex,nodey = logData.pos[key]
            if (nodex-event.xdata)**2+(nodey-event.ydata)**2<=0.002:
                changeLabel(int(key))
                if key=="1":
                    node_number=1
                    drawGraph(logData.G)
                    return
                elif int(key)==node_number:
                    return
                node_number=int(key)
                if mode2.get()==0:
                    makeGraph.makeRootGraph(mode1, int(key))
                    drawGraph(logData.rootG)
                else:
                    makeGraph.makeNeighborGraph(mode1, int(key))
                    drawGraph(logData.neighborG)
                return

def changeLabel(index):
    global label
    if index==1: label["text"]="map\n \n "
    else:
        label["text"] = f"{index}번 노드\n{logData.TYPE_STR[logData.type[index]]}\n"
        label["text"] += (f"PRR = {logData.prr[index]}") if logData.type[index] == 2 else " "

def drawGraph(G):
    global canvas_widget

    plt.close()
    if canvas_widget!=None: canvas_widget.destroy()
    fig, ax = plt.subplots()
    fig.canvas.mpl_connect("button_press_event",nodeSelected)

    logData.rank_pos = {node: (logData.pos[node][0], logData.pos[node][1]+0.1) for node in G.nodes()}  # rank 라벨의 위치를 조정합니다.
    logData.rank_labels = {node: logData.ranks[int(node)] for node in G.nodes()}  # 'rank' 문자열을 제거하고 숫자만 표시합니다.
    nx.draw_networkx_edges(G, logData.pos)
    weight = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, logData.pos, edge_labels=weight)
    nx.draw_networkx_nodes(logData.G, logData.pos, node_color=logData.colors, edgecolors=logData.edge_colors)
    nx.draw_networkx_labels(logData.G, logData.pos)  # 원래의 노드 라벨을 그립니다.
    nx.draw_networkx_labels(G, logData.rank_pos, labels=logData.rank_labels, font_color='darkred')

    canvas = FigureCanvasTkAgg(fig, master=frame2)
    canvas.draw()

    # Canvas 위젯 생성 및 그래프 출력
    canvas_widget = canvas.get_tk_widget()
    canvas_widget["height"] = 1000
    canvas_widget["width"] = 1800
    canvas_widget.pack()

def radioButtonPressed():
    if node_number == 1:
        return
    if mode2.get()==0:
        makeGraph.makeRootGraph(mode1, node_number)
        drawGraph(logData.rootG)
    else:
        makeGraph.makeNeighborGraph(mode1, node_number)
        drawGraph(logData.neighborG)

# tkinter 윈도우 생성
window = tk.Tk()
window.title("NetworkX Graph")
mode1 = tk.IntVar() # upstream vs downstream
mode2 = tk.IntVar() # root vs neighbor

node_number = 1
canvas_widget, canvas_widget2 = None, None
font = ("Pretendard", 12)
# 그래프를 그릴 Figure 객체 생성

frame1 = tk.Frame(window, width=1000, height=50)
frame1.pack(side="top")

frame2 = tk.Frame(window)
frame2.pack(side="bottom")

label = tk.Label(frame1, text="map\n \n ", font=font)
label.place(x=450, y=0, width=100, height=50)

modeRadio1 = tk.Radiobutton(frame1, text="upstream", variable=mode1, 
                        value=0, command=radioButtonPressed, font=font)
modeRadio1.place(x=780, y=0, width=100, height=25)
modeRadio2 = tk.Radiobutton(frame1, text="downstream", variable=mode1,
                        value=1, command=radioButtonPressed, font=font)
modeRadio2.place(x=880,y=0, width=120, height=25)
modeRadio3 = tk.Radiobutton(frame1, text="root node", font=font, variable=mode2, value=0, command=radioButtonPressed)
modeRadio3.place(x=780, y=25)
modeRadio4 = tk.Radiobutton(frame1, text="neighbor", font=font, variable=mode2, value=1, command=radioButtonPressed)
modeRadio4.place(x=880, y=25)

# tkinter 메인 루프 실행
drawGraph(logData.G)
window.mainloop()