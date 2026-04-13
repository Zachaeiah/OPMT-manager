"""
OPMT Manager

Operations Planning & Management Toolkit

High-level API for building, scheduling, and visualizing task graphs.
"""

# domain
from .domain import (
    Task,
    Operation,
    TaskManager,
    ComposableTask,
    ComposableOperation,
)

# systems
from .systems import (
    Scheduler,
    ScheduleResult,
    GraphVisualizer,
)

__all__ = [
    # domain
    "Task",
    "Operation",
    "TaskManager",
    "ComposableTask",
    "ComposableOperation",

    # systems
    "Scheduler",
    "ScheduleResult",
    "GraphVisualizer",
]

__version__ = "0.1.0"
__author__ = "Zachariah"
