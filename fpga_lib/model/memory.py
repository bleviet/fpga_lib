"""
Memory map definitions for IP cores.

These are Pydantic models for YAML parsing and validation.
For runtime register access, use fpga_lib.core.register classes.

Naming convention:
- Classes here use *Def suffix (e.g., RegisterDef, BitFieldDef) to indicate
  they are definitions/schemas, not runtime objects.
- Use to_runtime_*() methods to convert to runtime objects.
"""

from typing import List, Optional, Union, Dict, Any, ForwardRef, TYPE_CHECKING
from pydantic import BaseModel, Field, field_validator, computed_field
from enum import Enum

if TYPE_CHECKING:
    from fpga_lib.runtime.register import AbstractBusInterface, Register as RuntimeRegister

# Forward reference for recursive register definition
RegisterDef = ForwardRef('RegisterDef')


class AccessType(str, Enum):
    """Register/field access types for YAML parsing."""

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

    def to_runtime_access(self) -> str:
        """Convert to runtime AccessType string value (ro, wo, rw, rw1c)."""
        mapping = {
            self.READ_ONLY: 'ro',
            self.WRITE_ONLY: 'wo',
            self.READ_WRITE: 'rw',
            self.WRITE_1_TO_CLEAR: 'rw1c',
            self.READ_WRITE_1_TO_CLEAR: 'rw1c',
        }
        return mapping.get(self, 'rw')


class BitFieldDef(BaseModel):
    """
    Bit field definition within a register (Pydantic model for YAML parsing).

    Represents a named range of bits with specific access semantics.
    """

    name: str = Field(..., description="Bit field name")
    bit_offset: Optional[int] = Field(default=None, description="Starting bit position (LSB = 0)", ge=0)
    bit_width: Optional[int] = Field(default=None, description="Number of bits", ge=1)
    bits: Optional[str] = Field(default=None, description="Bit range string e.g. [7:0]")
    access: AccessType = Field(default=AccessType.READ_WRITE, description="Access type")
    reset_value: Optional[int] = Field(default=None, description="Reset/default value")
    description: str = Field(default="", description="Field description")
    enumerated_values: Optional[Dict[int, str]] = Field(
        default=None, description="Enumeration mapping {value: name}"
    )

    @field_validator("access", mode="before")
    @classmethod
    def normalize_access(cls, v: Any) -> Any:
        """Normalize access type using AccessType.normalize."""
        if isinstance(v, str):
            return AccessType.normalize(v)
        return v

    def to_runtime_bitfield(self):
        """Convert to a runtime BitField object from core.register."""
        from fpga_lib.runtime.register import BitField as RuntimeBitField
        
        # Resolve bit_offset and bit_width from bits string if needed
        offset = self.bit_offset
        width = self.bit_width
        
        if offset is None and self.bits:
            # Parse bits string like "[7:4]" or "7:4"
            bits_str = self.bits.strip('[]')
            if ':' in bits_str:
                high, low = bits_str.split(':')
                offset = int(low)
                width = int(high) - int(low) + 1
            else:
                offset = int(bits_str)
                width = 1
        
        # Default values if still None
        if offset is None:
            offset = 0
        if width is None:
            width = 1
        
        return RuntimeBitField(
            name=self.name,
            offset=offset,
            width=width,
            access=self.access.to_runtime_access(),
            description=self.description,
            reset_value=self.reset_value
        )
    
    model_config = {"extra": "ignore", "validate_assignment": True}


class RegisterDef(BaseModel):
    """
    Register definition within a memory map (Pydantic model for YAML parsing).

    Represents a memory-mapped register with bit fields.
    """

    name: str = Field(..., description="Register name")
    address_offset: Optional[int] = Field(default=None, alias="offset", description="Offset from address block base", ge=0)
    size: int = Field(default=32, description="Register width in bits")
    access: AccessType = Field(default=AccessType.READ_WRITE, description="Default access type")
    reset_value: Optional[int] = Field(default=0, description="Reset value for entire register")
    description: str = Field(default="", description="Register description")
    fields: List[BitFieldDef] = Field(default_factory=list, description="Bit fields")
    
    # Recursion support for register groups/arrays
    registers: List['RegisterDef'] = Field(default_factory=list, description="Child registers (for groups)")
    count: Optional[int] = Field(default=1, description="Array replication count")
    stride: Optional[int] = Field(default=None, description="Array replication stride")

    @field_validator("access", mode="before")
    @classmethod
    def normalize_access(cls, v: Any) -> Any:
        """Normalize access type using AccessType.normalize."""
        if isinstance(v, str):
            return AccessType.normalize(v)
        return v

    def to_runtime_register(self, bus: "AbstractBusInterface", base_offset: int = 0):
        """
        Convert to a runtime Register object from core.register.
        
        Args:
            bus: Bus interface for hardware communication
            base_offset: Base address offset to add to register offset
            
        Returns:
            Runtime Register object
        """
        from fpga_lib.runtime.register import Register as RuntimeRegister
        
        offset = (self.address_offset or 0) + base_offset
        runtime_fields = [f.to_runtime_bitfield() for f in self.fields]
        
        return RuntimeRegister(
            name=self.name,
            offset=offset,
            bus=bus,
            fields=runtime_fields,
            description=self.description
        )

    model_config = {"extra": "ignore", "validate_assignment": True, "populate_by_name": True}


