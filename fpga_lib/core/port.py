from dataclasses import dataclass
from typing import Union
from enum import Enum

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
    type: Union[str, "DataType"]  # Assuming DataType is defined elsewhere
    width: int = 1

    def invert_direction(self):
        """
        Inverts the direction of the port.
        """
        if self.direction == PortDirection.IN:
            self.direction = PortDirection.OUT
        elif self.direction == PortDirection.OUT:
            self.direction = PortDirection.IN