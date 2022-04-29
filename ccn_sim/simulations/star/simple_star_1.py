"""
Create a star network topology like this:

https://blog.boson.com/hs-fs/hub/70217/file-27052587-png/images/9_-_extended_star_topology.png

Run a DDoS scenario simulation and save the recorded experiment observations to file.

"""


from ccn_sim.simulations.util import create_data, run_experiment
from simpy.core import Environment

from .build_network import build_star_network


def simple_star_1():
    """Run a simulation using star network topology for various node cache sizes."""

    run_until = 20_000  # the simulation will run for 20_000 time steps
    request_delay = 3  # Clients send a request packet every three time steps
    data = create_data(n=100)  # There are 100 unique CCN data objects

    cache_sizes = [0, 25, 50, 75, 100]

    # Run CCN simulations
    for cache_size in cache_sizes:
        sim_path = f"star_1_cache{cache_size}"
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
    sim_path = "star_1_ip"
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
