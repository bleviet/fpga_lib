"""
Base models for IP core metadata.
"""

from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


class VLNV(BaseModel):
    """
    Vendor-Library-Name-Version identifier for IP cores.

    This uniquely identifies an IP core in the IP-XACT standard format.
    """

    vendor: str = Field(..., description="Vendor identifier (e.g., 'my-company.com')")
    library: str = Field(..., description="Library name (e.g., 'processing')")
    name: str = Field(..., description="IP core name (e.g., 'my_timer_core')")
    version: str = Field(..., description="Version string (e.g., '1.2.0')")

    @field_validator("vendor", "library", "name")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure identifiers are not empty."""
        if not v or not v.strip():
            raise ValueError("VLNV fields cannot be empty")
        return v.strip()

    @property
    def full_name(self) -> str:
        """Return fully qualified VLNV string."""
        return f"{self.vendor}:{self.library}:{self.name}:{self.version}"

    def __str__(self) -> str:
        return self.full_name

    def __hash__(self) -> int:
        return hash(self.full_name)


class Parameter(BaseModel):
    """
    Generic parameter/generic definition for IP cores.

    Used for VHDL generics, Verilog parameters, or component configuration.
    """

    name: str = Field(..., description="Parameter name")
    value: Any = Field(..., description="Default value")
    data_type: str = Field(default="integer", description="Data type (integer, string, boolean, etc.)")
    description: str = Field(default="", description="Parameter description")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure parameter name is valid."""
        if not v or not v.strip():
            raise ValueError("Parameter name cannot be empty")
        return v.strip()

    @property
    def is_numeric(self) -> bool:
        """Check if parameter is numeric type."""
        return self.data_type.lower() in ["integer", "natural", "positive", "real"]

    @property
    def is_boolean(self) -> bool:
        """Check if parameter is boolean type."""
        return self.data_type.lower() in ["boolean", "bool"]

    @property
    def is_string(self) -> bool:
        """Check if parameter is string type."""
        return self.data_type.lower() in ["string", "str"]

    model_config = {"extra": "forbid", "validate_assignment": True}
