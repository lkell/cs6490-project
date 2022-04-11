from __future__ import annotations

import sys
from typing import Dict, Protocol, Union

import simpy

sys.setrecursionlimit(1000)


class Packet:
    def __init__(self, search: str):
        self.search = search
        self.route = []
        self.response_data: Union[None, int] = None
        self.responder: Union[None, str] = None


class NetworkNode(Protocol):
    """A networked object that can fetch and return data."""

    def fetch_content(self, request: Packet) -> None:
        """Search for the data corresponding with the request packet."""

    def return_content(self, response: Packet) -> None:
        """Return the data reponse to the requesting node."""


class Server(NetworkNode):
    def __init__(self, id: str, router: Router, data: Dict[str, int]):
        self.id = id
        self.router = router
        self.data = data

    def fetch_content(self, request: Packet):
        if request.search in self.data.keys():
            # insert the data to packet
            request.response_data = self.data[request.search]

            # return the packet
            self.return_content(request)
        else:
            # Otherwise we don't have it, do nothing.
            pass

    def return_content(self, response: Packet):
        # Remove the immediate router from the route
        response.route.pop()

        # Give the reponse back to the router
        self.router.return_content(response)


class Client(NetworkNode):
    def __init__(self, id: str, router: Router):
        self.id = id
        self.router = router
        self.retrieved_content: Union[None, Packet] = None

    def build_packet_and_fetch_content(self, search: str):
        # Build the packet
        request = Packet(search)

        self.fetch_content(request)

    def fetch_content(self, request: Packet):
        # Add self to path and send to nearest router
        request.route.append(self.id)
        self.router.fetch_content(request)

    def return_content(self, response: Packet):
        print(f"client {self.id}: got response for {response.search}")
        self.retrieved_content = response


class Router(NetworkNode):
    def __init__(self, id: str):
        self.id = id
        self.neighbors: Union[None, Dict[str, NetworkNode]] = None
        self.cache = Dict[str, int]

    def add_neighbors(self, neighbors: Dict[str, NetworkNode]):
        self.neighbors = neighbors

    def fetch_content(self, request: Packet):
        # Add self as a hop on the path
        request.route.append(self.id)

        # Check the cache
        # TODO
        # if it's in the cache, call return_content directly

        # Check we have neighbors
        if self.neighbors is None:
            raise Exception("Router didn't have neighbors")

        # Else see if our neighbors have it
        for neighbor_id, neighbor in self.neighbors.items():
            if neighbor_id not in request.route:
                neighbor.fetch_content(request)

    def return_content(self, response: Packet):
        # Find the next router closest to the requestor
        next_router = response.route.pop()

        # Check we have neighbors
        if self.neighbors is None:
            raise Exception("Router didn't have neighbors")

        # Send to the next one in the chain
        self.neighbors[next_router].return_content(response)
