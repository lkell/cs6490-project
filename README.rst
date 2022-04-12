Things to work on:

- [X] Add caching at the routers
    - [] Check if caching requires LRU (check paper)
- [] Prevent packet looping (how do we do BFS without creating infinte packets, check paper)
- [] Prevent multiple packets taking the same path with switched nodes

A
|\
| \
|  \
|   \
|    \
B --- C

ABC vs ACB during our depth first search

- [] Create asynchronous environment with simpy
- [] Reduce the neighbor dict complexity
- [] Create some simple network topologies
- [] Figure out how to DDOS our networks
- [] Make some nice charts
- [] Make a powerpoint
