# core/graph.py

from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import replace
from typing import Any, Generic, Iterable, Iterator, Mapping, TypeVar

from .node import BaseNode, Node, NodeId, NodeLike

# NodeT is a type variable that represents a node type, which must be a subclass of BaseNode. This allows the Graph class to be generic and work with any specific node type that extends BaseNode.
NodeT = TypeVar("NodeT", bound=BaseNode)


class Graph(Generic[NodeT]):
    """
    Directed graph of nodes.

    The graph owns edge consistency:
        - if A.forward contains B
        - then B.backward must contain A

    Nodes store edge IDs only.
    """

    def __init__(self, nodes: Iterable[NodeT] | None = None) -> None:
        """Initialize the graph.

        Args:
            nodes (Iterable[NodeT] | None, optional): Initial nodes for the graph. Defaults to None.
        """
        self._nodes: dict[NodeId, NodeT] = {}

        if nodes is not None:
            for node in nodes:
                self.add_node(node, validate_edges=False)

            self.validate_integrity()

    def __len__(self) -> int:
        return len(self._nodes)

    def __bool__(self) -> bool:
        return bool(self._nodes)

    def __contains__(self, node: NodeLike) -> bool:
        return self._get_node_id(node) in self._nodes

    def __iter__(self) -> Iterator[NodeT]:
        return iter(self._nodes.values())

    def __repr__(self) -> str:
        return f"{type(self).__name__}(nodes={len(self._nodes)}, edges={self.edge_count})"

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return sum(len(node.forward) for node in self._nodes.values())

    def add_node(self, node: NodeT, *, validate_edges: bool = True) -> None:
        """ Add a node to the graph.

        Args:
            node (NodeT): The node
            validate_edges (bool, optional): Whether to validate the node's edges. Defaults to True.

        Raises:
            TypeError: If the node is not a BaseNode.
            ValueError: If the node already exists in the graph.
        """
        if not isinstance(node, BaseNode):
            raise TypeError("node must be a BaseNode")

        if node.id in self._nodes:
            raise ValueError(f"node already exists: {node.id}")

        if validate_edges:
            self._validate_external_edges(node)

        self._nodes[node.id] = node

    def add_nodes(self, nodes: Iterable[NodeT], *, validate_edges: bool = True) -> None:
        """ Add multiple nodes to the graph.

        Args:
            nodes (Iterable[NodeT]): The nodes to add.
            validate_edges (bool, optional): Whether to validate the nodes' edges. Defaults to True.
        """
        for node in nodes:
            self.add_node(node, validate_edges=validate_edges)

        if validate_edges:
            self.validate_integrity()

    def remove_node(self, node: NodeLike) -> NodeT:
        """ Remove a node from the graph, along with its edges.

        Args:
            node (NodeLike): The node to remove.

        Returns:
            NodeT: The removed node.
        """
        node_id = self._get_node_id(node)
        target = self._require_node(node_id)

        for succ_id in list(target.forward):
            if succ_id in self._nodes:
                self._nodes[succ_id].remove_backward(node_id)

        for pred_id in list(target.backward):
            if pred_id in self._nodes:
                self._nodes[pred_id].remove_forward(node_id)

        removed = self._nodes.pop(node_id)

        # Clear links from the removed node so it is detached.
        removed.forward.clear()
        removed.backward.clear()

        return removed

    def clear(self) -> None:
        self._nodes.clear()

    def get_node(self, node: NodeLike) -> NodeT:
        return self._require_node(self._get_node_id(node))

    def try_get_node(self, node: NodeLike) -> NodeT | None:
        return self._nodes.get(self._get_node_id(node))

    def connect(self, a: NodeLike, b: NodeLike) -> bool:
        """ Set A -> B.

        Args:
            a (NodeLike): The first node.
            b (NodeLike): The second node.

        Returns:
            bool: True if a new edge was added, False if the edge already existed.
        """
        a_id = self._get_node_id(a)
        b_id = self._get_node_id(b)

        self._reject_self_edge(a_id, b_id)

        a_node = self._require_node(a_id)
        b_node = self._require_node(b_id)

        if b_id in a_node.forward:
            return False

        a_node.add_forward(b_id)
        b_node.add_backward(a_id)

        return True

    def disconnect(self, a: NodeLike, b: NodeLike, *, strict: bool = False) -> bool:
        """ Set A -/-> B.

        Args:
            a (NodeLike): The first node.
            b (NodeLike): The second node.
            strict (bool, optional): If True, raises ValueError when the edge does not exist. Defaults to False.

        Raises:
            ValueError: If strict is True and the edge does not exist.

        Returns:
            bool: True if an edge was removed, False if no edge existed.
        """
        a_id = self._get_node_id(a)
        b_id = self._get_node_id(b)

        a_node = self._require_node(a_id)
        b_node = self._require_node(b_id)

        existed = b_id in a_node.forward

        if strict and not existed:
            raise ValueError(f"edge does not exist: {a_id} -> {b_id}")

        a_node.remove_forward(b_id)
        b_node.remove_backward(a_id)

        return existed

    def has_edge(self, a: NodeLike, b: NodeLike) -> bool:
        """ Check if there is an edge from A to B.

        Args:
            a (NodeLike): The first node.
            b (NodeLike): The second node.

        Returns:
            bool: True if there is an edge from A to B, False otherwise.
        """
        a_id = self._get_node_id(a)
        b_id = self._get_node_id(b)

        self._require_node(a_id)
        self._require_node(b_id)

        return b_id in self._nodes[a_id].forward

    def replace_edge(self, a: NodeLike, old: NodeLike, new: NodeLike) -> None:
        """
        Replace A -> OLD with A -> NEW.

        Args:
            a (NodeLike): The first node.
            old (NodeLike): The old second node.
            new (NodeLike): The new second node.

        Raises:
            ValueError: If the old edge does not exist.
        """
        a_id = self._get_node_id(a)
        old_id = self._get_node_id(old)
        new_id = self._get_node_id(new)

        self._reject_self_edge(a_id, new_id)

        self._require_node(a_id)
        self._require_node(old_id)
        self._require_node(new_id)

        if not self.has_edge(a_id, old_id):
            raise ValueError(f"edge does not exist: {a_id} -> {old_id}")

        if old_id == new_id:
            return

        self.disconnect(a_id, old_id, strict=True)
        self.connect(a_id, new_id)

    def insert_between(self, a: NodeLike, b: NodeLike, x: NodeLike) -> None:
        """ Create A -> X -> B, replacing A -> B.

        Args:
            a (NodeLike): The first node.
            b (NodeLike): The second node.
            x (NodeLike): The node to insert between A and B.

        Raises:
            ValueError: If the edge A -> B does not exist or if X is the same as A or B.
            ValueError: If any of the nodes are not in the graph.
        """
        a_id = self._get_node_id(a)
        b_id = self._get_node_id(b)
        x_id = self._get_node_id(x)

        self._require_node(a_id)
        self._require_node(b_id)
        self._require_node(x_id)

        if x_id in {a_id, b_id}:
            raise ValueError("insert node must be different from both edge nodes")

        if not self.has_edge(a_id, b_id):
            raise ValueError(f"edge does not exist: {a_id} -> {b_id}")

        self.disconnect(a_id, b_id, strict=True)
        self.connect(a_id, x_id)
        self.connect(x_id, b_id)

    def successors(self, node: NodeLike) -> set[NodeT]:
        """ Create a set of successor nodes for the given node.

        Args:
            node (NodeLike): The node for which to find successors.

        Returns:
            set[NodeT]: A set of successor nodes.
        """
        node_id = self._get_node_id(node)
        target = self._require_node(node_id)

        return {
            self._require_node(succ_id)
            for succ_id in target.forward
        }

    def predecessors(self, node: NodeLike) -> set[NodeT]:
        """ Generate a set of predecessor nodes for the given node.

        Args:
            node (NodeLike): The node for which to find predecessors.

        Returns:
            set[NodeT]: A set of predecessor nodes.
        """
        node_id = self._get_node_id(node)
        target = self._require_node(node_id)

        return {
            self._require_node(pred_id)
            for pred_id in target.backward
        }

    def successor_ids(self, node: NodeLike) -> set[NodeId]:
        return set(self._require_node(self._get_node_id(node)).forward)

    def predecessor_ids(self, node: NodeLike) -> set[NodeId]:
        return set(self._require_node(self._get_node_id(node)).backward)

    def neighbors(self, node: NodeLike) -> set[NodeT]:
        node_id = self._get_node_id(node)
        target = self._require_node(node_id)

        neighbor_ids = target.forward | target.backward

        return {
            self._require_node(neighbor_id)
            for neighbor_id in neighbor_ids
        }

    def has_successors(self, node: NodeLike) -> bool:
        return bool(self._require_node(self._get_node_id(node)).forward)

    def has_predecessors(self, node: NodeLike) -> bool:
        return bool(self._require_node(self._get_node_id(node)).backward)

    def in_degree(self, node: NodeLike) -> int:
        return len(self._require_node(self._get_node_id(node)).backward)

    def out_degree(self, node: NodeLike) -> int:
        return len(self._require_node(self._get_node_id(node)).forward)

    def degree(self, node: NodeLike) -> int:
        target = self._require_node(self._get_node_id(node))
        return len(target.forward) + len(target.backward)

    def roots(self) -> list[NodeT]:
        """
        Nodes with no predecessors.
        """
        return [
            node
            for node in self._nodes.values()
            if not node.backward
        ]

    def leaves(self) -> list[NodeT]:
        """
        Nodes with no successors.
        """
        return [
            node
            for node in self._nodes.values()
            if not node.forward
        ]

    def node_ids(self) -> list[NodeId]:
        return list(self._nodes.keys())

    def node_items(self) -> list[tuple[NodeId, NodeT]]:
        return list(self._nodes.items())

    def node_values(self) -> list[NodeT]:
        return list(self._nodes.values())

    def edges(self) -> Iterator[tuple[NodeId, NodeId]]:
        for a_id, node in self._nodes.items():
            for b_id in node.forward:
                yield a_id, b_id

    def edge_list(self) -> list[tuple[NodeId, NodeId]]:
        return list(self.edges())

    def topological_sort(self) -> list[NodeT]:
        """
        Return nodes in dependency order.

        Raises:
            ValueError: If the graph contains a cycle.
        """
        in_degree = {
            node_id: len(node.backward)
            for node_id, node in self._nodes.items()
        }

        queue = deque(
            node_id
            for node_id, degree in in_degree.items()
            if degree == 0
        )

        ordered: list[NodeT] = []

        while queue:
            node_id = queue.popleft()
            node = self._nodes[node_id]
            ordered.append(node)

            for succ_id in node.forward:
                in_degree[succ_id] -= 1

                if in_degree[succ_id] == 0:
                    queue.append(succ_id)

        if len(ordered) != len(self._nodes):
            raise ValueError("graph contains a cycle")

        return ordered

    def has_cycle(self) -> bool:
        try:
            self.topological_sort()
            return False
        except ValueError:
            return True

    def validate_integrity(self) -> None:
        """
        Validate that all edges are complete and reciprocal.

        Raises:
            ValueError:
                If a dangling, missing, self, or one-sided edge exists.
        """
        for node_id, node in self._nodes.items():
            if node.id != node_id:
                raise ValueError(f"node key/id mismatch: key={node_id}, node.id={node.id}")

            if node_id in node.forward:
                raise ValueError(f"self edge found in forward set: {node_id}")

            if node_id in node.backward:
                raise ValueError(f"self edge found in backward set: {node_id}")

            for succ_id in node.forward:
                if succ_id not in self._nodes:
                    raise ValueError(f"dangling forward edge: {node_id} -> {succ_id}")

                if node_id not in self._nodes[succ_id].backward:
                    raise ValueError(f"missing backward edge: {succ_id} <- {node_id}")

            for pred_id in node.backward:
                if pred_id not in self._nodes:
                    raise ValueError(f"dangling backward edge: {pred_id} -> {node_id}")

                if node_id not in self._nodes[pred_id].forward:
                    raise ValueError(f"missing forward edge: {pred_id} -> {node_id}")

    def clone(self, *, keep_ids: bool = True) -> "Graph[NodeT]":
        """
        Deep copy the graph.

        Args:
            keep_ids:
                True:
                    Preserve node IDs.

                False:
                    Generate new node IDs and remap all edges.
        """
        if keep_ids:
            return deepcopy(self)

        id_map = {
            old_id: BaseNode.new_id()
            for old_id in self._nodes
        }

        new_graph: Graph[NodeT] = Graph()

        for old_id, node in self._nodes.items():
            cloned = deepcopy(node)

            new_forward = {
                id_map[succ_id]
                for succ_id in cloned.forward
            }

            new_backward = {
                id_map[pred_id]
                for pred_id in cloned.backward
            }

            cloned = replace(
                cloned,
                id=id_map[old_id],
                forward=new_forward,
                backward=new_backward,
            )

            new_graph.add_node(cloned, validate_edges=False)

        new_graph.validate_integrity()
        return new_graph

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [
                node.to_dict()
                for node in self._nodes.values()
            ]
        }

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
        *,
        node_cls: type[NodeT] = Node,
    ) -> "Graph[NodeT]":
        """ Returns a Graph instance from a dictionary representation.

        Args:
            data (Mapping[str, Any]): The dictionary representation of the graph.
            node_cls (type[NodeT], optional): The node class used to rebuild each node. Defaults to Node.

        Raises:
            TypeError: If the data is not a mapping or if the nodes are not a list.
            TypeError: If a node is not of the correct type.


        Returns:
            Graph[NodeT]: A Graph instance reconstructed from the dictionary representation.
        """
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping")

        raw_nodes = data.get("nodes", [])

        if not isinstance(raw_nodes, list):
            raise TypeError("data['nodes'] must be a list")

        graph: Graph[NodeT] = cls()

        for raw_node in raw_nodes:
            node = node_cls.from_dict(raw_node)
            graph.add_node(node, validate_edges=False)

        graph.validate_integrity()
        return graph

    def _validate_external_edges(self, node: NodeT) -> None:
        """ Returns True if all edges of the node are valid and exist in the graph.

        Args:
            node (NodeT): The node to validate.
        """
        for succ_id in node.forward:
            self._require_node(succ_id)

        for pred_id in node.backward:
            self._require_node(pred_id)

    @staticmethod
    def _get_node_id(node: NodeLike) -> NodeId:
        """ Get the ID of a node, whether it's a NodeId or a BaseNode instance.

        Args:
            node (NodeLike): The node or node ID to retrieve the ID from.

        Returns:
            NodeId: The ID of the node.
        """
        if isinstance(node, BaseNode):
            return node.id

        return BaseNode._require_node_id(node)

    def _require_node(self, node_id: NodeId) -> NodeT:
        """ Check that the node exists in the graph and return it.

        Args:
            node_id (NodeId): The ID of the node to retrieve.

        Raises:
            KeyError: If the node with the specified ID is not found.

        Returns:
            NodeT: The node with the specified ID.
        """
        node_id = BaseNode._require_node_id(node_id)

        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise KeyError(f"node not found: {node_id}") from exc

    @staticmethod
    def _reject_self_edge(a_id: NodeId, b_id: NodeId) -> None:
        """ Check that the edge does not connect a node to itself.

        Args:
            a_id (NodeId): The ID of the first node.
            b_id (NodeId): The ID of the second node.

        Raises:
            ValueError: If the edge connects a node to itself.
        """
        if a_id == b_id:
            raise ValueError("self-connections are not allowed")