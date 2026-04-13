# systems/schedule_result.py
from dataclasses import dataclass, field

@dataclass
class ScheduleResult:
    ES: dict = field(default_factory=dict)
    EF: dict = field(default_factory=dict)
    LS: dict = field(default_factory=dict)
    LF: dict = field(default_factory=dict)
    slack: dict = field(default_factory=dict)

    def get(self, node_id):
        return {
            "ES": self.ES.get(node_id),
            "EF": self.EF.get(node_id),
            "LS": self.LS.get(node_id),
            "LF": self.LF.get(node_id),
            "slack": self.slack.get(node_id)

        }