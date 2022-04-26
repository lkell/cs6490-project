from __future__ import annotations

import csv
import os
import sys
import typing
from collections import OrderedDict
from typing import Dict, Final, Literal, Protocol, Set, Tuple, Union

from simpy.core import Environment

sys.setrecursionlimit(1000)

import random


class Packet:
    def __init__(
        self,
        uid: int,
        search: str,
        sender_id: str,
        type: Literal["request", "data"],
        inverse_TTL: int = 0,
        response_data: int = -1,
    ):
        self.search: Final = search
        self.sender_id: Final = sender_id
        self.response_data: Final = response_data
        self.inverse_TTL: Final = inverse_TTL
        self.type: Final = type
        self.uid: Final = uid

    def update_packet(
        self,
        sender_id: str,
        type: Literal["request", "data"],
        response_data: int = -1,
        increment_hops: bool = False,
    ) -> Packet:
        """Create a new copy of packet so that update contents is thread safe."""
        inverse_TTL = self.inverse_TTL + 1 if increment_hops else self.inverse_TTL
        return Packet(
            uid=self.uid,
            search=self.search,
            sender_id=sender_id,
            type=type,
            inverse_TTL=inverse_TTL,
            response_data=response_data,
        )

    def __repr__(self) -> str:
        if self.type == "request":
            return str(
                {
                    "uid": self.uid,
                    "type": self.type,
                    "search": self.search,
                    "last_sender": self.sender_id,
                    "hops": self.inverse_TTL,
                }
            )
        else:
            return str(
                {
                    "uid": self.uid,
                    "type": self.type,
                    "search": self.search,
                    "last_sender": self.sender_id,
                    "hops": self.inverse_TTL,
                    "response_data": self.response_data,
                }
            )


class NetworkNode(Protocol):
    """A networked object that can fetch and return data."""

    def update_queue(self, packet: Packet) -> None:
        """Used to forward packets."""


class Client(NetworkNode):
    def __init__(self, env: Environment, id: str, router: Router):
        self.id = id
        self.router = router
        self.retrieved_content: Union[None, Packet] = None
        self.env = env
        self.responses: list[Packet] = []
        self.request_times: list[Tuple[str, int]] = []
        self.response_times: list[Tuple[str, int]] = []

    def run(self, request_paths: list[str], request_delay: int = 1):
        for search in request_paths:
            uid = random.randrange(10000)
            request = Packet(uid=uid, search=search, sender_id=self.id, type="request")
            self.request_times.append((search, int(self.env.now)))
            self.router.update_queue(request)
            yield self.env.timeout(request_delay)

    def update_queue(self, packet: Packet) -> None:
        self.response_times.append((packet.search, int(self.env.now)))
        self.responses.append(packet)

    def write_request_times(self, sim_path: str) -> None:
        path = f"output/{sim_path}"
        if not os.path.exists(path):
            os.mkdir(path)
        filepath = f"{path}/{self.id}_requests.csv"
        list_to_csv(self.request_times, filepath, header_row=["path", "time"])

    def write_response_times(self, sim_path: str) -> None:
        path = f"output/{sim_path}"
        if not os.path.exists(path):
            os.mkdir(path)
        filepath = f"{path}/{self.id}_responses.csv"
        list_to_csv(self.response_times, filepath, header_row=["path", "time"])

    def __repr__(self) -> str:
        return f"Client <{self.id}>"


def list_to_csv(x: list, path: str, header_row: Union[list[str], None]) -> None:
    with open(path, "w") as f:
        writer = csv.writer(f)
        if header_row:
            writer.writerow(header_row)
        for row in x:
            writer.writerow(row)


class ContentCache:
    def __init__(self, limit: int = 20):
        self.limit = limit
        self.cache: typing.OrderedDict[str, int] = OrderedDict()

    def add(self, key: str, val: int):
        if self.limit == 0:
            return

        if key in self.cache.keys():
            # Pop to move key to the front of the ordered dict if it exists
            self.cache.pop(key)

        if len(self.cache.keys()) >= self.limit:
            self.evict()

        self.cache[key] = val

    def lookup(self, key: str) -> Union[int, None]:
        if key not in self.cache.keys():
            return None
        data = self.cache[key]
        self.add(key, data)
        return data

    def evict(self) -> None:
        self.cache.popitem(last=False)

    def flush(self):
        self.cache = OrderedDict()


