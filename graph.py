"""
Graph utility

Author: G Hampton
Date: 28 Feb 2025
"""

from abc import ABC, abstractmethod

import heapq
from collections import deque
from math import inf

# Abstract class!
class BaseAdjacencyStorage(ABC):
    """Implements basics for adjacency list and adjacency matrix to return"""
    def __init__(self):
        raise NotImplementedError("This is an abstract class, please instantiate a child class instead.")
    
    @abstractmethod
    def get_adjacent_nodes(self, node):
        pass

    @abstractmethod
    def are_adjacent(self, node1, node2):
        pass

class AdjacencyList(BaseAdjacencyStorage):
    def __init__(self, adjacencies):
        """
        Receives a dict of the following structure:
        {
            node: [adjacent_nodes]
        }
        """
        self.adjacency = adjacencies
    
    def get_adjacent_nodes(self, node):
        # O(1) to fetch the list
        return self.adjacency[node]
    
    def are_adjacent(self, node_1, node_2):
        # O(d) where d is degree of node_1
        return node_2 in self.adjacency[node_1]

class AdjacencyMatrix(BaseAdjacencyStorage):
    def __init__(self, adjacency_list):
        """
        Receives a dict of the following structure:
        {
            node: [adjacent_nodes]
        }
        """
        nodes = adjacency_list.keys().sorted()
        self.adjacency = {}
        for node in nodes:
            self.adjacency[node] = {}
            neighbours = deque(adjacency_list[node].sorted())
            for other_node in nodes:
                self.adjacency[node][other_node] = False
                if other_node == neighbours[0]:
                    self.adjacency[node][other_node] = True
                    neighbours.popleft()

    def get_adjacent_nodes(self, node):
        # O(n) where n is number of nodes
        return [neighbour for neighbour in self.adjacency[node].keys() if self.adjacency[node][neighbour]]
    
    def are_adjacent(self, node_1, node_2):
        # O(1)
        return [node_1][node_2]

class BaseGraph():
    def __init__(self, adjacency_list, weights):
        """
        Base instance of a graph.

        `adjacency_list` - representation of edges as an adjacency list, e.g.
            {
                "a": [],
                "b": ["a","c"],
                "c": ["a"],
            }
        `weights` - in similar format to adjacency list, e.g.
            {
                "a": {},
                "b": {
                    "a": 4,
                    "c": 2,
                },
                "c": {
                    "a": 1,
                }
            }
        """
        self.nodes = adjacency_list.keys()
        self.adj = adjacency_list
        self.weights = weights

        self._dijkstra_cache = {}

    def get_adjacent(self, node):
        """
        Return a list of all nodes adjacent to `node`.
        """
        return self.adj[node]

    def get_edge_cost(self, node, neighbour):
        """
        Cost of moving from `node` to `neighbour`. Return `inf` if there is no edge connecting them and no cost cached.
        """
        if neighbour not in self.adj[node]:
            if node in self._dijkstra_cache.keys():
                return self._dijkstra_cache[node][neighbour]
            return inf
        return self.weights[node][neighbour]

    def breadth_first_traversal(self, start):
        """
        Performs a breadth-first traversal from `start` and returns the order traversed.
        """
        # Slight modification from https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/
        queue = deque()
        visited = [False] * len(self.adj)
        order = []

        visited[start] = True
        queue.append(start)

        while queue:
            current = queue.popleft()
            order.append(current)

            # Add all fresh neighbours
            for node in self.adj[current]:
                if not visited[node]:
                    visited[node] = True
                    queue.append(node)

        return order

    def depth_first_traversal(self, start):
        pass

    def dijkstra(self, root, replace_cache=False):
        """
        Uses dijkstra's algorithm to find the shortest path from `root` to each other node.

        Makes use of caching to avoid recalculating where possible. Set `replace_cache` to
        `True` to make the search ignore the cache. The function will overwrite the cache
        on completing a fresh search.
        """
        # Return cached value
        if root in self._dijkstra_cache.keys() and not replace_cache:
            return self._dijkstra_cache[root]

        # Perform dijkstra's
        queue = []
        distance = {node: inf for node in self.nodes}
        distance[root] = 0
        heapq.heappush(queue, (0, root))

        while queue:
            distance, current = heapq.heappop(queue)
            for neighbour in self.adj[current]:
                route_through_current = distance[current] + self.get_edge_cost(current, neighbour)
                # Check if the current node provides a shorter path than currently found for the neighbour
                if distance[neighbour] > route_through_current:
                    distance[neighbour] = route_through_current
                    heapq.heappush(queue, (distance[neighbour], neighbour))

        # Add to cache and return
        self._dijkstra_cache[root] = distance
        return distance

    # TODO: Add MST algorithms (why not)
    def prim(self):
        pass

    def kruskal(self):
        pass

class UnweightedGraph(BaseGraph):
    """
    Base instance of an unweighted graph.
    """
    def __init__(self, adjacency_list):
        """
        Create from adjacency list.

        `adjacency_list` - representation of edges as an adjacency list, e.g.
            {
                "a": [],
                "b": ["a","c"],
                "c": ["a"],
            }
        """
        # Kind of cheat by creating a graph with weights of all 1
        weights = {}
        for node in adjacency_list.keys():
            weights[node] = {}
            for neighbour in adjacency_list[node]:
                weights[node][neighbour] = 1

        return super(adjacency_list, weights)