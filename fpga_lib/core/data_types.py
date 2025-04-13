# fpga_lib/core/data_types.py
from dataclasses import dataclass

@dataclass
class DataType:
    """
    Base class for data types.
    """
    name: str

@dataclass
class BitType(DataType):
    """
    Represents a bit data type.
    """
    name: str = "bit"

@dataclass
class VectorType(DataType):
    """
    Represents a vector data type.
    """
    name: str = "vector"
    width: int = 1

@dataclass
class IntegerType(DataType):
    """
    Represents an integer data type.
    """
    name: str = "integer"