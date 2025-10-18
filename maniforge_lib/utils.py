"""
Utility functions for Maniforge
"""

from typing import Dict, Any


def deep_merge(target: Dict, source: Dict):
    """Deep merge source dict into target dict"""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge(target[key], value)
        else:
            target[key] = value
