from ccn_sim import __version__
from ccn_sim.node import Client, Router, Server


def test_version():
    assert __version__ == "0.1.0"


def test_simple_network():
    # test a simple [Client <-> Router <-> Server] setup

    data = 123

    client, routers, server = build_simple_network(1)
    server.data = {"data/0": data}

    client.build_packet_and_fetch_content("data/0")

    assert client.retrieved_content is not None
    assert client.retrieved_content.response_data == data

    assert client.retrieved_content.inverse_TTL == 4


def build_simple_network(n_routers: int = 100):
    routers = [Router(f"r-{i}") for i in range(n_routers)]
    for i in range(1, n_routers - 1):
        prev_router = i - 1
        next_router = i + 1
        routers[i].add_neighbors(
            {
                routers[prev_router].id: routers[prev_router],
                routers[next_router].id: routers[next_router],
            }
        )

    client = Client("c-0", routers[0])
    server = Server("s-0", routers[n_routers - 1], {"data/0": -1})

    second_node = routers[1] if n_routers > 1 else server
    routers[0].add_neighbors({"c-0": client, "r-1": second_node})

    if n_routers > 1:
        routers[n_routers - 1].add_neighbors(
            {"r-98": routers[n_routers - 2], "s-0": server}
        )

    return client, routers, server


def test_simple_network_long():
    # test a simple network with chain of routers [Client <-> Routers <-> Server]

    data = 123

    client, routers, server = build_simple_network()
    server.data = {"data/0": data}

    # No cached data
    client.build_packet_and_fetch_content("data/0")

    assert routers[0].cache.lookup("data/0") == data
    assert routers[0].cache.lookup("data/1") is None

    assert client.retrieved_content is not None
    assert client.retrieved_content.response_data == data

    assert client.retrieved_content.inverse_TTL == 202

    # Use cached data
    client.build_packet_and_fetch_content("data/0")

    assert routers[0].cache.lookup("data/0") == data
    assert routers[0].cache.lookup("data/1") is None

    assert client.retrieved_content is not None
    assert client.retrieved_content.response_data == data

    assert client.retrieved_content.inverse_TTL == 2


def test_cache():
    max_cache = 20

    client, routers, server = build_simple_network(1)

    assert len(routers[0].cache.cache.keys()) == 0

    # Add the data
    for i in range(21):
        server.data[f"data/{i}"] = i

    # ASSUMES FIFO CACHE
    # Request 21 items twice and make sure that the cache expires
    for i in range(42):
        client.build_packet_and_fetch_content(f"data/{i % 21}")
        assert client.retrieved_content is not None
        assert client.retrieved_content.response_data == i % 21
        assert client.retrieved_content.inverse_TTL == 4
        assert len(routers[0].cache.cache.keys()) == min(i + 1, max_cache)

    routers[0].cache.flush()

    # Test for cache hits
    for i in range(40):
        client.build_packet_and_fetch_content(f"data/{i % 20}")
        assert client.retrieved_content is not None
        assert client.retrieved_content.response_data == i % 20
        assert client.retrieved_content.inverse_TTL == (4 if i < 20 else 2)
        assert len(routers[0].cache.cache.keys()) == min(i + 1, max_cache)
