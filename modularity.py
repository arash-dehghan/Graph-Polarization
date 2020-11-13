import community as com
import networkx as nx
import itertools

class Modularity():
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
		#Get modularity scores between each community
		self.scores = self.get_scores()
		#Get overall modularity score of graph
		self.overall_score  = self.overall_modularity()

	def overall_modularity(self):
		#Calculate overall modularity
		return self.modularity(self.partition,self.G)

	def community_file_to_list(self, filename):
		#Convert community file given into list format, community value at index i represents community of node i
		com_list = []
		file = open(filename, 'r') 
		Lines = file.readlines() 
		for line in Lines:
			com_list.append(line.strip())
		return com_list

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

	def find_pairs_of_communities(self):
		#Get all possible pairs of communities in graph G
		com = list(dict.fromkeys(self.community_list))
		com = list(itertools.combinations(com, 2))
		return com

	def modularity(self, partition, graph, weight='weight'):
		#Calculate the modularity as described using formula given in paper
		if graph.is_directed():
			raise TypeError("Bad graph type, use only non directed graph")

		inc = dict([])
		deg = dict([])
		links = graph.size(weight=weight)
		if links == 0:
			raise ValueError("A graph without link has an undefined modularity")

		for node in graph:
			com = partition[node]
			deg[com] = deg.get(com, 0.) + graph.degree(node, weight=weight)
			for neighbor, datas in graph[node].items():
				edge_weight = datas.get(weight, 1)
				if partition[neighbor] == com:
					if neighbor == node:
						inc[com] = inc.get(com, 0.) + float(edge_weight)
					else:
						inc[com] = inc.get(com, 0.) + float(edge_weight) / 2.

		res = 0.
		for com in set(partition.values()):
			res += (inc.get(com, 0.) / links) - \
				   (deg.get(com, 0.) / (2. * links)) ** 2
		return res

	def get_scores(self):
		#Create empty scores list to fill later
		scores = []
		#For each pair of communities in the overall pair of communities
		for communities in self.community_pairs:
			#Create empty list for nodes and dictionary for note partitions
			node_list = []
			node_partition = {}
			#For each node in the overall graph node partition
			for node in self.partition:
				#Find the node community
				node_community = str(self.partition[node])
				#Check if the node is in either of the communities in the communities pair
				if (node_community == communities[0]) or (node_community == communities[1]):
					#If they are append them to the respective list/dictionary
					node_list.append(node)	
					node_partition[node] = self.partition[node]
			#Create subgraph using those nodes and edges between those nodes
			H = self.G.subgraph(node_list)
			#Calculate new modularity score of subgraph
			m = self.modularity(node_partition,H)
			#Append score gotten, as well as the communities, to the scores list
			scores.append((m,communities))
		return scores


