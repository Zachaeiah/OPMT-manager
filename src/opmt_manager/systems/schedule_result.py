# systems/schedule_result.py
from dataclasses import dataclass, field

@dataclass
class ScheduleResult:
    """ This class represents the result of a scheduling operation, containing various metrics for each node in the graph.

    Returns:
        _type_: The ScheduleResult instance containing scheduling metrics for each node.
    """
    ES: dict = field(default_factory=dict)
    EF: dict = field(default_factory=dict)
    LS: dict = field(default_factory=dict)
    LF: dict = field(default_factory=dict)
    RC: dict = field(default_factory=dict)
    SC: dict = field(default_factory=dict)
    slack: dict = field(default_factory=dict)
    

    def get(self, node_id: str) -> dict:
        """ Get the scheduling metrics for a specific node by its ID.

        Args:
            node_id (str): The ID of the node for which to retrieve scheduling metrics.

        Returns:
            dict: A dictionary containing the scheduling metrics for the specified node.
        """
        return {
            "ES": self.ES.get(node_id),
            "EF": self.EF.get(node_id),
            "LS": self.LS.get(node_id),
            "LF": self.LF.get(node_id),
            "slack": self.slack.get(node_id),
            "RC": self.RC.get(node_id),
            "SC": self.SC.get(node_id),


        }