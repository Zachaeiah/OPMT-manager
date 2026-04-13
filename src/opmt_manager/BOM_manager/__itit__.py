"""
BOM Manager Module

Provides tools for managing Bills of Materials (BOM) and generating part IDs.
"""

from .bom import BOM
from .partIDGenerator import PartIDGenerator

__all__ = [
    "BOM",
    "PartIDGenerator",
]

__version__ = "0.1.0"
__author__ = "Zachariah"