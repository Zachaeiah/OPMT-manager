# domain/task.py
from typing import Any, Dict

from opmt_manager.Graphs.node import Node
from copy import deepcopy

class Task(Node):
    def __init__(
        self,
        name: str,
        duration: float,
        running_cost: float = 0.0,
        slack_cost: float = 0.0,
        **kwargs: Any
    ):
        """Initialize a Task with a name, duration, and optional costs.

        Args:
            name: Name of the task.
            duration: Duration of the task.
            running_cost: Cost while the task is running.
            slack_cost: Cost associated with unused slack time.
            **kwargs: Extra arguments passed to the base Node class.
        """
        super().__init__(name=name, **kwargs)

        self.duration: float = duration

        self.earliest_start: float = 0.0
        self.earliest_finish: float = 0.0
        self.latest_start: float = 0.0
        self.latest_finish: float = 0.0
        self.slack: float = 0.0

        self.running_cost: float = running_cost
        self.slack_cost: float = slack_cost

    def clone(self, keep_id: bool = False) -> "Task":
        """Create a copy of this task.

        Args:
            keep_id (bool): If True, preserves the same ID (dangerous in graphs).
                            Default False = new unique node.

        Returns:
            Task: cloned task
        """
        new_task = Task(self.name, self.duration, running_cost=self.running_cost, slack_cost=self.slack_cost)

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
    
    def to_dict(self) -> Dict[str, Any]:
        """ Convert the Task to a dictionary representation.

        Returns:
            dict: Dictionary containing task attributes
        """
        return {
            "id": self.id,
            "name": self.name,
            "duration": self.duration,
            "earliest_start": self.earliest_start,
            "earliest_finish": self.earliest_finish,
            "latest_start": self.latest_start,
            "latest_finish": self.latest_finish,
            "slack": self.slack,
            "running_cost": self.running_cost,
            "slack_cost": self.slack_cost
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Task":
        """ Create a Task instance from a dictionary representation.

        Args:
            data (dict): Dictionary containing task attributes

        Returns:
            Task: A Task instance created from the provided dictionary
        """

        task = Task(
            name=data["name"],
            duration=data["duration"],
            running_cost=data.get("running_cost", 0.0),
            slack_cost=data.get("slack_cost", 0.0)
        )
        task.id = data["id"]
        task.earliest_start = data.get("earliest_start", 0.0)
        task.earliest_finish = data.get("earliest_finish", 0.0)
        task.latest_start = data.get("latest_start", 0.0)
        task.latest_finish = data.get("latest_finish", 0.0)
        task.slack = data.get("slack", 0.0)

        return task

    def __repr__(self) -> str:
        """ Returns a string representation of the Task, including scheduling info if available.

        Returns:
            str : String representation of the Task
        """
        if self.earliest_finish > 0:
            return (f"Task(name={self.name}, duration={self.duration}, "
                    f"ES={self.earliest_start}, EF={self.earliest_finish}, "
                    f"LS={self.latest_start}, LF={self.latest_finish}, "
                    f"Slack={self.slack})", 
                    f"Cost = ${self.running_cost*self.duration}, loss = ${self.slack_cost*self.slack}")
                    
        if self.duration > 0:
            return f"Task(name={self.name}, duration={self.duration})"
        else:
            return f"Task(name={self.name})"
        
        return ""