# systems/scheduler.py

from collections import deque
from typing import List

from opmt_manager.Graphs.graph import Graph
from opmt_manager.domain.operation import Operation
from opmt_manager.domain.task import Task
from opmt_manager.systems.schedule_result import ScheduleResult

class Scheduler:

    def __init__(self, operation: Operation):
        """ Initialize scheduler with an operation

        Note:
            operation must have a valid graph with start and end nodes

        Args:
            operation (Operation): Operation to schedule
        """
        self.operation: Operation = operation
        self.graph: Graph = operation.graph

        self.start_id: str = operation.start.id
        self.end_id: str = operation.end.id

        # validate that start and end nodes are in the graph
        self.graph._validate(self.start_id)
        self.graph._validate(self.end_id)
        
        self.compute()

    def compute(self) -> ScheduleResult:
        """ Compute the schedule for the operation using critical path method

        Returns:
            ScheduleResult: ScheduleResult object containing the computed schedule information
        """
        graph: Graph = self.graph
        result: ScheduleResult = ScheduleResult()

        task_ids: List[str] = graph.node_ids()

        # forward + backward
        self._forward_pass(task_ids, result)
        self._backward_pass(task_ids, result)

        # slack
        for nid in task_ids:
            slack = result.LS.get(nid, 0) - result.ES.get(nid, 0)
            result.slack[nid] = slack
            result.SC[nid] = slack * result.SC.get(nid, 0)

        # apply to operation (domain owns state)
        for nid in task_ids:
            node: Task = self.graph.get_node(nid)

            if not isinstance(node, Task):
                continue

            self.operation.apply_times(nid, result.get(nid))

        return result
    
    def _forward_pass(self, task_ids: List[str], result: ScheduleResult) -> None:
        """ Perform forward pass to compute earliest start and finish times

        Args:
            task_ids (List[str]): List of task IDs in the graph
            result (ScheduleResult): ScheduleResult object to store results in
        """
        graph: Graph = self.graph

        indegree = {
            nid: len(graph.predecessors_ids(nid))
            for nid in task_ids
        }

        queue: deque[str] = deque([self.start_id])

        result.ES[self.start_id] = 0
        result.EF[self.start_id] = 0

        while queue:
            current: str = queue.popleft()
            node: Task = graph.get_node(current)

            duration: float = getattr(node, "duration", 0)
            result.EF[current] = result.ES[current] + duration

            # running cost and slack cost
            result.RC[current] = getattr(node, "running_cost", 0) * duration

            # store slack cost in result.SC for each node
            result.SC[current] = getattr(node, "slack_cost", 0)

            for nxt in graph.successors_ids(current):
                result.ES[nxt] = max(
                    result.ES.get(nxt, 0),
                    result.EF[current]
                )

                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

    def _backward_pass(self, task_ids: List[str], result: ScheduleResult) -> None:
        """ Perform backward pass to compute latest start and finish times
        

        Args:
            task_ids (List[str]): List of task IDs in the graph
            result (ScheduleResult): ScheduleResult object to store results in
        """
        graph: Graph = self.graph

        outdegree = {
            nid: len(graph.successors_ids(nid))
            for nid in task_ids
        }

        max_time: float = result.EF[self.end_id]

        queue: deque[str] = deque([self.end_id])

        result.LF[self.end_id] = max_time
        result.LS[self.end_id] = max_time

        while queue:
            current: str = queue.popleft()
            node: Task = graph.get_node(current)

            duration: float = getattr(node, "duration", 0)
            result.LS[current] = result.LF[current] - duration

            for prev in graph.predecessors_ids(current):
                result.LF[prev] = min(
                    result.LF.get(prev, float("inf")),
                    result.LS[current]
                )

                outdegree[prev] -= 1
                if outdegree[prev] == 0:
                    queue.append(prev)

    def is_critical(self, task_id: str) -> bool:
        """ Check if a task is on the critical path (i.e. has zero slack)

        Args:
            task_id (str): ID of the task to check

        Returns:
            bool: True if the task is on the critical path (has zero slack), False otherwise
        """
        return getattr(self.graph.get_node(task_id), "slack", 1) == 0

    def get_critical_path(self) -> List[str]:
        """ Get the critical path of the process, which is the list of task IDs where ES == LS

        Returns:
            List[str]: List of task IDs in the critical path
        """
        return [
            node.id for node in self.graph.node_values()
            if getattr(node, "slack", 1) == 0
        ]
    
    def get_critical_path_ordered(self) -> List[str]:
        """ Get the critical path of the process in order, which is the list of task IDs where ES == LS and each task's earliest finish matches the next task's earliest start

        Returns:
            List[str]: List of task IDs in the critical path in order
        """
        path: List[str] = []
        current: str = self.start_id

        while True:
            path.append(current)

            current_node: Task = self.graph.get_node(current)

            next_nodes: List[str] = [
                nid for nid in self.graph.successors_ids(current)
                if getattr(self.graph.get_node(nid), "slack", 1) == 0
                and getattr(self.graph.get_node(nid), "earliest_start", 0)
                   == getattr(current_node, "earliest_finish", 0)
            ]

            if not next_nodes:
                break

            current = next_nodes[0]

        return path

    
    def get_cycle_time(self) -> float:
        """ Returns the cycle time of the process, which is the maximum earliest finish time of any task

        Returns:
            float: Cycle time of the process
        """
        return max(
            getattr(node, "earliest_finish", 0)
            for node in self.graph.node_values()
        )
    
    def get_process_efficiency(self) -> float:
        """ Returns the process efficiency, which is the total work divided by the cycle time

        Raises:
            ValueError: If cycle time is zero

        Returns:
            float: Process efficiency of the process
        """
        cycle_time: float = self.get_cycle_time()

        if cycle_time == 0:
            raise ValueError("Cycle time is zero")

        total_work: float = sum(
            getattr(node, "duration", 0)
            for node in self.graph.node_values()
            if node.id not in (self.start_id, self.end_id)
        )

        return cycle_time / total_work
    
    def __repr__(self):
        """Return a readable summary of the schedule and task timing table."""

        cycle_time = self.get_cycle_time()
        efficiency = self.get_process_efficiency()

        lines = [
            "",
            "=" * 110,
            f"Scheduler: {self.operation.name}",
            "-" * 110,
            f"Cycle Time : {cycle_time}",
            f"Efficiency : {efficiency:.2%}",
            "-" * 110,
            (
                f"{'Task':<38} "
                f"{'Dur':>5} "
                f"{'ES':>5} "
                f"{'EF':>5} "
                f"{'LS':>5} "
                f"{'LF':>5} "
                f"{'Slack':>7} "
                f"{'Run Cost':>10} "
                f"{'Slack Cost':>11}"
            ),
            "-" * 110,
        ]

        # Sort tasks in schedule order
        nodes = sorted(
            self.graph.node_values(),
            key=lambda node: (
                getattr(node, "earliest_start", 0),
                getattr(node, "earliest_finish", 0),
                node.name
            )
        )

        for node in nodes:
            lines.append(
                f"{node.name:<38} "
                f"{getattr(node, 'duration', 0):>5} "
                f"{getattr(node, 'earliest_start', 0):>5} "
                f"{getattr(node, 'earliest_finish', 0):>5} "
                f"{getattr(node, 'latest_start', 0):>5} "
                f"{getattr(node, 'latest_finish', 0):>5} "
                f"{getattr(node, 'slack', 0):>7} "
                f"{getattr(node, 'running_cost', 0):>10} "
                f"{getattr(node, 'slack_cost', 0):>11}"
            )

        lines.append("=" * 110)

        return "\n".join(lines)