class Router(NetworkNode):
    def __init__(
        self, env: Environment, id: str, data: Dict[str, int] = {}, cache_size: int = 20
    ):
        self.id = id
        self.neighbors: Union[None, Dict[str, NetworkNode]] = None
        self.cache = ContentCache(cache_size)
        self.pit: Dict[str, Set[str]] = {}
        self.data: Dict[str, int] = data
        self.env = env
        self.queue: list[Packet] = []
        self.queue_hist: list[Tuple[int, int]] = []

    def log(self, msg: str) -> None:
        print(f"[{self.id}]: {msg}")

    def run(self):
        while True:
            self.queue_hist.append((int(self.env.now), len(self.queue)))
            if len(self.queue) == 0:
                yield self.env.timeout(1)
            else:
                yield self.env.timeout(1)
                self.process_packet(self.queue.pop(0))

    def process_packet(self, packet: Packet):
        if packet.type == "request":
            # self.log("Processing request packet " + str(packet))
            self.process_request(packet)
        else:
            # self.log("Processing response packet " + str(packet))
            self.process_response(packet)

    def add_neighbors(self, neighbors: Dict[str, NetworkNode]):
        if self.neighbors is None:
            self.neighbors = neighbors
        else:
            self.neighbors = self.neighbors | neighbors

    def process_request(self, request: Packet) -> None:
        # add the request packet and sender_id to PIT
        if request.search not in self.pit:
            self.pit[request.search] = {request.sender_id}
        else:
            self.pit[request.search].add(request.sender_id)

        # if the data is in the cache, call return_content directly
        cache_result = self.cache.lookup(request.search)
        if cache_result is not None:
            response = request.update_packet(
                sender_id=self.id,
                type="data",
                response_data=cache_result,
                increment_hops=True,
            )
            self.process_response(response)

        # if the node owns the data, return it
        # print(self.id, request.search, self.data.keys())
        if request.search in self.data.keys():
            # print(1)
            response = request.update_packet(
                sender_id=self.id,
                type="data",
                response_data=self.data[request.search],
                increment_hops=True,
            )
            self.process_response(response)

        # Check we have neighbors
        if self.neighbors is None:
            raise Exception("Router didn't have neighbors")

        # Else see if our neighbors have it
        sender_id = request.sender_id
        for neighbor_id, neighbor in self.neighbors.items():
            if neighbor_id != sender_id:
                new_request = request.update_packet(
                    sender_id=self.id, type="request", increment_hops=True
                )
                neighbor.update_queue(new_request)

    def process_response(self, response: Packet) -> None:
        # Add data to cache
        if response.response_data is None:
            raise Exception("Response data is None")
        self.cache.add(response.search, response.response_data)

        # self.log("pit:" + str(self.pit))
        if response.search not in self.pit.keys():
            return
        next_routers = self.pit[response.search]

        # Check we have neighbors
        if self.neighbors is None:
            raise Exception("Router didn't have neighbors")

        for router in next_routers:
            new_response = response.update_packet(
                sender_id=self.id,
                type="data",
                response_data=response.response_data,
                increment_hops=True,
            )
            self.neighbors[router].update_queue(new_response)

        self.pit.pop(response.search)

    def update_queue(self, packet: Packet) -> None:
        self.queue.append(packet)

    def write_queue_hist(self, sim_path: str) -> None:
        path = f"output/{sim_path}"
        if not os.path.exists(path):
            os.mkdir(path)
        filepath = f"{path}/{self.id}_queue.csv"
        list_to_csv(self.queue_hist, filepath, header_row=["time", "queue_size"])

    def __repr__(self) -> str:
        return f"Router <{self.id}>"


def build_simple_network(env: Environment, n_routers: int = 100):
    if n_routers < 2:
        raise ValueError("n_routers must be at least 2")

    routers = [Router(env, f"r-{i}") for i in range(n_routers - 1)]
    routers.append(Router(env, f"r-{n_routers - 1}", {"data/0": -1}))
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

    client = Client(env, "c-0", routers[0])
    routers[0].add_neighbors({"c-0": client, "r-1": routers[1]})

    return client, routers
