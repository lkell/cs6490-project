Things to work on:

- [X] Add caching at the routers
    - [X] Check if caching requires LRU
- [X] Add LRU policy to ContentCache
- [X] Prevent packet looping (how do we do BFS without creating infinte packets, check paper)
    - [X] Implement PIT
    - [X] Implement FIB (potentially set up beforehand and sweep under the rug) [Dalton]


- [X] Create asynchronous environment with simpy
- [X] Combine client and router classes [Jack]
- [X] Add mechanism to output network load [Leo]
    - [X] Router queue history
    - [X] Request packet turnaround time
- [x] Fix PIT implementation in the node_sim.py file
- [] Reduce the neighbor dict complexity
- [] Create some simple network topologies
- [] Figure out how to DDOS our networks
- [] Make some nice charts [Jack]
- [] Make a powerpoint
