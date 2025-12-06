"""
Memory map definitions for IP cores.

Integrates with existing register.py for backward compatibility.
"""

from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator, computed_field
from enum import Enum


class AccessType(str, Enum):
    """Register/field access types."""

    READ_ONLY = "read-only"
    WRITE_ONLY = "write-only"
    READ_WRITE = "read-write"
    WRITE_1_TO_CLEAR = "write-1-to-clear"
    READ_WRITE_1_TO_CLEAR = "read-write-1-to-clear"

    # Aliases for backward compatibility
    RO = "read-only"
    WO = "write-only"
    RW = "read-write"
    RW1C = "write-1-to-clear"

    @classmethod
    def normalize(cls, value: str) -> "AccessType":
        """Normalize various access type representations."""
        normalized_map = {
            "ro": cls.READ_ONLY,
            "read-only": cls.READ_ONLY,
            "readonly": cls.READ_ONLY,
            "wo": cls.WRITE_ONLY,
            "write-only": cls.WRITE_ONLY,
            "writeonly": cls.WRITE_ONLY,
            "rw": cls.READ_WRITE,
            "read-write": cls.READ_WRITE,
            "readwrite": cls.READ_WRITE,
            "rw1c": cls.WRITE_1_TO_CLEAR,
            "write-1-to-clear": cls.WRITE_1_TO_CLEAR,
            "write1toclear": cls.WRITE_1_TO_CLEAR,
        }
        return normalized_map.get(value.lower(), cls.READ_WRITE)


class BitField(BaseModel):
    """
    Bit field within a register.

    Represents a named range of bits with specific access semantics.
    """

    name: str = Field(..., description="Bit field name")
    bit_offset: int = Field(..., description="Starting bit position (LSB = 0)", ge=0)
    bit_width: int = Field(..., description="Number of bits", ge=1)
    access: AccessType = Field(default=AccessType.READ_WRITE, description="Access type")
    reset_value: Optional[int] = Field(default=None, description="Reset/default value")
    description: str = Field(default="", description="Field description")
    enumerated_values: Optional[Dict[int, str]] = Field(
        default=None, description="Enumeration mapping {value: name}"
    )

    @field_validator("bit_offset")
    @classmethod
    def validate_offset(cls, v: int) -> int:
        """Ensure offset is within 32-bit boundary."""
        if v >= 32:
            raise ValueError("Bit offset cannot exceed 31 (32-bit register boundary)")
        return v

    @field_validator("bit_width")
    @classmethod
    def validate_width(cls, v: int) -> int:
        """Ensure width is positive and reasonable."""
        if v <= 0:
            raise ValueError("Bit width must be positive")
        if v > 32:
            raise ValueError("Bit width cannot exceed 32 bits")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate bit field after initialization."""
        if self.bit_offset + self.bit_width > 32:
            raise ValueError(
                f"Bit field '{self.name}' extends beyond 32-bit boundary "
                f"(offset={self.bit_offset}, width={self.bit_width})"
            )

        # Validate reset value if provided
        if self.reset_value is not None:
            if self.reset_value < 0 or self.reset_value > self.max_value:
                raise ValueError(
                    f"Reset value {self.reset_value} out of range [0, {self.max_value}] "
                    f"for field '{self.name}'"
                )

    @computed_field
    @property
    def bit_range(self) -> str:
        """Get bit range string (e.g., '[7:0]' or '[5]')."""
        if self.bit_width == 1:
            return f"[{self.bit_offset}]"
        return f"[{self.bit_offset + self.bit_width - 1}:{self.bit_offset}]"

    @computed_field
    @property
    def mask(self) -> int:
        """Get bit mask for this field."""
        return ((1 << self.bit_width) - 1) << self.bit_offset

    @computed_field
    @property
    def max_value(self) -> int:
        """Get maximum value that can be stored."""
        return (1 << self.bit_width) - 1

    @property
    def is_read_only(self) -> bool:
        """Check if field is read-only."""
        return self.access == AccessType.READ_ONLY

    @property
    def is_write_only(self) -> bool:
        """Check if field is write-only."""
        return self.access == AccessType.WRITE_ONLY

    @property
    def is_read_write(self) -> bool:
        """Check if field is read-write."""
        return self.access == AccessType.READ_WRITE

    @property
    def is_write_1_to_clear(self) -> bool:
        """Check if field is write-1-to-clear."""
        return self.access in [AccessType.WRITE_1_TO_CLEAR, AccessType.READ_WRITE_1_TO_CLEAR]

    def extract_value(self, register_value: int) -> int:
        """Extract this field's value from a register value."""
        return (register_value >> self.bit_offset) & self.max_value

    def insert_value(self, register_value: int, field_value: int) -> int:
        """Insert this field's value into a register value."""
        if field_value > self.max_value:
            raise ValueError(
                f"Value {field_value} exceeds field '{self.name}' maximum {self.max_value}"
            )
        # Clear field bits, then insert new value
        cleared = register_value & ~self.mask
        return cleared | ((field_value << self.bit_offset) & self.mask)

    model_config = {"extra": "forbid", "validate_assignment": True}


