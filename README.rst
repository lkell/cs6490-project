Things to work on:

- [X] Add caching at the routers
    - [X] Check if caching requires LRU
- [X] Add LRU policy to ContentCache
- [X] Prevent packet looping (how do we do BFS without creating infinte packets, check paper)
    - [X] Implement PIT
    - [] Implement FIB (potentially set up beforehand and sweep under the rug) [Dalton]


- [X] Create asynchronous environment with simpy
- [] Combine client and router classes [Jack]
- [] Add mechanism to output network load [Leo]
    - [] Router queue history
    - [] Request packet turnaround time
- [] Reduce the neighbor dict complexity
- [] Create some simple network topologies
- [] Figure out how to DDOS our networks
- [] Make some nice charts [Jack]
- [] Make a powerpoint
