from opmt_manager.Graphs.graph import Graph
from opmt_manager.domain.task import Task

class TaskManager:
    def __init__(self, graph: Graph = None):
        """ Initialize the OperationTaskManager with a graph. 
        The OperationTaskManager is responsible for managing tasks within an operation, 
        including adding tasks, retrieving tasks, and applying scheduling times to tasks.

        Args:
            graph (Graph, optional): _description_. Defaults to None.
        """
        if graph is None:
            graph = Graph()

        self.graph = graph 

    def add_task(self, task: Task) -> None:
        """ Add task to the operation by adding it to the graph

        Args:
            task (Task): Task to add to the operation
        """
        self.graph.add_node(task)

    def get_task(self, task_id) -> Task:
        """ Get a task from the operation by ID

        Args:
            task_id (str): ID of the task to get
        """
        node: Task = self.graph.get_node(task_id)

        if not isinstance(node, Task):
            raise ValueError(f"Node with ID {task_id} is not a Task")

        return node
    
    def tasks(self) -> list[Task]:
        """ Get all tasks in the operation (i.e. all nodes except START and END)

        Returns:
            list[Task]: List of Task objects in the operation
        """
        return [
            node for node in self.graph.node_values()
            if node.id not in (self.start.id, self.end.id)
        ]

    def successors(self, task_id: str)-> list[Task]:
        """ Get the successor nodes of a given node in the operation

        Args:
            task_id (str): ID of the task to get successors for

        Returns:
            list[Task]: List of successor tasks for the given task ID
        """

        return [
            self.graph.get_node(sid)
            for sid in self.graph.successors_ids(task_id)
        ]

    def successor_names(self, task_id: str) -> list[str]:
        """ Get the names of the successor nodes of a given node in the operation

        Args:
            task_id (str): ID of the task to get successor names for

        Returns:
            list[str]: List of names of successor tasks for the given task ID
        """
        return [succ.name for succ in self.successors(task_id)]
    
    def predecessors(self, task_id: str):
        """ Get the

        Args:
            task_id (str): ID of the task to get predecessors for

        Returns:
            _type_: List of predecessor tasks for the given task ID
        """

        return [
            self.graph.get_node(pid)
            for pid in self.graph.predecessors_ids(task_id)
        ]
    
    def predecessor_names(self, task_id: str) -> list[str]:
        """ Get the names of the predecessor nodes of a given node in the operation

        Args:
            task_id (str): ID of the task to get predecessor names for

        Returns:
            list[str]: List of names of predecessor tasks for the given task ID
        """
        return [pred.name for pred in self.predecessors(task_id)]

    def apply_times(self, task_id: str, times: dict) -> None:
        """ Apply the scheduling times to a node in the graph by setting attributes on the node for earliest start, 
            earliest finish, latest start, latest finish, and slack

        Args:
            task_id (str): ID of the node to apply times to
            times (dict): Dictionary containing the times to apply, with keys "ES", "EF", "LS", "LF", and "slack"
        """
        task: Task = self.get_task(task_id)

        if not hasattr(task, "duration"):
            return

        task.earliest_start  = times.get("ES", 0)
        task.earliest_finish = times.get("EF", 0)
        task.latest_start    = times.get("LS", 0)
        task.latest_finish   = times.get("LF", 0)
        task.slack           = times.get("slack", 0)

    def get_times(self, node_id: str) -> dict:
        """ Get the scheduling times for a node in the graph by retrieving attributes from the node for earliest start, earliest finish, latest start, latest finish, and slack

        Args:
            node_id (str): ID of the node to get times for

        Returns:
            dict: Dictionary containing the times for the node, with keys "ES", "EF", "LS", "LF", and "slack"
        """
        node = self.graph.get_node(node_id)

        return {
            "ES": getattr(node, "earliest_start", 0),
            "EF": getattr(node, "earliest_finish", 0),
            "LS": getattr(node, "latest_start", 0),
            "LF": getattr(node, "latest_finish", 0),
            "slack": getattr(node, "slack", 0),
        }