class Register(BaseModel):
    """
    Register definition within a memory map.

    Represents a memory-mapped register with bit fields.
    """

    name: str = Field(..., description="Register name")
    address_offset: int = Field(..., description="Offset from address block base", ge=0)
    size: int = Field(default=32, description="Register width in bits")
    access: AccessType = Field(default=AccessType.READ_WRITE, description="Default access type")
    reset_value: Optional[int] = Field(default=0, description="Reset value for entire register")
    description: str = Field(default="", description="Register description")
    fields: List[BitField] = Field(default_factory=list, description="Bit fields")

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: int) -> int:
        """Validate register size."""
        valid_sizes = [8, 16, 32, 64]
        if v not in valid_sizes:
            raise ValueError(f"Register size must be one of {valid_sizes}, got {v}")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate register after initialization."""
        # Check for overlapping fields
        for i, field1 in enumerate(self.fields):
            for field2 in self.fields[i + 1 :]:
                if self._fields_overlap(field1, field2):
                    raise ValueError(
                        f"Overlapping bit fields in register '{self.name}': "
                        f"'{field1.name}' {field1.bit_range} and "
                        f"'{field2.name}' {field2.bit_range}"
                    )

    @staticmethod
    def _fields_overlap(field1: BitField, field2: BitField) -> bool:
        """Check if two fields overlap."""
        end1 = field1.bit_offset + field1.bit_width
        end2 = field2.bit_offset + field2.bit_width
        return not (end1 <= field2.bit_offset or end2 <= field1.bit_offset)

    @computed_field
    @property
    def byte_offset(self) -> int:
        """Get byte-aligned offset."""
        return self.address_offset

    @computed_field
    @property
    def hex_address(self) -> str:
        """Get hex-formatted address."""
        return f"0x{self.address_offset:08X}"

    @property
    def is_read_only(self) -> bool:
        """Check if register is read-only."""
        return self.access == AccessType.READ_ONLY

    @property
    def is_write_only(self) -> bool:
        """Check if register is write-only."""
        return self.access == AccessType.WRITE_ONLY

    def get_field(self, field_name: str) -> Optional[BitField]:
        """Get field by name."""
        for field in self.fields:
            if field.name == field_name:
                return field
        return None

    model_config = {"extra": "forbid", "validate_assignment": True}


class RegisterArray(BaseModel):
    """
    Array of registers with automatic address calculation.

    Used for repeated register structures (e.g., per-channel registers).
    """

    name: str = Field(..., description="Base name for array")
    base_address: int = Field(..., description="Starting address", ge=0)
    count: int = Field(..., description="Number of instances", ge=1)
    stride: int = Field(..., description="Address increment between instances", ge=4)
    template: Register = Field(..., description="Register template for each instance")
    description: str = Field(default="", description="Array description")

    @field_validator("stride")
    @classmethod
    def validate_stride(cls, v: int) -> int:
        """Ensure stride is aligned."""
        if v < 4 or v % 4 != 0:
            raise ValueError("Stride must be at least 4 and word-aligned")
        return v

    def get_register_address(self, index: int) -> int:
        """Get address for specific array instance."""
        if index < 0 or index >= self.count:
            raise IndexError(f"Register array index {index} out of range [0, {self.count})")
        return self.base_address + (index * self.stride)

    def get_register_name(self, index: int) -> str:
        """Get name for specific array instance."""
        return f"{self.name}{index}"

    @computed_field
    @property
    def total_size(self) -> int:
        """Get total size occupied by array."""
        return self.count * self.stride

    model_config = {"extra": "forbid", "validate_assignment": True}


class BlockUsage(str, Enum):
    """Address block usage type."""

    REGISTERS = "register"
    MEMORY = "memory"
    RESERVED = "reserved"


class AddressBlock(BaseModel):
    """
    Contiguous address block within a memory map.

    Can contain registers, memory, or reserved space.
    """

    name: str = Field(..., description="Block name")
    base_address: int = Field(..., description="Block starting address", ge=0)
    range: Union[int, str] = Field(..., description="Block size (bytes or '4K', '1M', etc.)")
    usage: BlockUsage = Field(default=BlockUsage.REGISTERS, description="Block usage type")
    access: AccessType = Field(default=AccessType.READ_WRITE, description="Default access")
    description: str = Field(default="", description="Block description")

    # Content
    registers: List[Register] = Field(default_factory=list, description="Registers in block")
    register_arrays: List[RegisterArray] = Field(
        default_factory=list, description="Register arrays"
    )

    @field_validator("range", mode="before")
    @classmethod
    def parse_range(cls, v: Union[int, str]) -> int:
        """Parse range string (e.g., '4K', '1M') to bytes."""
        if isinstance(v, int):
            return v

        if isinstance(v, str):
            v = v.strip().upper()
            multipliers = {
                "K": 1024,
                "M": 1024 * 1024,
                "G": 1024 * 1024 * 1024,
            }

            for suffix, mult in multipliers.items():
                if v.endswith(suffix):
                    try:
                        value = int(v[:-1])
                        return value * mult
                    except ValueError:
                        raise ValueError(f"Invalid range format: {v}")

            # Try parsing as plain integer
            try:
                return int(v)
            except ValueError:
                raise ValueError(f"Invalid range format: {v}")

        raise ValueError(f"Range must be int or string, got {type(v)}")

    @computed_field
    @property
    def end_address(self) -> int:
        """Get ending address (exclusive)."""
        return self.base_address + self.range

    @computed_field
    @property
    def hex_range(self) -> str:
        """Get hex-formatted address range."""
        return f"0x{self.base_address:08X} - 0x{self.end_address - 1:08X}"

    def contains_address(self, address: int) -> bool:
        """Check if address is within this block."""
        return self.base_address <= address < self.end_address

    model_config = {"extra": "forbid", "validate_assignment": True}


class MemoryMapReference(BaseModel):
    """Reference to a memory map by name."""

    name: str = Field(..., description="Memory map name")

    model_config = {"extra": "forbid"}


class MemoryMap(BaseModel):
    """
    Complete memory map for an IP core.

    Organizes registers into address blocks with validation.
    """

    name: str = Field(..., description="Memory map name")
    description: str = Field(default="", description="Memory map description")
    address_blocks: List[AddressBlock] = Field(
        default_factory=list, description="Address blocks"
    )

    def model_post_init(self, __context: Any) -> None:
        """Validate memory map after initialization."""
        # Check for overlapping address blocks
        for i, block1 in enumerate(self.address_blocks):
            for block2 in self.address_blocks[i + 1 :]:
                if self._blocks_overlap(block1, block2):
                    raise ValueError(
                        f"Overlapping address blocks: '{block1.name}' {block1.hex_range} "
                        f"and '{block2.name}' {block2.hex_range}"
                    )

    @staticmethod
    def _blocks_overlap(block1: AddressBlock, block2: AddressBlock) -> bool:
        """Check if two address blocks overlap."""
        return not (block1.end_address <= block2.base_address or block2.end_address <= block1.base_address)

    def get_block_at_address(self, address: int) -> Optional[AddressBlock]:
        """Find address block containing given address."""
        for block in self.address_blocks:
            if block.contains_address(address):
                return block
        return None

    def get_register_by_name(self, name: str) -> Optional[Register]:
        """Find register by name across all blocks."""
        for block in self.address_blocks:
            for reg in block.registers:
                if reg.name == name:
                    return reg
        return None

    @computed_field
    @property
    def total_registers(self) -> int:
        """Count total registers across all blocks."""
        return sum(len(block.registers) for block in self.address_blocks)

    @computed_field
    @property
    def total_address_space(self) -> int:
        """Get total address space covered by all blocks."""
        if not self.address_blocks:
            return 0
        max_end = max(block.end_address for block in self.address_blocks)
        min_start = min(block.base_address for block in self.address_blocks)
        return max_end - min_start

    model_config = {"extra": "forbid", "validate_assignment": True}
