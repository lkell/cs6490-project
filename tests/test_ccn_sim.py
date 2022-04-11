from ccn_sim import __version__
from ccn_sim.node import Client, Router, Server


def test_version():
    assert __version__ == "0.1.0"


def test_simple_network():
    # test a simple [Client <-> Router <-> Server] setup

    data = 123

    router = Router("r-0")
    client = Client("c-0", router)
    server = Server("s-0", router, {"data/0": data})

    router.add_neighbors({"c-0": client, "s-0": server})

    client.build_packet_and_fetch_content("data/0")

    assert client.retrieved_content is not None
    assert client.retrieved_content.response_data == data
