# domain/operation.py
import warnings
from typing import Optional
from opmt_manager.Graphs.graph import Graph
from opmt_manager.Graphs.node  import Node
from opmt_manager.domain.task import Task
from opmt_manager.domain._TaskManager import TaskManager


class DanglingEdgeWarning(UserWarning):
    """Raised when an edge references a node that is not present in the graph.

    Indicates inconsistent graph state (e.g., connect/disconnect called with
    missing nodes, or nodes removed without cleaning edges).
    """

    def __init__(
        self,
        src_id: str,
        dst_id: str,
        direction: str,  # "forward" or "backward"
        graph_name: Optional[str] = None,
    ):
        """ Initialize the warning with details about the dangling edge.

        Args:
            src_id (str): ID of the source node for the edge
            dst_id (str): ID of the destination node for the edge
            direction (str): Direction of the edge ("forward" or "backward")
            graph_name (Optional[str], optional): Name of the graph. Defaults to None.
        """
        self.src_id = src_id
        self.dst_id = dst_id
        self.direction = direction
        self.graph_name = graph_name

        msg = (
            f"Dangling edge detected ({direction}): "
            f"{src_id} -> {dst_id} "
            f"(missing {'dst' if direction == 'forward' else 'src'} node)"
        )

        if graph_name:
            msg = f"[{graph_name}] {msg}"

        super().__init__(msg)

def warn_dangling_edge(
    src_id: str,
    dst_id: str,
    direction: str,
    graph_name: Optional[str] = None) -> None:
    """ Then a warning about a dangling edge in the graph, which indicates an inconsistent state where an edge references a node that is not present in the graph.

    Args:
        src_id (str): ID of the source node for the edge
        dst_id (str): ID of the destination node for the edge
        direction (str): Direction of the edge ("forward" or "backward")
        graph_name (Optional[str], optional): Name of the graph. Defaults to None.
    """
    warnings.warn(DanglingEdgeWarning(src_id, dst_id, direction, graph_name),stacklevel=2,)


