import tkinter as tk
import tkinter.ttk as ttk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logData
from math import *

def makeRootGraph(index):
    logData.rootG.clear()
    logData.rootG.clear_edges()
    A, B = index, logData.parent[index]
    while True:
        if B==0:break
        logData.rootG.add_weighted_edges_from([(str(A), str(B), "In : %d, Out : %d"%(logData.incoming[B][A], logData.outgoing[B][A])),
                (str(B), str(A),"")])
        A, B = B, logData.parent[B]

def makeNeighborGraph(index):
    logData.neighborG.clear()
    logData.neighborG.clear_edges()
    logData.neighborG.add_node(str(index), pos=(0,0), name=index,
                               color=logData.NODE_COLOR[logData.node_type[index]], edge_color=logData.NODE_EDGECOLOR[logData.node_type[index]])
    cnt = 2*pi/(logData.child_cnt[index])
    not_child_cnt = 0
    for i in range(1, logData.NODE_CNT+1):
        if i==index: continue
        if logData.outgoing[index][i]==0 or logData.incoming[index][i]==0:
            logData.neighborG.add_node(str(i), pos=(-1.5,not_child_cnt), name=i,
                                       color=logData.NODE_COLOR[logData.node_type[i]], edge_color=logData.NODE_EDGECOLOR[logData.node_type[i]])
            not_child_cnt+=0.2
            continue
        logData.neighborG.add_node(str(i), pos=(cos(cnt), sin(cnt)), name=i,
                                       color=logData.NODE_COLOR[logData.node_type[i]], edge_color=logData.NODE_EDGECOLOR[logData.node_type[i]])
        logData.neighborG.add_weighted_edges_from(
                [(str(index), str(i), "In : %d, Out : %d"%(logData.incoming[index][i], logData.outgoing[index][i])),
                 (str(i), str(index),"")])
        cnt+=2*pi/(logData.child_cnt[index])
    logData.neighborPos = nx.get_node_attributes(logData.neighborG, "pos")

