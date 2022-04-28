from __future__ import annotations

import csv
import os
import sys
import typing
from collections import OrderedDict
from multiprocessing.sharedctypes import Value
from typing import Dict, Final, Literal, Set, Tuple, Union

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


class Node:
    def __init__(
        self,
        env: Environment,
        id: str,
        data: Dict[str, int] = {},
        cache_size: int = 20,
        is_client: bool = False,
        simulate_ip: bool = False,
    ):
        self.id = id
        self.neighbors: Union[None, Dict[str, Node]] = None
        self.pit: Dict[str, Set[str]] = {}
        self.data: Dict[str, int] = data
        self.env = env
        self.queue: list[Packet] = []
        self.queue_hist: list[Tuple[int, int]] = []
        self.request_times: list[Tuple[str, int]] = []
        self.response_times: list[Tuple[str, int]] = []
        self.responses: list[Packet] = []
        self.is_client = is_client
        self.FIB: Dict[str, Tuple[str, int]] = {}
        self.simulate_ip = simulate_ip
        self.cache = ContentCache(0) if self.simulate_ip else ContentCache(cache_size)

    def log(self, msg: str) -> None:
        print(f"[{self.id}]: {msg}")

    def init_routing_broadcast(self):
        if self.neighbors is None:
            raise ValueError("Neighbors must be initialiazed")

        for path in self.data.keys():
            for neighbor in self.neighbors.values():
                neighbor.rebroadcast(self.id, path, distance=0)

    def rebroadcast(self, router_id: str, path: str, distance: int):
        if self.neighbors is None:
            raise ValueError("Neighbors must be initialiazed")

        # Update data entry with closest neighbor
        if path not in self.FIB.keys():
            self.FIB[path] = router_id, distance
        else:
            if distance < self.FIB[path][1]:
                self.FIB[path] = router_id, distance
        # pass it on to the next router
        for neighbor_id in self.neighbors.keys():
            if neighbor_id != router_id:
                self.neighbors[neighbor_id].rebroadcast(self.id, path, distance + 1)

    def run(
        self,
        request_paths: list[str] = [],
        request_delay: int = 1,
    ):
        if self.neighbors is None:
            raise ValueError("Neighbors is not set")

        if self.is_client:
            for search in request_paths:
                uid = random.randrange(10000)
                request = Packet(
                    uid=uid, search=search, sender_id=self.id, type="request"
                )
                self.request_times.append((search, int(self.env.now)))
                for neighbor in self.neighbors.values():
                    neighbor.update_queue(request)
                yield self.env.timeout(request_delay)
        else:
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

    def add_neighbors(self, neighbors: Dict[str, Node]):
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
            if not self.simulate_ip:
                return

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
            return

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
            return

        # Check we have neighbors
        if self.neighbors is None:
            raise Exception("Router didn't have neighbors")

        # Else see if our neighbors have it
        sender_id = request.sender_id
        neighbor_id = self.FIB[request.search][0]
        new_request = request.update_packet(
            sender_id=self.id, type="request", increment_hops=True
        )
        self.neighbors[neighbor_id].update_queue(new_request)

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
        self.response_times.append((packet.search, int(self.env.now)))
        self.responses.append(packet)
        self.queue.append(packet)

    def write_queue_hist(self, sim_path: str) -> None:
        path = f"output/{sim_path}"
        if not os.path.exists(path):
            os.mkdir(path)
        filepath = f"{path}/{self.id}_queue.csv"
        list_to_csv(self.queue_hist, filepath, header_row=["time", "queue_size"])

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
        return f"Node <{self.id}>"
