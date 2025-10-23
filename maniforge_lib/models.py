"""
Data models and types for Maniforge
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ResourceAmount:
    """Represents a resource amount (CPU or memory)"""
    value: float  # Normalized value (CPU in millicores, memory in bytes)
    original: str  # Original string representation
    
    @staticmethod
    def parse_cpu(value: str) -> 'ResourceAmount':
        """Parse CPU value to millicores"""
        if value.endswith('m'):
            millicores = float(value[:-1])
        else:
            millicores = float(value) * 1000
        return ResourceAmount(millicores, value)
    
    @staticmethod
    def parse_memory(value: str) -> 'ResourceAmount':
        """Parse memory value to bytes"""
        units = {
            'Ki': 1024,
            'Mi': 1024**2,
            'Gi': 1024**3,
            'Ti': 1024**4,
            'K': 1000,
            'M': 1000**2,
            'G': 1000**3,
            'T': 1000**4,
        }
        
        for suffix, multiplier in units.items():
            if value.endswith(suffix):
                number = float(value[:-len(suffix)])
                return ResourceAmount(number * multiplier, value)
        
        # Assume bytes if no suffix
        return ResourceAmount(float(value), value)
    
    def format_cpu(self) -> str:
        """Format CPU value as string"""
        if self.value < 1000:
            return f"{int(self.value)}m"
        else:
            return f"{self.value / 1000:.2f}"
    
    def format_memory(self) -> str:
        """Format memory value as string"""
        if self.value >= 1024**3:
            return f"{self.value / (1024**3):.2f}Gi"
        elif self.value >= 1024**2:
            return f"{self.value / (1024**2):.2f}Mi"
        elif self.value >= 1024:
            return f"{self.value / 1024:.2f}Ki"
        else:
            return f"{int(self.value)}"


@dataclass
class ResourceRequirements:
    """Resource requests and limits"""
    cpu_request: ResourceAmount
    cpu_limit: ResourceAmount
    memory_request: ResourceAmount
    memory_limit: ResourceAmount


@dataclass
class NodeCapacity:
    """Node capacity information"""
    cpu: ResourceAmount
    memory: ResourceAmount
    node_type: str
    count: int = 1
    disk: Optional[ResourceAmount] = None


@dataclass
class AppResources:
    """Application resource requirements"""
    app_name: str
    namespace: str
    node_selector: str
    replicas: int
    resources: ResourceRequirements