class Operation(TaskManager):
    """ The operation

    Args:
        TaskManager (_type_): _description_
    """
    def __init__(self, name: str, graph: Graph = None):
        """ Initialize an operation with a name and an empty graph, and add special START and END nodes to the graph.

        Args:
            name (str): Name of the operation
            graph (Graph, optional): Graph to initialize the operation with. Defaults to None.
        """
        self.name: str = name

        if graph is None:
            graph = Graph()

        super().__init__(graph)

        # special nodes
        self.start: Node = Node(name=f"{name}_START")
        self.end: Node = Node(name=f"{name}_END")

        self.graph.add_node(self.start)
        self.graph.add_node(self.end)

    def connect(self, a: Task, b: Task) -> None:
        """ Connect two nodes in the operation graph.  

        Args:
            a (Node): predecessors
            b (Node): successor
        """

        # if a node is not in the graph, add it
        if a.id not in self.graph._nodes:
            self.graph.add_node(a)
        if b.id not in self.graph._nodes:
            self.graph.add_node(b)
        
        # connect the nodes
        self.graph.connect(a.id, b.id)

    def disconnect(self, a: Task, b: Task) -> None:
        """ Disconnect two nodes in the operation graph.  

        Args:
            a (Node): predecessors
            b (Node): successor
        """

        # if a node is not in the graph, add it
        if a.id not in self.graph._nodes:
            self.graph.add_node(a)
        if b.id not in self.graph._nodes:
            self.graph.add_node(b)

        self.graph.disconnect(a.id, b.id)

    def delete_task(self, task_id: str) -> None:
        """ Delete a task from the operation graph.

        Args:
            task_id (str): ID of the task to delete
        """
        self.graph.remove_node(task_id)

    def connect_start(self, task: Task) -> None:
        """ Connect a task to the start node.

        Args:
            task (Task): Task to connect to the start node.
        """
        self.graph.connect(self.start.id, task.id)

    def connect_to_end(self, task: Task) -> None:
        """ Connect a task to the end node.

        Args:
            task (Task): Task to connect to the end node.
        """
        self.graph.connect(task.id, self.end.id)

    def finalize(self) -> None:
        """ Finalize the operation by ensuring all tasks are connected to START and END.
            - Tasks with no predecessors are connected to START
            - Tasks with no successors are connected to END
            - Validates that there are no isolated tasks and that the structure is sound.
        """

        for node_id in list(self.graph._nodes):
            if node_id in (self.start.id, self.end.id):
                continue

            if not self.graph.has_predecessors(node_id):
                self.graph.connect(self.start.id, node_id)

            if not self.graph.has_successors(node_id):
                self.graph.connect(node_id, self.end.id)

    def first_tasks(self) -> set:
        """Tasks directly after START (real entry tasks)"""
        return {
            self.graph.get_node(i)
            for i in self.graph.successors_ids(self.start.id)
        }
    
    def last_tasks(self) -> set:
        """Tasks directly before END (real exit tasks)"""
        return {
            self.graph.get_node(i)
            for i in self.graph.predecessors_ids(self.end.id)
        }
    
    def _entry_nodes(self) -> set[str]:
        """Nodes directly after START"""
        return set(self.start.forward)

    def _exit_nodes(self) -> set[str]:
        """Nodes directly before END"""
        return set(self.end.backward)

    def _append(self, other: "Operation") -> None:
        """ Append another operation to the end of this one (i.e. sequential composition).
        by connecting the last tasks of this operation to the first tasks of the other operation

        Args:
            other (Operation): Operation to append to this one.

        Raises:
            ValueError: If attempting to append the operation to itself
        """

        if other is self:
            raise ValueError("Cannot append operation to itself")
        
        self_exits: set[str] = self._exit_nodes() # Nodes directly before END
        other_entries: set[str] = other._entry_nodes() # Nodes directly after START
        other_exits: set[str] = other._exit_nodes() # Nodes directly before END
        
        #other_graph = other.graph._clone(keep_id = True) # clone to avoid modifying original

        # remove other START and END nodes (we will connect to self's START and END instead)
        for nid in other_entries:
            other.graph.disconnect(other.start.id, nid)

        for nid in other_exits:
            other.graph.disconnect(nid, other.end.id)

        # remove other.start and other.end from the graph (we will not use them)
        other.graph.remove_node(other.start.id)
        other.graph.remove_node(other.end.id)

        # add other graph's nodes and edges to self's graph (no duplicates)
        for node_id, node in other.graph.node_items():
            if node_id not in self.graph._nodes:
                self.graph.add_node(node)

        # connect self's exit nodes to other's entry nodes
        for a in self_exits:
            for b in other_entries:
                self.graph.connect(a, b)

        # connect other's exit nodes to self's END node
        for b in other_exits:
            self.graph.connect(b, self.end.id)

    def _clone(self) -> "Operation":
        """ Return a deep copy of the operation with new node objects but the same structure and durations.

        Returns:
            Operation: A deep copy of the operation with new node objects but the same structure and durations.
        """
        new_op = Operation(name=self.name)

        id_map: dict[str, str] = {}

        # -------------------------
        # 1. Map START/END
        # -------------------------
        id_map[self.start.id] = new_op.start.id
        id_map[self.end.id] = new_op.end.id

        # -------------------------
        # 2. Clone all other nodes
        # -------------------------
        for old_node in self.graph.node_values():
            if old_node.id in (self.start.id, self.end.id):
                continue

            new_node = old_node.clone(keep_id=False)

            new_op.graph.add_node(new_node)
            id_map[old_node.id] = new_node.id

        # -------------------------
        # 3. Recreate edges
        # -------------------------
        for a_id, b_id in self.graph.edges():
            new_op.graph.connect(
                id_map[a_id],
                id_map[b_id]
            )

        return new_op

    def _dfs_forward(self, start_id: str) -> set:
        """ Compute all nodes reachable from START (i.e. are on a path from START)

        Args:
            start_id (str): ID of the START node

        Returns:
            set: Set of node IDs that are reachable from the START node
        """
        visited: set[str] = set()
        stack: list[str] = [start_id]

        while stack:
            current: str = stack.pop()
            for nxt in self.graph.successor_ids(current):
                if nxt not in visited:
                    visited.add(nxt)
                    stack.append(nxt)

        return visited

    def _dfs_backward(self, end_id: str) -> set:
        """ Compute all nodes that can reach END (i.e. are on a path to END)

        Args:
            end_id (str): ID of the END node

        Returns:
            set: Set of node IDs that can reach the END node
        """
        visited: set[str] = set()
        stack: list[str] = [end_id]

        while stack:
            current: str = stack.pop()
            for prev in self.graph.predecessor_ids(current):
                if prev not in visited:
                    visited.add(prev)
                    stack.append(prev)

        return visited

    def validate(self) -> None:
        """ Validate the operation structure to ensure it is sound and can be scheduled.

        Raises:
            ValueError: START node missing
            ValueError: END node missing
            ValueError: Operation has no tasks
            ValueError: Node is not reachable from START
            ValueError: Node cannot reach END
            ValueError: Invalid: START connects directly to END
        """

        if self.start.id not in self.graph._nodes:
            raise ValueError("START node missing")

        if self.end.id not in self.graph._nodes:
            raise ValueError("END node missing")

        if len(self.graph._nodes) <= 2:
            raise ValueError("Operation has no tasks")

        reachable = self._dfs_forward(self.start.id)

        for node_id in self.graph._nodes:
            if node_id != self.start.id and node_id not in reachable:
                raise ValueError(
                    f"Node '{self.graph.get_node(node_id).name}' is not reachable from START"
                )

        can_reach_end = self._dfs_backward(self.end.id)

        for node_id in self.graph._nodes:
            if node_id != self.end.id and node_id not in can_reach_end:
                raise ValueError(
                    f"Node '{self.graph.get_node(node_id).name}' cannot reach END"
                )

        if self.end.id in self.graph.successor_ids(self.start.id):
            raise ValueError("Invalid: START connects directly to END")
        
    def __add__(self, other: "Operation") -> "Operation":
        """ Append another operation to the end of this one (i.e. sequential composition).

        Args:
            other (Operation): Operation to append to this one.

        Returns:
            Operation: A new operation that is the result of appending the other operation to this one
        """
        new_op = self._clone()
        new_op._append(other._clone())

        for node_id, node in self.graph.node_items():
            for succ in node.forward:
                if succ not in self.graph._nodes:
                    warn_dangling_edge(node_id, succ, "forward", self.name)

            for pred in node.backward:
                if pred not in self.graph._nodes:
                    warn_dangling_edge(pred, node_id, "backward", self.name)

        return new_op
        
    def _debug(self) -> None:
        """ Print the operation structure for debugging purposes.
        """
        print(f"\nOperation: {self.name}")

        for node_id, node in self.graph.node_items():
            preds = [
                self.graph.get_node(i).name
                for i in self.graph.predecessors_ids(node_id)
            ]
            succs = [
                self.graph.get_node(i).name
                for i in self.graph.successors_ids(node_id)
            ]

            print(f"{node.name}")
            print(f"  <- {preds}")
            print(f"  -> {succs}")

    def __repr__(self) -> str:
        """ Return a string representation of the operation, showing the name and the structure of the graph.

        Returns:
            str: A string representation of the operation, showing the name and the structure of the graph.
        """
        rep = f"Operation(name={self.name})\n"
        for node_id, node in self.graph.node_items():
            preds = [
                self.graph.get_node(i).name
                for i in self.graph.predecessors_ids(node_id)
            ]
            succs = [
                self.graph.get_node(i).name
                for i in self.graph.successors_ids(node_id)
            ]
            rep += f"{node.name}\n  <- {preds}\n  -> {succs}\n"
        return rep