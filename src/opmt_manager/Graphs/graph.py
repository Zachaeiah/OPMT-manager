# core/graph.py

from typing import Dict, Set
from .node import Node


class Graph:
    def __init__(self):
        """ Initialize graph
        """
        self._nodes: Dict[str, Node] = {}

    def add_node(self, node: Node) -> None:
        """ Add node to graph

        Args:
            node (Node): Node to add to graph

        Raises:
            ValueError: If a node with the same ID already exists
        """
        if node.id in self._nodes:
            raise ValueError(f"Node {node.id} already exists")
        self._nodes[node.id] = node

    def remove_node(self, node_id: str) -> None:
        """ Remove node from graph

        Args:
            node_id (str): ID of the node to remove

        Raises:
            KeyError: If the node does not exist
        """
        self._validate(node_id)

        node = self._nodes[node_id]

        # remove from neighbors
        for succ in node.forward:
            self._nodes[succ].remove_backward(node_id)

        for pred in node.backward:
            self._nodes[pred].remove_forward(node_id)

        del self._nodes[node_id]

    def get_node(self, node_id: str) -> Node:
        """ Get node by ID

        Args:
            node_id (str): ID of the node to retrieve

        Raises:
            KeyError: If the node does not exist

        Returns:
            Node: The node with the specified ID
        """
        self._validate(node_id)
        return self._nodes[node_id]
    
    def has_edge(self, a_id: str, b_id: str) -> bool:
        """ Check if an edge exists between two nodes

        Args:
            a_id (str): ID of the first node
            b_id (str): ID of the second node

        Returns:
            bool: True if the edge exists, False otherwise
        """
        self._validate(a_id)
        self._validate(b_id)
        return b_id in self._nodes[a_id].forward

    def connect(self, a_id: str, b_id: str) -> None:
        """ Connect two nodes

        Args:
            a_id (str): ID of the first node
            b_id (str): ID of the second node

        Raises:
            KeyError: If either node does not exist
            ValueError: If attempting to connect a node to itself
        """
        self._validate(a_id)
        self._validate(b_id)

        if a_id == b_id:
            raise ValueError("Self-connections are not allowed")

        a = self._nodes[a_id]
        b = self._nodes[b_id]

        a.add_forward(b_id)
        b.add_backward(a_id)
        
    def disconnect(self, a_id: str, b_id: str):
        """ Disconnect two nodes

        Args:
            a_id (str): ID of the first node
            b_id (str): ID of the second node
        """
        self._validate(a_id)
        self._validate(b_id)
        self._validate(a_id)
        self._validate(b_id)

        self._nodes[a_id].remove_forward(b_id)
        self._nodes[b_id].remove_backward(a_id)

    def replace_edge(self, a_id: str, old_id: str, new_id: str) -> None:
        """ Replace an edge from a_id -> old_id with a new edge from a_id -> new_id. 
        This is a common operation during task decomposition where we want to replace 
        an abstract task with a more detailed subgraph.

        Args:
            a_id (str): ID of the source node for the edge to replace
            old_id (str): ID of the target node for the edge to replace
            new_id (str): ID of the target node for the new edge to add

        Raises:
            ValueError: If attempting to create a self-connection or if the old edge does not exist
            ValueError: If any of the node IDs do not exist in the graph
        """
        self._validate(a_id)
        self._validate(old_id)
        self._validate(new_id)

        if a_id == new_id:
            raise ValueError("Self-connections are not allowed")

        # Only modify if edge exists
        if old_id not in self._nodes[a_id].forward:
            raise ValueError(f"No edge {a_id} -> {old_id} to replace")

        # remove old
        self.disconnect(a_id, old_id)

        # add new
        self.connect(a_id, new_id)

    def insert_between(self, a_id: str, b_id: str, x_id: str):
        """ Insert a new node x between nodes a and b by replacing the edge from a to b with edges from a to x and x to b.

        Args:
            a_id (str): ID of the first node
            b_id (str): ID of the second node
            x_id (str): ID of the new node to insert
        """
        self.disconnect(a_id, b_id)
        self.connect(a_id, x_id)
        self.connect(x_id, b_id)

    def successors(self, node_id: str) -> Set[Node]:
        """ Get all successors of a node

        Args:
            node_id (str): ID of the node to retrieve successors for

        Returns:
            Set[Node]: A set of successor nodes
        """
        self._validate(node_id)
        return {self._nodes[i] for i in self._nodes[node_id].forward}

    def predecessors(self, node_id: str) -> Set[Node]:
        """ Get all predecessors of a node

        Args:
            node_id (str): ID of the node to retrieve predecessors for

        Returns:
            Set[Node]: A set of predecessor nodes
        """
        self._validate(node_id)
        return {self._nodes[i] for i in self._nodes[node_id].backward}
    
    def successors_ids(self, node_id: str) -> Set[str]:
        """ Get IDs of all successors of a node

        Args:
            node_id (str): ID of the node to retrieve successor IDs for

        Returns:
            Set[str]: A set of successor node IDs
        """
        self._validate(node_id)
        return set(self._nodes[node_id].forward)

    def predecessors_ids(self, node_id: str) -> Set[str]:
        """ Get IDs of all predecessors of a node

        Args:
            node_id (str): ID of the node to retrieve predecessor IDs for

        Returns:
            Set[str]: A set of predecessor node IDs
        """
        self._validate(node_id)
        return set(self._nodes[node_id].backward)

    def has_successors(self, node_id: str) -> bool:
        """Check if a node has any successors

        Args:
            node_id (str): ID of the node to check

        Returns:
            bool: True if the node has at least one successor, False otherwise
        """
        return len(self._nodes[node_id].forward) > 0

    def has_predecessors(self, node_id: str) -> bool:
        """Check if a node has any predecessors

        Args:
            node_id (str): ID of the node to check

        Returns:
            bool: True if the node has at least one predecessor, False otherwise
        """
        return len(self._nodes[node_id].backward) > 0

    def node_ids(self) -> list[str]:
        """ Return list of node IDs in the graph

        Returns:
            list[str]: List of node IDs in the graph
        """
        return list(self._nodes.keys())

    def node_items(self) -> list[tuple[str, Node]]:
        """ Return list of node items in the graph

        Returns:
            list[tuple[str, Node]]: List of node items in the graph
        """

        return list(self._nodes.items())

    def node_values(self) -> list[Node]:
        """ Return list of node values in the graph

        Returns:
            list[Node]: List of nodes in the graph
        """
        return list(self._nodes.values())

    def neighbors(self, node_id: str) -> Set[Node]:
        """ Get all neighbors of a node (both forward and backward)

        Args:
            node_id (str): ID of the node to retrieve neighbors for

        Returns:
            Set[Node]: A set of neighboring nodes
        """
        self._validate(node_id)
        node = self._nodes[node_id]
        ids = node.forward | node.backward
        return {self._nodes[i] for i in ids}
    
    def edges(self):
        """
        Iterate over all directed edges in the graph.

        Yields:
            tuple[str, str]: Tuples representing directed edges (a_id -> b_id)
        """
        for a_id, node in self._nodes.items():
            for b_id in node.forward:
                yield a_id, b_id

    def degree(self, node_id: str) -> int:
        """ Get the degree (number of neighbors) of a node.

        Args:
            node_id (str):  ID of the node to retrieve degree for

        Returns:
            int: Degree of the node (number of neighbors)
        """
        self._validate(node_id)
        node = self._nodes[node_id]
        return len(node.forward) + len(node.backward)

    def _clone(self, keep_id: bool = True) -> "Graph":
        """[INTERNAL] Create a deep copy of the graph. This is intended for internal use only.
        Useful for operations that require a modified version of the graph without altering the original.

        Args:
            keep_id (bool): If True, preserves the same node IDs in the cloned graph (dangerous if you plan to merge graphs or add new nodes). Default True = same IDs, False = new unique IDs. Use with caution.   

        Returns:
            Graph: A deep copy of the graph
        """
        new_graph = Graph()
        for node_id, node in self._nodes.items():
            new_graph.add_node(node._clone(keep_id=keep_id))
        return new_graph

    def _validate(self, node_id: str):
        """ Validate that a node exists in the graph

        Args:
            node_id (str): ID of the node to validate

        Raises:
            KeyError: If the node does not exist
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} not found")