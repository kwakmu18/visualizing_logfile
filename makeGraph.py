import logData

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
    logData.neighborG.add_node(str(index), name=index,
                               color=logData.NODE_COLOR[logData.node_type[index]], edge_color=logData.NODE_EDGECOLOR[logData.node_type[index]])
    for i in range(1, logData.NODE_CNT+1):
        logData.neighborG.add_node(str(i), name=i,
                                       color=logData.NODE_COLOR[logData.node_type[i]], edge_color=logData.NODE_EDGECOLOR[logData.node_type[i]])
        if logData.outgoing[index][i]==0 or logData.incoming[index][i]==0:
            continue
        logData.neighborG.add_edge(str(index), str(i), weight=
                                                        "%d/%d"%(logData.incoming[index][i], logData.outgoing[index][i]))