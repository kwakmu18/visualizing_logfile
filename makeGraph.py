def makeRootGraph(ld, index):
    #ld.rootG.clear()
    ld.rootG.clear_edges()
    A, B = index, ld.parent[index]
    while True:
        if B==0:break
        if ld.incoming[B][A]==0: 
            prr1 = ld.outgoing[A][B]
            prr2 = ld.incoming[A][B]
        else:
            prr1 = ld.incoming[B][A]
            prr2 = ld.outgoing[B][A]
        ld.rootG.add_weighted_edges_from([(A, B, prr1)],color="red")
        ld.rootG.add_weighted_edges_from([(B, A, prr2)], color="blue")
        A, B = B, ld.parent[B]

def makeNeighborGraph(ld, index):
    ld.neighborG.clear()
    ld.neighborG.clear_edges()
    
    for i in range(1, ld.node_cnt+1):
        ld.neighborG.add_node(i)
        if ld.outgoing[index][i]==0 and ld.incoming[index][i]==0 and ld.outgoing[i][index]==0 and ld.incoming[i][index]==0:
            continue
        if ld.incoming[index][i]==0:
            prr1 = ld.outgoing[i][index]
            prr2 = ld.incoming[i][index]
        else:
            prr1 = ld.incoming[index][i]
            prr2 = ld.outgoing[index][i]
        ld.neighborG.add_weighted_edges_from([(i,index,prr1)],color="red")
        ld.neighborG.add_weighted_edges_from([(index,i,prr2)], color="blue")
        #ld.neighborG.add_edge(index, i, weight=ld.incoming[index][i] if ld.incoming[index][i]!=0 else ld.outgoing[i][index])
                                                        #"%d/%d"%(ld.incoming[index][i] if ld.incoming[index][i]!=0 else ld.outgoing[i][index],
                                                        #         ld.outgoing[index][i] if ld.outgoing[index][i]!=0 else ld.incoming[i][index]))