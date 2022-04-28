import random
from typing import Dict, Iterable

from ccn_sim.node_sim import Node
from simpy.core import Environment


def run_experiment(
    sim_path: str,
    env: Environment,
    network: Dict[str, list[Node]],
    data_paths: list[str],
    run_until: int,
    request_delay: int,
) -> None:
    """
    Use the supplied arguments to run a CCN experiment and save the network load
    measurements to CSV files.
    """

    clients = network["clients"]
    routers = network["routers"]
    servers = network["servers"]

    for client in clients:
        requests = randomized_data_requests(data_paths)
        env.process(client.run(request_paths=requests, request_delay=request_delay))
    for router in routers:
        env.process(router.run())
    for server in servers:
        env.process(server.run())

    print(f"Running simulation...")
    env.run(until=run_until)

    print(f"Saving output to {sim_path}...")
    for client in clients:
        client.write_request_times(sim_path)
        client.write_response_times(sim_path)
    for router in routers:
        router.write_queue_hist(sim_path)
    for server in servers:
        server.write_queue_hist(sim_path)


def create_data(n: int) -> Dict[str, int]:
    """
    Create a dictionary of data path-content pairs to be stored in a CCN server.
    Each path is assigned an incremented id.

    Parameters:
        n: The number of data elements.

    """
    data = {}
    for i in range(n):
        data[f"data/{i}"] = i
    return data


def randomized_data_requests(data: list[str]) -> Iterable[str]:
    """
    Create an infinite sequence CCN requests from the given set of all possible requests.
    This generator is useful for running CCN DDoS simulations.

    Parameters:
        data: The list of all possible CCN request paths.
    """
    while True:
        i = random.randint(0, len(data) - 1)
        yield data[i]
