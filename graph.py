import community as community_louvain
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import networkx as nx
from polarization import Polarization


def graph(p):	
	pos = nx.spring_layout(p.G)
	# color the nodes according to their partition
	cmap = cm.get_cmap('viridis', max(p.partition.values()) + 1)
	nx.draw_networkx_nodes(p.G, pos, p.partition.keys(), node_size=40,
	                       cmap=cmap, node_color=list(p.partition.values()))
	nx.draw_networkx_edges(p.G, pos, alpha=0.5)
	plt.show()
