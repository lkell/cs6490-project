import random
from typing import Dict

"""
Create a star network topology like this:

https://blog.boson.com/hs-fs/hub/70217/file-27052587-png/images/9_-_extended_star_topology.png

"""


from ccn_sim.simulations.util import (
    create_data,
    randomized_data_requests,
    run_experiment,
)
from requests import request
from simpy.core import Environment

from .build_network import build_star_network


def simple_star_1():
    run_until = 20_000
    request_delay = 3
    data = create_data(n=100)

    cache_sizes = [0, 25, 50, 75, 100]

    # Run CCN simulations
    for cache_size in cache_sizes:
        sim_path = f"star/1/cache{cache_size}"
        env = Environment()

        network = build_star_network(
            env=env,
            cache_size=cache_size,
            n_clusters=4,
            simulate_ip=False,
            cluster_clients=3,
            client_to_router_hops=0,
            data=data,
        )
        run_experiment(
            sim_path=sim_path,
            env=env,
            network=network,
            data_paths=list(data.keys()),
            run_until=run_until,
            request_delay=request_delay,
        )

    # Run simulation with 'IP' mode set
    sim_path = "star/1/ip-mode"
    env = Environment()

    network = build_star_network(
        env=env,
        cache_size=0,
        n_clusters=4,
        simulate_ip=True,
        cluster_clients=3,
        client_to_router_hops=0,
        data=data,
    )
    run_experiment(
        sim_path=sim_path,
        env=env,
        network=network,
        data_paths=list(data.keys()),
        run_until=run_until,
        request_delay=request_delay,
    )


if __name__ == "__main__":
    simple_star_1()
