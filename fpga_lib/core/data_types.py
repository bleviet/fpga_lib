# fpga_lib/core/data_types.py
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, List, Dict, Union

class VHDLBaseType(Enum):
    """
    Enumeration of VHDL base types.
    """
    STD_LOGIC = "std_logic"
    STD_LOGIC_VECTOR = "std_logic_vector"
    UNSIGNED = "unsigned"
    SIGNED = "signed"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    BIT = "bit"
    BIT_VECTOR = "bit_vector"
    NATURAL = "natural"
    POSITIVE = "positive"
    
    @classmethod
    def from_string(cls, type_str: str) -> 'VHDLBaseType':
        """
        Convert a string to a VHDLBaseType enum.
        Handles case-insensitive conversion.
        
        Args:
            type_str: String representation of the type
            
        Returns:
            VHDLBaseType enum corresponding to the string
        """
        try:
            return cls(type_str.lower())
        except ValueError:
            # Default to std_logic if unknown
            return cls.STD_LOGIC

@dataclass
class DataType:
    """
    Base class for data types.
    
    Attributes:
        base_type: Base type (e.g., std_logic, std_logic_vector)
        range_constraint: Optional range constraint (e.g., "7 downto 0")
        array_dimensions: Optional array dimensions
    """
    base_type: Union[VHDLBaseType, str]
    range_constraint: Optional[str] = None
    array_dimensions: Optional[List[str]] = None
    
    def __str__(self) -> str:
        """
        Generate string representation of the data type.
        
        Returns:
            String representation of the data type
        """
        if isinstance(self.base_type, VHDLBaseType):
            result = self.base_type.value
        else:
            result = str(self.base_type)
            
        if self.range_constraint:
            result += f"({self.range_constraint})"
            
        if self.array_dimensions:
            dims = " ".join(self.array_dimensions)
            result = f"array ({dims}) of {result}"
            
        return result
    
    def to_vhdl(self) -> str:
        """
        Convert to VHDL type representation.
        
        Returns:
            VHDL type representation
        """
        return str(self)
    
    def to_verilog(self) -> str:
        """
        Convert to Verilog type representation.
        
        Returns:
            Verilog type representation
        """
        if isinstance(self.base_type, VHDLBaseType):
            if self.base_type == VHDLBaseType.STD_LOGIC:
                return "wire"
            elif self.base_type == VHDLBaseType.STD_LOGIC_VECTOR and self.range_constraint:
                # Parse range like "7 downto 0" -> "[7:0]"
                try:
                    parts = self.range_constraint.split()
                    msb = parts[0]
                    lsb = parts[-1]
                    return f"wire [{msb}:{lsb}]"
                except:
                    return f"wire [0:0]"
        
        # Default case
        return "wire"

@dataclass
class BitType(DataType):
    """
    Represents a bit data type (std_logic in VHDL).
    """
    def __init__(self):
        super().__init__(VHDLBaseType.STD_LOGIC)

@dataclass
class VectorType(DataType):
    """
    Represents a vector data type.
    """
    def __init__(self, width: int = 1):
        range_str = f"{width-1} downto 0" if width > 1 else None
        super().__init__(VHDLBaseType.STD_LOGIC_VECTOR, range_str)
        self.width = width

@dataclass
class IntegerType(DataType):
    """
    Represents an integer data type.
    """
    def __init__(self):
        super().__init__(VHDLBaseType.INTEGER)