from ccn_sim import __version__
from ccn_sim.node import ContentCache, Node


def test_version():
    assert __version__ == "0.1.0"


def test_simple_network():
    # test a simple [Node <-> Node <-> Server (Node)] setup

    data = 123

    client, routers = build_simple_network(2)
    routers[1].data = {"data/0": data}

    client.build_packet_and_fetch_content("data/0")

    assert client.retrieved_content is not None
    assert client.retrieved_content.response_data == data

    assert client.retrieved_content.inverse_TTL == 4


def build_simple_network(n_routers: int = 100):
    if n_routers < 2:
        raise ValueError("n_routers must be at least 2")

    routers = [Node(f"r-{i}") for i in range(n_routers - 1)]
    routers.append(Node(f"r-{n_routers - 1}", {"data/0": -1}))
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

    client = Node("c-0", cache_size=0)
    client.add_neighbors({"r-0": routers[0]})
    routers[0].add_neighbors({"c-0": client, "r-1": routers[1]})

    return client, routers


def test_simple_network_long():
    # test a simple network with chain of routers [Node <-> Nodes <-> Server]

    data = 123

    (
        client,
        routers,
    ) = build_simple_network(100)
    routers[99].data = {"data/0": data}

    # No cached data
    client.build_packet_and_fetch_content("data/0")

    assert routers[0].cache.lookup("data/0") == data
    assert routers[0].cache.lookup("data/1") is None

    assert client.retrieved_content is not None
    assert client.retrieved_content.response_data == data

    assert client.retrieved_content.inverse_TTL == 200

    # Use cached data
    client.build_packet_and_fetch_content("data/0")

    assert routers[0].cache.lookup("data/0") == data
    assert routers[0].cache.lookup("data/1") is None

    assert client.retrieved_content is not None
    assert client.retrieved_content.response_data == data

    assert client.retrieved_content.inverse_TTL == 2


def test_cache():
    max_cache = 20

    client, routers = build_simple_network(2)

    assert len(routers[0].cache.cache.keys()) == 0

    # Add the data
    for i in range(21):
        routers[1].data[f"data/{i}"] = i

    # ASSUMES FIFO CACHE (works with LRU)
    # Request 21 items twice and make sure that the cache expires
    for i in range(42):
        print("\n\n\n\n\n")
        client.build_packet_and_fetch_content(f"data/{i % 21}")
        assert client.retrieved_content is not None
        assert client.retrieved_content.response_data == i % 21
        assert client.retrieved_content.inverse_TTL == 4
        assert len(routers[0].cache.cache.keys()) == min(i + 1, max_cache)

    routers[0].cache.flush()
    assert len(routers[0].cache.cache.keys()) == 0

    # Test for cache hits
    for i in range(40):
        client.build_packet_and_fetch_content(f"data/{i % 20}")
        print(routers[0].cache.cache.keys().__len__())
        assert client.retrieved_content is not None
        assert client.retrieved_content.response_data == i % 20
        assert client.retrieved_content.inverse_TTL == (4 if i < 20 else 2)
        assert len(routers[0].cache.cache.keys()) == min(i + 1, max_cache)


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
