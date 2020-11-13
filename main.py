from polarization import Polarization
from modularity import Modularity
from graph import *

p = Polarization('data/karate.edgelist','data/karate.ecg')
print(p.scores)
graph(p)

m = Modularity('data/karate.edgelist','data/karate.ecg')
print(m.scores)
graph(m)