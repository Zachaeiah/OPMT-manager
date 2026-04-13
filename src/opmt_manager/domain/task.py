# domain/task.py
from opmt_manager.Graphs.node import Node
from copy import deepcopy

class Task(Node):
    def __init__(self, name: str, duration: float):
        """ Initialize a Task with a name and duration.

        Args:
            name (str): Name of the task
            duration (float): Duration of the task
        """
        super().__init__(name=name)
        self.duration: float = duration

        self.earliest_start: float = 0.0
        self.earliest_finish: float = 0.0
        self.latest_start: float = 0.0
        self.latest_finish: float = 0.0
        self.slack: float = 0.0

    def clone(self, keep_id: bool = False) -> "Task":
        """Create a copy of this task.

        Args:
            keep_id (bool): If True, preserves the same ID (dangerous in graphs).
                            Default False = new unique node.

        Returns:
            Task: cloned task
        """
        new_task = Task(self.name, self.duration)

        # copy scheduling data
        new_task.earliest_start = self.earliest_start
        new_task.earliest_finish = self.earliest_finish
        new_task.latest_start = self.latest_start
        new_task.latest_finish = self.latest_finish
        new_task.slack = self.slack

        # optionally preserve ID (NOT recommended for graph use)
        if keep_id:
            new_task.id = self.id

        return new_task

    def __repr__(self) -> str:
        """ Returns a string representation of the Task, including scheduling info if available.

        Returns:
            str : String representation of the Task
        """
        if self.earliest_finish > 0:
            return (f"Task(name={self.name}, duration={self.duration}, "
                    f"ES={self.earliest_start}, EF={self.earliest_finish}, "
                    f"LS={self.latest_start}, LF={self.latest_finish}, "
                    f"Slack={self.slack})")
        if self.duration > 0:
            return f"Task(name={self.name}, duration={self.duration})"
        else:
            return f"Task(name={self.name})"
        
        return ""