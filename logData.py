from anytree import Node
import networkx as nx
import re

def extract(text):
    pattern = r'\((.*?)\)'  # 괄호 안에 있는 값을 추출하기 위한 정규 표현식
    matches = re.findall(pattern, text)  # 정규 표현식과 문자열을 매칭하여 값들을 추출
    
    return matches

NODE_CNT = 12
ROOT_NODE = 1
LOGFILE_NAME = "log.txt"
TYPE_STR = [None, "AP", "Sensor", "Actuator", "Router"]
NODE_COLOR = [None, "red", "white", "green", "cyan"]
NODE_EDGECOLOR = ["white", "white", "black", "white", "white"]

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
neighborG = nx.DiGraph()
colors = []
edge_colors = []

with open(LOGFILE_NAME, 'r') as file:
    for line in file:
        if line.startswith("[N]") or line.startswith("[+]"):
            root_childcnt = int(line.split(":")[2])
            sections = extract(line)
            root_id, root_type, root_level, root_rank, root_parent_id = map(int, sections[0].split(","))
            parent_node = root.get(root_parent_id, None)
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
    for j in range(1, NODE_CNT+1):
        if i==j: continue
        if incoming[i][j]!=0: cnt+=1
    child_cnt[i] = cnt
print(child_cnt)
for node_id, node in root.items():
    for child in node.children:
        G.add_edge(node.name, child.name)

pos = nx.spring_layout(G)
neighborPos = None

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