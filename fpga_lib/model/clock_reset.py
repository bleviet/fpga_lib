"""
Clock and reset definitions for IP cores.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Polarity(str, Enum):
    """Reset polarity enumeration."""

    ACTIVE_HIGH = "activeHigh"
    ACTIVE_LOW = "activeLow"


class Clock(BaseModel):
    """
    Clock definition for an IP core.

    Defines both logical (internal) and physical (port) names for clock signals.
    """

    name: str = Field(..., description="Logical clock name (e.g., 'SYS_CLK')")
    physical_port: str = Field(..., description="Physical port name (e.g., 'i_clk_sys')")
    direction: str = Field(default="in", description="Port direction (typically 'in')")
    frequency: Optional[str] = Field(default=None, description="Clock frequency (e.g., '100MHz')")
    description: str = Field(default="", description="Clock description")

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate clock direction."""
        if v.lower() not in ["in", "input"]:
            raise ValueError("Clock direction must be 'in' or 'input'")
        return v.lower()

    @property
    def frequency_hz(self) -> Optional[float]:
        """Parse frequency string to Hz (e.g., '100MHz' -> 100000000.0)."""
        if not self.frequency:
            return None

        freq_str = self.frequency.strip().upper()
        multipliers = {
            "HZ": 1,
            "KHZ": 1e3,
            "MHZ": 1e6,
            "GHZ": 1e9,
        }

        for suffix, mult in multipliers.items():
            if freq_str.endswith(suffix):
                try:
                    value = float(freq_str[: -len(suffix)])
                    return value * mult
                except ValueError:
                    return None
        return None

    model_config = {"extra": "forbid", "validate_assignment": True}


class Reset(BaseModel):
    """
    Reset definition for an IP core.

    Defines both logical (internal) and physical (port) names for reset signals,
    including polarity information.
    """

    name: str = Field(..., description="Logical reset name (e.g., 'SYS_RST')")
    physical_port: str = Field(..., description="Physical port name (e.g., 'i_rst_n_sys')")
    direction: str = Field(default="in", description="Port direction (typically 'in')")
    polarity: Polarity = Field(
        default=Polarity.ACTIVE_HIGH, description="Reset polarity (activeHigh or activeLow)"
    )
    description: str = Field(default="", description="Reset description")

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate reset direction."""
        if v.lower() not in ["in", "input"]:
            raise ValueError("Reset direction must be 'in' or 'input'")
        return v.lower()

    @property
    def is_active_low(self) -> bool:
        """Check if reset is active low."""
        return self.polarity == Polarity.ACTIVE_LOW

    @property
    def is_active_high(self) -> bool:
        """Check if reset is active high."""
        return self.polarity == Polarity.ACTIVE_HIGH

    model_config = {"extra": "forbid", "validate_assignment": True}
