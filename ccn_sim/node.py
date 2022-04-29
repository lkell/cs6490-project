"""This file contains a synchronous version of the simulated network entities."""

from __future__ import annotations

import sys
import typing
from collections import OrderedDict
from typing import Dict, Set, Union

import simpy

sys.setrecursionlimit(1000)


class Packet:
    def __init__(self, search: str):
        self.search = search
        self.response_data: Union[None, int] = None
        self.responder: Union[None, str] = None
        self.inverse_TTL = 0

    def increment_hops(self):
        self.inverse_TTL += 1


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
    def __init__(self, id: str, data: Dict[str, int] = {}, cache_size: int = 20):
        self.id = id
        self.neighbors: Union[None, Dict[str, Node]] = None
        self.cache = ContentCache(cache_size)
        self.pit: Dict[str, Set[str]] = {}
        self.data: Dict[str, int] = data

    def add_neighbors(self, neighbors: Dict[str, Node]):
        self.neighbors = neighbors

    def fetch_content(self, request: Packet, sender_id: str):
        # print(f"{self.id} is incrementing hops")

        if sender_id != self.id:
            request.increment_hops()

        # add the request packet and sender_id to PIT
        if request.search not in self.pit:
            self.pit[request.search] = {sender_id}
        else:
            self.pit[request.search].add(sender_id)
            # TODO: wait for response...

        # if the data is in the cache, call return_content directly
        cache_result = self.cache.lookup(request.search)
        if cache_result is not None:
            request.response_data = cache_result
            return self.return_content(request)

        # if the node owns the data, return it
        if request.search in self.data.keys():
            request.response_data = self.data[request.search]
            return self.return_content(request)

        # Check we have neighbors
        if self.neighbors is None:
            raise Exception("Router didn't have neighbors")

        # Else see if our neighbors have it
        for neighbor_id, neighbor in self.neighbors.items():
            if neighbor_id != sender_id:
                neighbor.fetch_content(request, self.id)

    def return_content(self, response: Packet):
        # print(f"{self.id} is incrementing hops")
        # print(self.neighbors)

        # Add data to cache
        if response.response_data is None:
            raise Exception("Response data is None")
        self.cache.add(response.search, response.response_data)

        # Find everyone that wants this info
        next_routers = self.pit[response.search]

        # Increment the TTL if there is going to be another hop
        if self.id not in next_routers:
            response.increment_hops()

        # Check we have neighbors
        if self.neighbors is None:
            raise Exception("Router didn't have neighbors")

        # print("next routers", next_routers)
        for router in next_routers:
            if router == self.id:
                self.retrieved_content = response
            else:
                self.neighbors[router].return_content(response)

        self.pit.pop(response.search)

    def build_packet_and_fetch_content(self, search: str):
        # Build the packet
        request = Packet(search)
        self.fetch_content(request, self.id)
