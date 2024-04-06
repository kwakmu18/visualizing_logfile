def makeRootGraph(ld, index):
    #ld.rootG.clear()
    ld.rootG.clear_edges()
    A, B = index, ld.parent[index]
    while True:
        if B==0:break
        ld.rootG.add_weighted_edges_from([(str(A), str(B), ld.incoming[B][A])])#"%d/%d"%(ld.incoming[B][A] if ld.incoming[B][A]!=0 else ld.outgoing[A][B],
                                                                #         ld.outgoing[B][A] if ld.outgoing[B][A]!=0 else ld.incoming[A][B])),
                #(str(B), str(A),"")])
        A, B = B, ld.parent[B]

def makeNeighborGraph(ld, index):
    ld.neighborG.clear()
    ld.neighborG.clear_edges()
    ld.neighborG.add_node(str(index), name=index,
                               color=ld.NODE_COLOR[ld.node_type[index]], edge_color=ld.NODE_EDGECOLOR[ld.node_type[index]])
    for i in range(1, ld.node_cnt+1):
        ld.neighborG.add_node(str(i), name=i,
                                       color=ld.NODE_COLOR[ld.node_type[i]], edge_color=ld.NODE_EDGECOLOR[ld.node_type[i]])
        if ld.outgoing[index][i]==0 or ld.incoming[index][i]==0:
            continue
        ld.neighborG.add_edge(str(index), str(i), weight=ld.incoming[index][i] if ld.incoming[index][i]!=0 else ld.outgoing[i][index])
                                                        #"%d/%d"%(ld.incoming[index][i] if ld.incoming[index][i]!=0 else ld.outgoing[i][index],
                                                        #         ld.outgoing[index][i] if ld.outgoing[index][i]!=0 else ld.incoming[i][index]))