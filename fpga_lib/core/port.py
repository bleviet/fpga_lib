from dataclasses import dataclass
from typing import Union, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .data_types import DataType

class PortDirection(str, Enum):
    """
    Enum for port directions.
    """
    IN = "in"
    OUT = "out"

@dataclass
class Port:
    """
    Represents a port with its attributes and behaviors.
    """
    name: str
    direction: PortDirection
    type: Union[str, "DataType"]  # Forward reference to DataType
    width: int = 1

    def invert_direction(self) -> None:
        """
        Inverts the direction of the port.
        """
        if self.direction == PortDirection.IN:
            self.direction = PortDirection.OUT
        elif self.direction == PortDirection.OUT:
            self.direction = PortDirection.IN