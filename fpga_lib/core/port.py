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
    INOUT = "inout"
    BUFFER = "buffer"
    LINKAGE = "linkage"

# Alias for compatibility with parser code
Direction = PortDirection

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
            
    def to_vhdl(self) -> str:
        """
        Get VHDL representation of this port.
        
        Returns:
            String with VHDL port declaration
        """
        type_str = str(self.type) if hasattr(self.type, "__str__") else str(self.type)
        return f"{self.name} : {self.direction.value} {type_str}"
    
    def to_verilog(self) -> str:
        """
        Get Verilog representation of this port.
        
        Returns:
            String with Verilog port declaration
        """
        # Map VHDL directions to Verilog
        direction_map = {
            PortDirection.IN: "input",
            PortDirection.OUT: "output",
            PortDirection.INOUT: "inout",
            PortDirection.BUFFER: "output", # No direct buffer in Verilog
            PortDirection.LINKAGE: "inout"  # No direct linkage in Verilog
        }
        
        verilog_dir = direction_map.get(self.direction, "input")
        
        # Get type representation
        if hasattr(self.type, "to_verilog"):
            type_str = self.type.to_verilog()
            return f"{verilog_dir} {type_str} {self.name}"
        else:
            # If no specific Verilog representation, use wire/reg
            if self.width > 1:
                return f"{verilog_dir} [{self.width-1}:0] {self.name}"
            else:
                return f"{verilog_dir} {self.name}"