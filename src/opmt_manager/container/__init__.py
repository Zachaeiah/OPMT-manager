"""
Dependency Injection Container Module

Provides a lightweight container for dependency management.
"""

from .container import Container
from .exceptions import DependencyNotFoundError

__all__ = [
    "Container",
    "DependencyNotFoundError",
]

__version__ = "0.1.0"
__author__ = "Zachariah"