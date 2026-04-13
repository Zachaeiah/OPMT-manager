# core/node.py

from dataclasses import dataclass, field
from typing import Any, Dict, Set
import uuid

@dataclass(slots=True)
class Node:
    """ Base class for graph nodes. Can be extended with domain-specific data.

    Raises:
        TypeError: If name is not a string

    Returns:
        Node: Node instance
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""

    
    # forward neighbors (successors)
    forward: Set[str] = field(default_factory=set)

    # backward neighbors (predecessors)
    backward: Set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """ Post-initialization to validate the node's name and ensure it's a string.
        Raises:
            TypeError: If name is not a string
        """
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")

    def __hash__(self) -> int:
        """ returns a hash based on the unique id of the node

        Returns:
            int: hash value
        """
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """ compares two nodes based on their unique id

        Args:
            other (object): object to compare with

        Returns:
            bool: boolean indicating if the nodes are equal
        """
        return isinstance(other, Node) and self.id == other.id

    def add_forward(self, node_id: str) -> None:
        """ Adds a forward edge to another node.

        Args:
            node_id (str): ID of the node to add as a forward neighbor
        """
        self.forward.add(node_id)

    def add_backward(self, node_id: str) -> None:
        """ Adds a backward edge to another node

        Args:
            node_id (str): ID of the node to add as a backward neighbor
        """
        self.backward.add(node_id)

    def remove_forward(self, node_id: str) -> None:
        """ Removes a forward edge to another node

        Args:
            node_id (str): ID of the node to remove as a forward neighbor
        """
        self.forward.discard(node_id)

    def remove_backward(self, node_id: str) -> None:
        """ Removes a backward edge to another node

        Args:
            node_id (str): ID of the node to remove as a backward neighbor
        """
        self.backward.discard(node_id)

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dictionary representation of the node, including id and name.

        Returns:
            Dict[str, Any]: dictionary representation of the node
        """
        return {
            "id": self.id,
            "name": self.name
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Node":
        """Creates a Node instance from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing node data.

        Returns:
            Node: A Node instance created from the provided dictionary.
        """
        return Node(
            id=data["id"],
            name=data["name"],
            forward=set(data.get("forward", [])),
            backward=set(data.get("backward", []))
        )