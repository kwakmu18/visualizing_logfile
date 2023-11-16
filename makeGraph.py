import tkinter as tk
import tkinter.ttk as ttk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logData

def makeRootGraph(mode, index):
    logData.rootG.clear()
    logData.rootG.clear_edges()
    if mode.get()==0:
        A, B = index, logData.parent[index]
        while True:
            if B==0:break
            logData.rootG.add_weighted_edges_from([(str(A), str(B), logData.incoming[B][A])])
            A, B = B, logData.parent[B]
    else: 
        A, B = logData.parent[index], index
        while True:
            if A==0:break
            logData.rootG.add_weighted_edges_from([(str(A), str(B), logData.outgoing[A][B])])
            A, B = logData.parent[A], A

def makeNeighborGraph(mode, index):
    logData.neighborG.clear()
    logData.neighborG.clear_edges()
    for i in range(1, logData.NODE_CNT+1):
        if logData.outgoing[i][index]==0 or logData.incoming[i][index]==0: continue
        if mode.get()==0:
            logData.neighborG.add_weighted_edges_from([(str(index), str(i),
                                                        "In : %d, Out : %d"%(logData.incoming[i][index], logData.outgoing[i][index]))])
        else:
            logData.neighborG.add_weighted_edges_from([(str(i), str(index), logData.outgoing[i][index])])

