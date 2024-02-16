from anytree import Node, RenderTree, PreOrderIter
import networkx as nx
import re
import matplotlib.pyplot as plt
import pydot
from networkx.drawing.nx_pydot import graphviz_layout

def extract(text):
    pattern = r'\((.*?)\)'  # 괄호 안에 있는 값을 추출하기 위한 정규 표현식
    matches = re.findall(pattern, text)  # 정규 표현식과 문자열을 매칭하여 값들을 추출
    
    return matches

NODE_CNT = 12
ROOT_NODE = 1
LOGFILE_NAME = "log.txt"
TYPE_STR = [None, "AP", "Sensor", "Actuator", "Router", "Virtual Sensor"]
NODE_COLOR = [None, "red", "white", "green", "cyan", "blue"]
NODE_EDGECOLOR = ["white", "white", "black", "white", "white", "black"]

root = {}
incoming = [[0 for _ in range(NODE_CNT+1)] for _ in range(NODE_CNT+1)]
outgoing = [[0 for _ in range(NODE_CNT+1)] for _ in range(NODE_CNT+1)]
parent = [0 for _ in range(NODE_CNT+1)]
node_type = [0 for _ in range(NODE_CNT+1)]
child_cnt = [0 for _ in range(NODE_CNT+1)]
prr = {}

ranks = {}
G = nx.Graph()
rootG = nx.DiGraph()
neighborG = nx.Graph()
colors = []
edge_colors = []
levels = {}

with open(LOGFILE_NAME, 'r') as file:
    for line in file:
        if line.startswith("[N]") or line.startswith("[+]"):
            root_childcnt = int(line.split(":")[2])
            sections = extract(line)
            root_id, root_type, root_level, root_rank, root_parent_id = map(int, sections[0].split(","))
            parent_node = root.get(root_parent_id, None)

            levels[root_id] = root_level

            root[root_id] = Node(f"{root_id}", parent=parent_node)
            ranks[root_id] = root_rank
            node_type[root_id] = root_type
            parent[root_id] = root_parent_id
            
            for section in sections[1:]:
                child_id, child_level, child_incoming, child_outgoing = map(int, section.split(","))
                incoming[root_id][child_id]=child_incoming
                #incoming[child_id][root_id]=child_outgoing
                outgoing[root_id][child_id]=child_outgoing
                #outgoing[child_id][root_id]=child_incoming
        elif line.startswith("[INFO: CNLAB     ]      node=(1): number of received data from="):
            data = list(map(int, extract(line)))
            prr[data[1]] = data[3]

for i in range(1, NODE_CNT+1):
    cnt = 0
    for j in range(i, NODE_CNT+1):
        if i==j: continue
        if incoming[i][j]!=0: cnt+=1
    child_cnt[i] = cnt


dist = {}
for i in range(1, NODE_CNT+1):
    for j in range(i+1, NODE_CNT+1):
        if i==j or outgoing[i][j]==0: continue
        G.add_edge(str(i), str(j))
        dist[(str(i),str(j))]=outgoing[i][j]
# pos = nx. fruchterman_reingold_layout(G)
pos = nx.spring_layout(G, k=0.001, iterations = 50, seed = 71)

G.clear(); G.clear_edges()
for node_id, node in root.items():
    for child in node.children:
        G.add_edge(node.name, child.name)

neighborPos = pos

for node_id, _ in pos.items():
    node_id = int(node_id)
    if node_type[node_id]==1:
        colors.append("red")
        edge_colors.append("white")
    elif node_type[node_id]==2:
        colors.append("white")
        edge_colors.append("black")
    elif node_type[node_id]==3:
        colors.append("green")
        edge_colors.append("white")
    elif node_type[node_id]==4:
        colors.append("cyan")
        edge_colors.append("white")
    elif node_type[node_id]==5:
        colors.append("blue")
        edge_colors.append("black")

# 추가된 코드: 트리 순회 (전위 순회 사용)
root_node = root[ROOT_NODE]  # 루트 노드 설정
    
    # 트리를 시각화 (텍스트 기반)
for pre, fill, node in RenderTree(root_node):
    print("%s%s" % (pre, node.name))
    