from ccn_sim import __version__
from ccn_sim.node_sim import ContentCache, Node
from simpy.core import Environment


def test_version():
    assert __version__ == "0.1.0"


def build_simple_network(env: Environment, n_routers: int = 100):
    if n_routers < 2:
        raise ValueError("n_routers must be at least 2")

    routers = [Node(env, f"r-{i}") for i in range(n_routers - 1)]
    routers.append(Node(env, f"r-{n_routers - 1}", {"data/0": -1}))
    for i in range(1, n_routers - 1):
        prev_router = i - 1
        next_router = i + 1
        routers[i].add_neighbors(
            {
                routers[prev_router].id: routers[prev_router],
                routers[next_router].id: routers[next_router],
            }
        )
    routers[n_routers - 1].add_neighbors(
        {routers[n_routers - 2].id: routers[n_routers - 2]}
    )

    client = Node(env, "c-0", is_client=True)
    client.add_neighbors({"r-0": routers[0]})
    routers[0].add_neighbors({"c-0": client, "r-1": routers[1]})

    return client, routers


def test_broadcast():
    env = Environment()

    client, routers = build_simple_network(env, 100)
    routers[99].data = {"data/0": 0, "data/1": 1}
    routers[99].init_routing_broadcast()

    for i in range(98, -1, -1):
        expected_dist = 98 - i
        expected_data = {
            "data/0": (f"r-{i+1}", expected_dist),
            "data/1": (f"r-{i+1}", expected_dist),
        }
        assert routers[i].FIB == expected_data

    assert client.FIB == {
        "data/0": ("r-0", 99),
        "data/1": ("r-0", 99),
    }


def test_simple_network():
    # test a simple [Node <-> Node <-> Server (Node)] setup

    data = 123
    env = Environment()

    client, routers = build_simple_network(env, 2)
    routers[1].data = {"data/0": data}
    routers[1].init_routing_broadcast()

    env.process(client.run(request_paths=["data/0", "data/0"], request_delay=5))
    for router in routers:
        env.process(router.run())
    env.run(until=100)

    assert client.responses is not None
    assert len(client.responses) == 2
    assert client.responses[0].response_data == data
    assert client.responses[0].inverse_TTL == 4
    assert client.responses[1].response_data == data
    assert client.responses[1].inverse_TTL == 2  #  content caching should shorten path

    env = Environment()
    client, routers = build_simple_network(env, 2)
    routers[1].data = {"data/0": data}
    routers[1].init_routing_broadcast()
    env.process(client.run(request_paths=["data/0", "data/0"], request_delay=1))
    for router in routers:
        env.process(router.run())
    env.run(until=100)

    # We should see only one response packet this time because the first router
    # is able to consolidate the return packets using its PIT
    assert len(client.responses) == 1


def test_simple_network_long():
    # test a simple network with chain of routers [Node <-> Nodes <-> Server]

    data = 123
    env = Environment()

    (
        client,
        routers,
    ) = build_simple_network(env, 100)
    routers[99].data = {"data/0": data}
    routers[99].init_routing_broadcast()

    env.process(client.run(request_paths=["data/0", "data/0"], request_delay=1000))
    for router in routers:
        env.process(router.run())
    env.run(until=2000)

    assert routers[0].cache.lookup("data/0") == data
    assert routers[0].cache.lookup("data/1") is None

    assert client.responses is not None
    assert client.responses[0].response_data == data
    assert client.responses[0].inverse_TTL == 200
    assert client.responses[1].inverse_TTL == 2


def test_cache():
    max_cache = 20
    env = Environment()

    client, routers = build_simple_network(env, 2)

    assert len(routers[0].cache.cache.keys()) == 0

    # Add the data
    for i in range(21):
        routers[1].data[f"data/{i}"] = i
    routers[1].init_routing_broadcast()

    # TODO: Convert the following commented-out code to work with async node_sim

    # # ASSUMES FIFO CACHE (works with LRU)
    # # Request 21 items twice and make sure that the cache expires
    # for i in range(42):
    #     print("\n\n\n\n\n")
    #     client.build_packet_and_fetch_content(f"data/{i % 21}")
    #     assert client.retrieved_content is not None
    #     assert client.retrieved_content.response_data == i % 21
    #     assert client.retrieved_content.inverse_TTL == 4
    #     assert len(routers[0].cache.cache.keys()) == min(i + 1, max_cache)

    # routers[0].cache.flush()
    # assert len(routers[0].cache.cache.keys()) == 0

    # # Test for cache hits
    # for i in range(40):
    #     client.build_packet_and_fetch_content(f"data/{i % 20}")
    #     print(routers[0].cache.cache.keys().__len__())
    #     assert client.retrieved_content is not None
    #     assert client.retrieved_content.response_data == i % 20
    #     assert client.retrieved_content.inverse_TTL == (4 if i < 20 else 2)
    #     assert len(routers[0].cache.cache.keys()) == min(i + 1, max_cache)


def test_lru_cache():
    max_cache = 5
    cache = ContentCache(max_cache)

    for x in range(max_cache):
        cache.add(f"data/{x}", x)

    for x in range(max_cache):
        assert cache.lookup(f"data/{x}") is not None

    cache.add("data/5", 5)
    assert cache.lookup("data/0") is None
    for x in range(1, max_cache + 1):
        assert cache.lookup(f"data/{x}") is not None

    # Test lookup moves an item to most recent
    cache.lookup("data/1")
    cache.add("data/6", 6)

    assert cache.lookup("data/1") is not None
    assert cache.lookup("data/2") is None

    # Test that adding moves an item to most recent
    cache.add("data/3", 3)
    cache.add("data/7", 7)

    assert cache.lookup("data/3") is not None
    assert cache.lookup("data/4") is None
