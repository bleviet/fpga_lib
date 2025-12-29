"""
Port definitions for IP cores.
"""

from typing import Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class PortDirection(str, Enum):
    """Port direction enumeration."""

    IN = "in"
    OUT = "out"
    INOUT = "inout"


class Port(BaseModel):
    """
    Generic port definition for IP cores.

    Used for data and control ports that are not part of clock, reset, or bus interfaces.
    """

    name: str = Field(..., description="Physical port name (HDL)")
    logical_name: str = Field(default="", description="Standard logical name for association")
    direction: PortDirection = Field(..., description="Port direction")
    width: int = Field(default=1, description="Port width in bits")
    description: str = Field(default="", description="Port description")

    @field_validator("direction", mode="before")
    @classmethod
    def normalize_direction(cls, v: Any) -> Any:
        """Validate and normalize port direction."""
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower == "input":
                return "in"
            if v_lower == "output":
                return "out"
            return v_lower
        return v

    @field_validator("width")
    @classmethod
    def validate_width(cls, v: int) -> int:
        """Ensure port width is positive."""
        if v <= 0:
            raise ValueError("Port width must be positive")
        return v

    @property
    def is_input(self) -> bool:
        """Check if port is input."""
        return self.direction == PortDirection.IN

    @property
    def is_output(self) -> bool:
        """Check if port is output."""
        return self.direction == PortDirection.OUT

    @property
    def is_bidirectional(self) -> bool:
        """Check if port is bidirectional."""
        return self.direction == PortDirection.INOUT

    @property
    def is_vector(self) -> bool:
        """Check if port is a vector (multi-bit)."""
        return self.width > 1

    @property
    def range_string(self) -> str:
        """Get VHDL-style range string (e.g., '7 downto 0')."""
        if self.width == 1:
            return ""
        return f"{self.width - 1} downto 0"

    model_config = {"extra": "forbid", "validate_assignment": True}
