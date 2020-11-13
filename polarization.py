import networkx as nx
import itertools
import community as community_louvain


class Polarization:
	def __init__(self, edgelist_file, community_file = None):
		try:
			#Take in edgelist to create networkx graph object
			self.G = nx.read_edgelist(edgelist_file)
		except:
			print("Edgelist file either not provided or not in proper format, please refer to documentation.")

		#If a community file is not provided, use louvain clustering to create one
		if community_file is None:
			#Set up a community list with all nodes and a node partition
			self.partition, self.community_list = self.create_louvain_communities()
		else:
			try:
				#If a community file is provided, set up a community list with all nodes and a node partition
				self.community_list = self.community_file_to_list(community_file)
				self.partition = self.create_partition()
			except:
				print("The community file provided is not in the proper format, please refer to documentation.")
		#Grab all possible pairs of communities
		self.community_pairs = self.find_pairs_of_communities()
		#Get polarization scores between each community
		self.scores = self.get_score()

	def create_partition(self):
		#Create a partition dictionary filled with each node and its respective community
		count = 0
		partition = {}
		for i in self.community_list:
			partition[str(count)] = int(i)
			count += 1 
		return partition

	def create_louvain_communities(self):
		#Create partition using louvain algorithm
		partition = community_louvain.best_partition(self.G)
		#Create list of length # of nodes with all None values
		comms = [None] * len(partition)
		#Get list of all the key values of partition
		keys = list(partition.keys())
		#Get list of all values of partition
		values = list(partition.values())
		#Append them into our comms list, we do this because the parition is not in numerical order (0,1,2,...) so we're doing that here 
		for i in range(0,len(partition)):
			k = keys[i]
			v = values[i]
			comms[int(k)] = str(v)

		return partition, comms

	def community_file_to_list(self, filename):
		#Convert community file given into list format, community value at index i represents community of node i
		com_list = []
		file = open(filename, 'r') 
		Lines = file.readlines() 
		for line in Lines:
			com_list.append(line.strip())
		return com_list

	def find_pairs_of_communities(self):
		#Get all possible pairs of communities in graph G
		com = list(dict.fromkeys(self.community_list))
		com = list(itertools.combinations(com, 2))
		return com


	def get_subgraph(self,communities):
		#Create empty list of nodes in either communities
		node_list = []
		#Create empty dictionary of nodes and their communities
		node_partition = {}
		#For each node in the overall partition of nodes
		for node in self.partition:
			#Grab the node community
			node_community = str(self.partition[node])
			#If the node community is in either of the communities in the pair of communities provided
			if (node_community == communities[0]) or (node_community == communities[1]):
				#Append the node to the nodes list
				node_list.append(node)	
				#Add node and its community to node partition dictionary
				node_partition[node] = self.partition[node]
		#Creat subgraph, H, of grpah G
		H = self.G.subgraph(node_list)
		return H, node_partition


	def get_score(self):
		#Create scores list to insert polarization score for each pair
		scores = []
		#For every combination of pairs of communities
		for pair in self.community_pairs:
			#Get subgraph that contains only the nodes and edges in/between those communities
			H,H_partition = self.get_subgraph(pair)
			#Get boundary nodes and interior nodes for each community
			b1, b2, i1, i2 = self.group_nodes(pair,H,H_partition)
			#Get boundary edges and interior edges 
			E_B, E_int = self.group_edges(H,b1,b2,i1,i2)
			#Calculate the polarization score
			score = self.get_polarization_score(b1 + b2,E_B,E_int,pair)
			#Append the score, along with the community pairs to the scores list
			scores.append((score,pair))
		return scores

	def group_nodes(self,pair,H,H_partition):
		#Append all nodes in graph H into list
		nodes = [value for value in H.nodes()]
		#Create empty lists for boundary and inner nodes from each community
		boundary_1, inner_1, boundary_2, inner_2 = ([] for i in range(4))

		#Iterate through each node in our subgraph
		for node in H.nodes():
			#Find which community the node in question belongs to
			node_community = H_partition[node]
			#Check that said node passes condition one (node is connected to a node from other community)
			if self.check_first_condition(node, H, H_partition, node_community):
				#Check condition two is passed (node connects to a node within same community that does not connect to an opposing community node)
				if self.check_second_condition(node, H, H_partition, node_community):
					#If both condition one and two are passed, the node is a boundary node, and we append it to the appropriate boundary list and remove it from our overall nodes list
					if node_community == int(pair[0]):
						boundary_1.append(node)
						nodes.remove(node)
					else:
						boundary_2.append(node)
						nodes.remove(node)	
				#If the node passes only condition one and not two, it is neither a boundary node nor an inner node, so we simply get rid of it from our nodes list
				else:
					nodes.remove(node)

		#Any remaining nodes in our node list are inner nodes, so we append them to the respective inner lists accordingly
		for node in nodes:
			node_community = H_partition[node]
			if node_community == int(pair[0]):
				inner_1.append(node)
			else:
				inner_2.append(node)
		return boundary_1, boundary_2, inner_1, inner_2

	def check_first_condition(self, node, H, H_partition, node_community):
		#Iterate through every node in subgraph H
		for n in H.nodes():
			#If there exists an edge between our node and any other node in subgraph that belongs to opposing community, return True
			if (H.has_edge(node,n)) and (H_partition[n] != node_community):
				return True
		#Otherwise return False, condition one failed
		return False

	def check_second_condition(self, node, H, H_partition, node_community):
		#Iterate through every node in subgraph H
		for n in H.nodes():
			#If there exists an edge between our node and any other node in same community, and that node not connected to an outside node, return True
			if (H.has_edge(node,n)) and (H_partition[n] == node_community) and self.not_connected_to_outsiders(n, H, H_partition, node_community):
				return True
		#Otherwise return False, condition two failed
		return False

	def not_connected_to_outsiders(self, node, H, H_partition, node_community):
		#Iterate through every node in subgraph H
		for n in H.nodes():
			#If our connected node connects to any nodes outside its own community, return False
			if (H.has_edge(node,n)) and (H_partition[n] != node_community):
				return False
		return True

	def group_edges(self,H,b1,b2,i1,i2):
		#Create empty list for boundary edges (edges between boundary nodes) and interior edges (edges between boundary nodes and inner nodes within same community)
		E_B, E_int = ([] for i in range(2))
		#For the set of boundary nodes in H, for each pair of nodes check if they connect, append their edge to boundary edges list if they do
		for node_1 in b1:
			for node_2 in b2:
				if H.has_edge(node_1,node_2):
					E_B.append((node_1, node_2))
		#For set of boundary and inner nodes of first community, fir each pair of nodes check if they connect, append their edge to interior edges list if they do
		for node_1 in b1:
			for node_2 in i1:
				if H.has_edge(node_1,node_2):
					E_int.append((node_1, node_2))
		#For set of boundary and inner nodes of second community, fir each pair of nodes check if they connect, append their edge to interior edges list if they do
		for node_1 in b2:
				for node_2 in i2:
					if H.has_edge(node_1,node_2):
						E_int.append((node_1, node_2))
		return E_B, E_int

	def get_polarization_score(self,B,E_B,E_int,pair):
		#Set score to 0
		score = 0
		#Try to apply formula defined in paper for polarization to arrive at polarization score
		try:
			for node in B:
				di_v = 0
				db_v = 0
				for edge in E_B:
					if node in edge:
						db_v += 1
				for edge in E_int:
					if node in edge:
						di_v += 1
				score += ((di_v / (db_v + di_v)) - 0.5)
			score = (score / len(B))
		#There are cases, especially for small graphs, where there 
		except:
			print(f"There exist {len(B)} boundary nodes between community {pair[0]} and {pair[1]}")
			score = 'DNE'
		return score
