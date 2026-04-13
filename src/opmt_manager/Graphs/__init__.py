"""
Graph Core Module: Provides Node and Graph structures for building directed graphs.
"""

__version__ = "0.1.0"
__author__ = "Zachariah"

from .graph import Graph
from .node import Node

__all__ = [
    "Graph",
    "Node",
]