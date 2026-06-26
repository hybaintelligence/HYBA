#!/usr/bin/env python
import sys
sys.path.insert(0, '.')

from python_backend.pythia_mining.pulvini_topology import ADJACENCY_MAP
from collections import Counter

# Check for asymmetries
asymmetric = []
for node_id, neighbors in ADJACENCY_MAP.items():
    for neighbor in neighbors['d']:
        if node_id not in ADJACENCY_MAP[neighbor]['d']:
            asymmetric.append((node_id, neighbor))

print(f'Asymmetric edges: {len(asymmetric)}')
if asymmetric:
    for src, dst in sorted(asymmetric)[:10]:
        print(f'  {src} -> {dst}')

# Check degree histogram
degree_hist = Counter(len(neighbors['d']) + len(neighbors['i']) for neighbors in ADJACENCY_MAP.values())
print(f'Degree histogram: {dict(degree_hist)}')

# Check if all nodes have same degree
degrees = [len(neighbors['d']) + len(neighbors['i']) for neighbors in ADJACENCY_MAP.values()]
print(f'All degrees same: {len(set(degrees)) == 1}')
print(f'Degree values: {set(degrees)}')