class RegisterArrayDef(BaseModel):
    """
    Array of registers definition with automatic address calculation (Pydantic model).

    Used for repeated register structures (e.g., per-channel registers).
    """

    name: str = Field(..., description="Base name for array")
    base_address: int = Field(..., description="Starting address", ge=0)
    count: int = Field(..., description="Number of instances", ge=1)
    stride: int = Field(..., description="Address increment between instances", ge=4)
    template: RegisterDef = Field(..., description="Register template for each instance")
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

    def to_runtime_array(self, bus: "AbstractBusInterface"):
        """Convert to a runtime RegisterArrayAccessor from core.register."""
        from fpga_lib.runtime.register import RegisterArrayAccessor
        
        runtime_fields = [f.to_runtime_bitfield() for f in self.template.fields]
        
        return RegisterArrayAccessor(
            name=self.name,
            base_offset=self.base_address,
            count=self.count,
            stride=self.stride,
            field_template=runtime_fields,
            bus_interface=bus
        )

    @computed_field
    @property
    def total_size(self) -> int:
        """Get total size occupied by array."""
        return self.count * self.stride

    model_config = {"extra": "ignore", "validate_assignment": True}


class BlockUsage(str, Enum):
    """Address block usage type."""

    REGISTERS = "register"
    MEMORY = "memory"
    RESERVED = "reserved"


class AddressBlock(BaseModel):
    """
    Contiguous address block within a memory map (Pydantic model).
    
    Can contain registers, memory, or reserved space.
    """

    name: str = Field(..., description="Block name")
    base_address: Optional[int] = Field(default=0, alias="offset", description="Block starting address", ge=0)
    range: Optional[Union[int, str]] = Field(default=None, description="Block size (bytes or '4K', '1M', etc.)")
    usage: BlockUsage = Field(default=BlockUsage.REGISTERS, description="Block usage type")
    access: AccessType = Field(default=AccessType.READ_WRITE, description="Default access")
    description: str = Field(default="", description="Block description")
    
    default_reg_width: int = Field(default=32, description="Default register width")

    # Content
    registers: List[RegisterDef] = Field(default_factory=list, description="Registers in block")
    
    model_config = {"extra": "ignore", "validate_assignment": True, "populate_by_name": True}

    @property
    def end_address(self) -> int:
        """Calculate end address of the block."""
        range_val = self.range
        if isinstance(range_val, str):
            # Simple parsing for common suffixes
            suffix = range_val[-1].upper()
            if suffix == 'K': range_val = int(range_val[:-1]) * 1024
            elif suffix == 'M': range_val = int(range_val[:-1]) * 1024 * 1024
            elif suffix == 'G': range_val = int(range_val[:-1]) * 1024 * 1024 * 1024
            else: range_val = int(range_val)
        
        # Default to 0 size if None (though parser provides default)
        size = range_val if range_val is not None else 0
        return self.base_address + size

    def contains_address(self, address: int) -> bool:
        """Check if address is within this block."""
        return self.base_address <= address < self.end_address

    @property
    def hex_range(self) -> str:
        """Get range as hex string."""
        return f"[{hex(self.base_address)} : {hex(self.end_address)}]"
    

# Update forward refs
RegisterDef.model_rebuild()
AddressBlock.model_rebuild()


class MemoryMapReference(BaseModel):
    """Reference to a memory map by name."""

    name: str = Field(..., description="Memory map name")

    model_config = {"extra": "forbid"}


class MemoryMap(BaseModel):
    """
    Complete memory map for an IP core (Pydantic model).

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
        # If range is missing (validation pending or failed), skip check to avoid crash
        if block1.range is None or block2.range is None:
            return False
            
        return not (block1.end_address <= block2.base_address or block2.end_address <= block1.base_address)

    def get_block_at_address(self, address: int) -> Optional[AddressBlock]:
        """Find address block containing given address."""
        for block in self.address_blocks:
            if block.contains_address(address):
                return block
        return None

    def get_register_by_name(self, name: str) -> Optional[RegisterDef]:
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


# Backward compatibility aliases
# These allow existing code to continue using the old names
Register = RegisterDef
BitField = BitFieldDef
RegisterArray = RegisterArrayDef
