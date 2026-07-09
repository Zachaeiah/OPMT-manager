# core/node.py

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Mapping, Self, Union
import uuid

# NodeId is a type alias for a string that represents the unique identifier of a node in the graph. It is used to ensure that node IDs are consistently treated as strings throughout the codebase.
NodeId = str

# NodeLike is a type that can be either a NodeId (string) or a BaseNode instance. This allows for flexibility in methods that accept either a node's ID or the node object itself.
NodeLike = Union[NodeId, "BaseNode"]


@dataclass(slots=True, eq=False)
class BaseNode(ABC):
    """
    Abstract base class for graph nodes.

    Stores:
        - a stable unique ID
        - a readable name
        - forward node IDs
        - backward node IDs

    Subclasses can add domain-specific data while keeping the same graph behavior.
    """

    NODE_TYPE: ClassVar[str] = "base"

    id: NodeId = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""

    # Successors
    forward: set[NodeId] = field(default_factory=set)

    # Predecessors
    backward: set[NodeId] = field(default_factory=set)

    def __post_init__(self) -> None:
        self._validate_base()
        self._validate_extra()

    def __setattr__(self, key: str, value: Any) -> None:
        """ Set an attribute on the node, with special handling for the 'id' attribute to ensure it remains immutable after creation.

        Args:
            key (str): The name of the attribute to set.
            value (Any): The value to assign to the attribute.

        Raises:
            AttributeError: If the 'id' attribute is being modified after creation.
        """
        if key == "id" and hasattr(self, "id"):
            raise AttributeError("Node.id is immutable after creation")

        object.__setattr__(self, key, value)

    def _validate_base(self) -> None:
        """ Check that the base fields are valid.

        Raises:
            TypeError: If the ID is not a string.
            ValueError: If the ID is an empty string.
            TypeError: If the name is not a string.
            TypeError: If the forward neighbors are not a set of strings.
            ValueError: If the forward neighbors include the node's own ID.
            TypeError: If the backward neighbors are not a set of strings.
            ValueError: If the backward neighbors include the node's own ID.
        """
        if not isinstance(self.id, str):
            raise TypeError("id must be a string")

        if not self.id.strip():
            raise ValueError("id cannot be empty")

        if not isinstance(self.name, str):
            raise TypeError("name must be a string")

        self.forward = self._coerce_id_set(self.forward, "forward")
        self.backward = self._coerce_id_set(self.backward, "backward")

        if self.id in self.forward:
            raise ValueError("node cannot be a forward neighbor of itself")

        if self.id in self.backward:
            raise ValueError("node cannot be a backward neighbor of itself")

    @abstractmethod
    def _validate_extra(self) -> None:
        """
        Hook for subclasses to validate their own extra fields.
        Concrete subclasses can simply pass if they have nothing extra to check.
        """
        pass

    @staticmethod
    def new_id() -> NodeId:
        """ Generate a new unique node ID.

        Returns:
            NodeId: A new unique node ID.
        """
        return str(uuid.uuid4())

    @staticmethod
    def _require_node_id(value: Any, field_name: str = "node_id") -> NodeId:
        """ The _require_node_id method ensures that the provided value is a valid node ID (string) and raises appropriate exceptions if it is not.

        Args:
            value (Any): The value to be checked for being a valid node ID.
            field_name (str, optional): The name of the field being checked. Defaults to "node_id".

        Raises:
            TypeError: If the value is not a string.
            ValueError: If the value is an empty string.

        Returns:
            NodeId: The validated node ID.
        """
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        if not value.strip():
            raise ValueError(f"{field_name} cannot be empty")

        return value

    @classmethod
    def _coerce_id_set(cls, value: Any, field_name: str) -> set[NodeId]:
        """ Returns a set of node IDs from an iterable of node IDs or NodeLike objects.

        Args:
            value (Any): An iterable of node IDs or NodeLike objects (NodeId or BaseNode).
            field_name (str): The name of the field being coerced.

        Raises:
            TypeError: If the value is not an iterable of node IDs or NodeLike objects.
            TypeError: If any item in the iterable is not a valid node ID or NodeLike object.

        Returns:
            set[NodeId]: A set of node IDs.
        """
        if isinstance(value, (str, bytes)):
            raise TypeError(f"{field_name} must be an iterable of node IDs, not a string")

        try:
            ids = set(value)
        except TypeError as exc:
            raise TypeError(f"{field_name} must be an iterable of node IDs") from exc

        return {
            cls._require_node_id(node_id, f"{field_name} item")
            for node_id in ids
        }

    @staticmethod
    def _get_node_id(node: NodeLike) -> NodeId:
        """ Returns the node ID of the given node, whether it's a NodeLike object or a string. If it's a NodeLike object, it extracts the ID; if it's a string, it validates that it's a non-empty string.

        Args:
            node (NodeLike): The node for which to get the ID.

        Returns:
            NodeId: The ID of the node.
        """
        if isinstance(node, BaseNode):
            return node.id

        return BaseNode._require_node_id(node)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BaseNode) and self.id == other.id

    def add_forward(self, node: NodeLike) -> None:
        """ Returns the node ID of the given node, whether it's a NodeLike object or a string. 
        If it's a NodeLike object, it extracts the ID; if it's a string, it validates that it's a non-empty string.

        Args:
            node (NodeLike): The node to add as a forward neighbor, which can be either a NodeLike object or a string representing the node ID.
        """
        node_id = self._get_node_id(node)
        self._reject_self_link(node_id)
        self.forward.add(node_id)

    def add_backward(self, node: NodeLike) -> None:
        """ Returns the node ID of the given node, whether it's a NodeLike object or a string.
        If it's a NodeLike object, it extracts the ID; if it's a string, it validates that it's a non-empty string.

        Args:
            node (NodeLike): The node to add as a backward neighbor, which can be either
            a NodeLike object or a string representing the node ID.
        """
        node_id = self._get_node_id(node)
        self._reject_self_link(node_id)
        self.backward.add(node_id)

    def remove_forward(self, node: NodeLike) -> bool:
        """ Returns the node ID of the given node, whether it's a NodeLike object or a string.

        Args:
            node (NodeLike): The node to remove from the forward neighbors, which can be either a NodeLike object or a string representing the node ID.

        Returns:
            bool: True if the node was in the forward neighbors, False otherwise.
        """
        node_id = self._get_node_id(node)
        existed = node_id in self.forward
        self.forward.discard(node_id)
        return existed

    def remove_backward(self, node: NodeLike) -> bool:
        """ Returns the node ID of the given node, whether it's a NodeLike object or a string.

        Args:
            node (NodeLike): The node to remove from the backward neighbors, which can be either a NodeLike object or a string representing the node ID.

        Returns:
            bool: True if the node was in the backward neighbors, False otherwise.
        """
        node_id = self._get_node_id(node)
        existed = node_id in self.backward
        self.backward.discard(node_id)
        return existed

    def connect_to(self, other: BaseNode) -> None:
        """ Connect this node to another node.

        Args:
            other (BaseNode): The node to connect to.
        """
        self.add_forward(other)
        other.add_backward(self)

    def disconnect_from(self, other: BaseNode) -> None:
        """ Disconnect this node from another node.

        Args:
            other (BaseNode): The node to disconnect from.
        """
        self.remove_forward(other)
        other.remove_backward(self)

    def has_forward(self, node: NodeLike) -> bool:
        """ Returns True if the given node is a forward neighbor of this node.

        Args:
            node (NodeLike): The node to check, which can be either a NodeLike object or a string representing the node ID.

        Returns:
            bool: True if the node is a forward neighbor, False otherwise.
        """
        return self._get_node_id(node) in self.forward

    def has_backward(self, node: NodeLike) -> bool:
        """ Returns True if the given node is a backward neighbor of this node.

        Args:
            node (NodeLike): The node to check, which can be either a NodeLike object or a string representing the node ID.

        Returns:
            bool: True if the node is a backward neighbor, False otherwise.
        """
        return self._get_node_id(node) in self.backward

    @property
    def in_degree(self) -> int:
        return len(self.backward)

    @property
    def out_degree(self) -> int:
        return len(self.forward)

    @property
    def is_root(self) -> bool:
        return self.in_degree == 0

    @property
    def is_leaf(self) -> bool:
        return self.out_degree == 0

    def _reject_self_link(self, node_id: NodeId) -> None:
        """ Rejects a node ID if it is the same as this node's ID, preventing self-links in the graph.

        Args:
            node_id (NodeId): The ID of the node to check.

        Raises:
            ValueError: If the node ID is the same as this node's ID.
        """
        if node_id == self.id:
            raise ValueError("node cannot link to itself")

    def to_dict(self) -> dict[str, Any]:
        """ Returns a dictionary representation of the node, including its type, ID, name, and sorted lists of forward and backward neighbor IDs.

        Returns:
            dict[str, Any]: A dictionary containing the node's type, ID, name, and sorted lists of forward and backward neighbor IDs.
        """
        return {
            "node_type": self.NODE_TYPE,
            "id": self.id,
            "name": self.name,
            "forward": sorted(self.forward),
            "backward": sorted(self.backward),
        }

    @classmethod
    def from_dict(cls: type[Self], data: Mapping[str, Any]) -> Self:
        """ Create a node instance from a dictionary representation, ensuring that the provided data is a mapping and contains valid node information.

        Args:
            cls (type[Self]): The class to instantiate.
            data (Mapping[str, Any]): The dictionary containing the node information.

        Returns:
            Self: An instance of the node class initialized with the provided data.
        """
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping")

        return cls(
            id=cls._require_node_id(data.get("id"), "id"),
            name=data.get("name", ""),
            forward=cls._coerce_id_set(data.get("forward", []), "forward"),
            backward=cls._coerce_id_set(data.get("backward", []), "backward"),
        )


@dataclass(slots=True, eq=False)
class Node(BaseNode):
    """
    Concrete generic node.

    Use this when you just need a basic graph node.
    Extend BaseNode or Node when you need domain-specific fields.
    """

    NODE_TYPE: ClassVar[str] = "node"

    def _validate_extra(self) -> None:
        pass