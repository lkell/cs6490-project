"""
Run a basic simulation with the following network architecture:

c-0 --> r-0 -->
             | 
c-1 --> r-1 --> r-3 --> s-0
             |
c-2 --> r-2 -->

"""
from typing import Dict

from ccn_sim.node_sim import Node
from simpy.core import Environment


def sim1():
    sim_path = "sim1"
    env = Environment()
    nodes = _create_network(env, cache_size=100)
    clients = nodes["clients"]
    routers = nodes["routers"]
    servers = nodes["servers"]

    client_requests = ["data/0" for _ in range(1_000_000)]
    for client in clients:
        env.process(client.run(request_paths=client_requests, request_delay=1))
    for router in routers:
        env.process(router.run())
    for server in servers:
        env.process(server.run())
    env.run(until=1000)

    for router in routers:
        router.write_queue_hist(sim_path)
    for server in servers:
        server.write_queue_hist(sim_path)
    for client in clients:
        client.write_request_times(sim_path)
        client.write_response_times(sim_path)


def _create_network(env: Environment, cache_size: int) -> Dict[str, list[Node]]:

    data = {"data/0": 0}

    # Define routers and server
    r0 = Node(env, id="r-0", cache_size=cache_size)
    r1 = Node(env, id="r-1", cache_size=cache_size)
    r2 = Node(env, id="r-2", cache_size=cache_size)
    r3 = Node(env, id="r-3", cache_size=cache_size)
    s0 = Node(env, id="s-0", cache_size=cache_size, data=data)

    # Define network router edges
    r0.add_neighbors({"r-3": r3})
    r1.add_neighbors({"r-3": r3})
    r2.add_neighbors({"r-3": r3})
    r3.add_neighbors({"r-0": r0})
    r3.add_neighbors({"r-1": r1})
    r3.add_neighbors({"r-2": r2})
    r3.add_neighbors({"s-0": s0})
    s0.add_neighbors({"r-3": r3})

    # Define Clients and add routers
    c0 = Node(env, id="c-0", is_client=True)
    c0.add_neighbors({"r-0": r0})
    r0.add_neighbors({"c-0": c0})

    c1 = Node(env, id="c-1", is_client=True)
    c1.add_neighbors({"r-1": r1})
    r1.add_neighbors({"c-1": c1})

    c2 = Node(env, id="c-2", is_client=True)
    c2.add_neighbors({"r-2": r2})
    r2.add_neighbors({"c-2": c2})

    s0.init_routing_broadcast()

    return {"clients": [c0, c1, c2], "routers": [r0, r1, r2, r3], "servers": [s0]}


if __name__ == "__main__":
    sim1()
