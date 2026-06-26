#!/usr/bin/env python
import sys
sys.path.insert(0, '.')

from python_backend.pythia_mining.pulvini_topology import ADJACENCY_MAP

print("D-node degrees:")
for d in range(5):
    d_internal = len(ADJACENCY_MAP[d]['d'])
    d_to_i = len(ADJACENCY_MAP[d]['i'])
    total = d_internal + d_to_i
    print(f"  D{d}: d={d_internal}, i={d_to_i}, total={total}")

print("\nI-node degrees:")
for i in range(20, 25):
    i_internal = len(ADJACENCY_MAP[i]['d'])
    i_to_d = len(ADJACENCY_MAP[i]['i'])
    total = i_internal + i_to_d
    print(f"  I{i}: d={i_internal}, i={i_to_d}, total={total}")

print("\nD/I connectivity check:")
print(f"D-nodes total connecting to I-nodes:")
total_d_to_i = sum(len(ADJACENCY_MAP[d]['i']) for d in range(20))
print(f"  Sum: {total_d_to_i} (should be 60 = 20*3)")

print(f"I-nodes total connecting to D-nodes:")
total_i_to_d = sum(len(ADJACENCY_MAP[i]['i']) for i in range(20, 32))
print(f"  Sum: {total_i_to_d} (should be 60 = 12*5)")
