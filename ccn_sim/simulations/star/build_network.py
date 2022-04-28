from typing import Dict

from ccn_sim.node_sim import Node
from simpy.core import Environment


def build_star_network(
    env: Environment,
    cache_size: int,
    n_clusters: int,
    simulate_ip: bool,
    cluster_clients: int,
    client_to_router_hops: int,
    data: Dict[str, int],
) -> Dict[str, list[Node]]:
    """
    Initializes a configurable "STAR" network ready form simulation.

    Parameters:
        env: The simpy Environment
        cache_size: The number of elements that each Router's content cache can hold.
        n_clusters: The number of network clusters connected to the central server.
            Each cluster contains a set of clients and one or more routers.
        simulate_ip: If True, the routers are configured to simulate simple IP
            routing behavior (no caching or PIT).
        cluster_clients: The number of clients contained in each cluster.
        client_to_router_hops: The number of routers situated between each client and
            the end router of the cluster.
        data: The content contained by the server.

    Returns:
            binary_sum (str): Binary string of the sum of a and b
    """

    clients: list[Node] = []  # All clients in the network
    routers: list[Node] = []  # All routers in the network
    final_routers: list[
        Node
    ] = []  # The routers directly connected to server. One per cluster.

    client_i = 0
    router_i = 0

    for i in range(n_clusters):

        # Create each cluster of clients + routers
        # final_router will directly connect to central server

        final_router_id = f"r-{router_i}"
        final_router = Node(
            env,
            id=final_router_id,
            cache_size=cache_size,
            is_client=False,
            simulate_ip=simulate_ip,
        )
        routers.append(final_router)
        final_routers.append(final_router)
        router_i += 1

        for j in range(cluster_clients):

            # Create each client with connecting router chain up to final router

            client_id = f"c-{client_i}"
            client = Node(env, id=client_id, is_client=True)
            clients.append(client)

            last_node = client

            for j in range(client_to_router_hops):
                raise NotImplementedError

            final_router.add_neighbors({last_node.id: last_node})
            last_node.add_neighbors({final_router.id: final_router})

            client_i += 1

    # Define server and connect to final routers from each server
    server_id = "s-0"
    server = Node(
        env,
        id=server_id,
        data=data,
        cache_size=cache_size,
        is_client=False,
        simulate_ip=simulate_ip,
    )

    for router in final_routers:
        server.add_neighbors({router.id: router})
        router.add_neighbors({server.id: server})

    # Create the routing tables
    server.init_routing_broadcast()

    return {"clients": clients, "routers": routers, "servers": [server]}
