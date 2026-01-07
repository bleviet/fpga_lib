"""
Memory Map Core - Model Layer

Pure Python implementation of memory map data structures and business logic.
Integrates with ipcore_lib.core register abstractions.
"""

import yaml
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Tuple
from pathlib import Path
import sys
import os

# Add ipcore_lib to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ipcore_lib.runtime.register import BitField, Register, AbstractBusInterface, RegisterArrayAccessor


class MockBusInterface(AbstractBusInterface):
    """Mock bus interface for GUI operations (no actual hardware access)."""

    def __init__(self):
        self._memory = {}

    def read_word(self, address: int) -> int:
        return self._memory.get(address, 0)

    def write_word(self, address: int, data: int) -> None:
        self._memory[address] = data & 0xFFFFFFFF


@dataclass
class MemoryMapProject:
    """
    Top-level container for a memory map project.

    This represents the complete state of a memory map design,
    including metadata and all registers/arrays.
    """
    name: str = "Untitled Memory Map"
    description: str = ""
    base_address: int = 0x40000000
    registers: List[Register] = field(default_factory=list)
    register_arrays: List[RegisterArrayAccessor] = field(default_factory=list)
    file_path: Optional[Path] = None

    def __post_init__(self):
        """Initialize with mock bus interface."""
        self._bus = MockBusInterface()

    def validate(self) -> List[str]:
        """
        Validate the memory map for errors and conflicts.

        Returns:
            List of validation error messages
        """
        errors = []

        # Check for address overlaps between registers
        addresses = set()
        for register in self.registers:
            if register.offset in addresses:
                errors.append(f"Address overlap at 0x{register.offset:04X} (register: {register.name})")
            addresses.add(register.offset)

        # Check for address overlaps with register arrays
        for array in self.register_arrays:
            array_info = array.get_info()
            start_addr = array._base_offset
            end_addr = start_addr + (array._count * array._stride) - 1

            for addr in range(start_addr, end_addr + 1, 4):  # Check word-aligned addresses
                if addr in addresses:
                    errors.append(f"Address overlap at 0x{addr:04X} (array: {array._name})")
                addresses.add(addr)

        # Validate individual registers
        for register in self.registers:
            reg_errors = self._validate_register(register)
            errors.extend(reg_errors)

        return errors

    def _validate_register(self, register: Register) -> List[str]:
        """Validate a single register for bit field conflicts."""
        errors = []

        # Check for bit field overlaps
        used_bits = [False] * 32

        for field_name, field in register._fields.items():
            for bit_pos in range(field.offset, field.offset + field.width):
                if bit_pos >= 32:
                    errors.append(f"Register {register.name}: Field {field_name} extends beyond 32 bits")
                    break

                if used_bits[bit_pos]:
                    errors.append(f"Register {register.name}: Bit {bit_pos} used by multiple fields")
                used_bits[bit_pos] = True

        return errors

    def add_register(self, name: str, offset: int, description: str = "") -> Register:
        """Add a new register to the project."""
        register = Register(
            name=name,
            offset=offset,
            bus=self._bus,
            fields=[],
            description=description
        )
        self.registers.append(register)
        return register

    def add_register_array(self, name: str, base_offset: int, count: int,
                          stride: int = 4, description: str = "") -> RegisterArrayAccessor:
        """Add a new register array to the project."""
        array = RegisterArrayAccessor(
            name=name,
            base_offset=base_offset,
            count=count,
            stride=stride,
            field_template=[],
            bus_interface=self._bus
        )
        self.register_arrays.append(array)
        return array

    def remove_register(self, register: Register):
        """Remove a register from the project."""
        if register in self.registers:
            self.registers.remove(register)

    def remove_register_array(self, array: RegisterArrayAccessor):
        """Remove a register array from the project."""
        if array in self.register_arrays:
            self.register_arrays.remove(array)

    def get_all_items(self) -> List[Union[Register, RegisterArrayAccessor]]:
        """Get all registers and arrays in the project."""
        return self.registers + self.register_arrays


def _normalize_access(access_str: str) -> str:
    """
    Normalize access string to ipcore_lib format.

    Maps:
    - 'read-write' -> 'rw'
    - 'read-only' -> 'ro'
    - 'write-only' -> 'wo'
    - 'write-1-to-clear' -> 'rw1c'
    """
    access_map = {
        'read-write': 'rw',
        'read-only': 'ro',
        'write-only': 'wo',
        'write-1-to-clear': 'rw1c',
        'rw': 'rw',
        'ro': 'ro',
        'wo': 'wo',
        'rw1c': 'rw1c'
    }
    normalized = access_map.get(access_str.lower())
    if normalized is None:
        raise ValueError(f"Unknown access type: {access_str}")
    return normalized


def _parse_bits(bits_def: Union[str, int]) -> Tuple[int, int]:
    """
    Helper to parse bit definitions into offset and width.

    Supports formats:
    - 'bits: "[7:4]"' -> offset=4, width=4
    - 'bits: "[0:0]"' -> offset=0, width=1
    - 'bit: 0' (legacy) -> offset=0, width=1
    - Direct int (legacy) -> offset=int, width=1
    """
    if isinstance(bits_def, int):
        return bits_def, 1
    if isinstance(bits_def, str):
        if ':' in bits_def:
            # Handle '[7:4]' or '7:4' format
            clean_def = bits_def.strip('[]').strip()
            high, low = map(int, clean_def.split(':'))
            return low, (high - low + 1)
        else:
            # Handle single bit as string
            return int(bits_def), 1
    raise ValueError(f"Invalid bit definition: {bits_def}")


def load_from_yaml(file_path: Union[str, Path]) -> MemoryMapProject:
    """
    Load a memory map project from a YAML file.

    Supports both formats:
    - Legacy: {name, description, base_address, registers: [...]}
    - New: [{name, description, addressBlocks: [...]}]

    Args:
        file_path: Path to the YAML file

    Returns:
        MemoryMapProject instance

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML parsing fails
        ValueError: If YAML structure is invalid
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # Detect format: list (new) or dict (legacy)
    if isinstance(data, list):
        # New format: list of memory maps
        if not data:
            raise ValueError("Empty memory map list")
        mem_map = data[0]  # Use first memory map
        return _load_new_format(mem_map, file_path)
    elif isinstance(data, dict):
        # Legacy format: single dict
        return _load_legacy_format(data, file_path)
    else:
        raise ValueError("Invalid YAML structure: root must be a list or dictionary")


def _load_legacy_format(data: dict, file_path: Path) -> MemoryMapProject:
    """Load legacy format: {name, description, base_address, registers}"""
    # Create project with metadata
    project = MemoryMapProject(
        name=data.get('name', file_path.stem),
        description=data.get('description', ''),
        base_address=data.get('base_address', 0x40000000),
        file_path=file_path
    )

    # Load registers
    for reg_info in data.get('registers', []):
        _load_register(project, reg_info, base_offset=0)

    return project


def _load_new_format(mem_map: dict, file_path: Path) -> MemoryMapProject:
    """Load new format: {name, description, addressBlocks: [...]}"""
    # Create project with metadata
    project = MemoryMapProject(
        name=mem_map.get('name', file_path.stem),
        description=mem_map.get('description', ''),
        base_address=0x40000000,  # Default for new format
        file_path=file_path
    )

    # Process address blocks
    for addr_block in mem_map.get('addressBlocks', []):
        block_offset = addr_block.get('offset', 0)
        default_reg_width = addr_block.get('defaultRegWidth', 32) // 8  # Convert bits to bytes

        # Track current offset for auto-calculation
        current_offset = 0

        # Load registers within this address block
        for reg_info in addr_block.get('registers', []):
            # If register doesn't have explicit offset, use auto-calculated one
            if 'offset' not in reg_info:
                reg_info = reg_info.copy()  # Don't modify original
                reg_info['offset'] = current_offset

            _load_register(project, reg_info, base_offset=block_offset)

            # Calculate next offset based on register type
            if 'registers' in reg_info and 'count' in reg_info:
                # Nested array: size = count * stride
                current_offset = reg_info['offset'] + (reg_info['count'] * reg_info.get('stride', default_reg_width))
            elif 'count' in reg_info:
                # Simple array: size = count * stride
                current_offset = reg_info['offset'] + (reg_info['count'] * reg_info.get('stride', default_reg_width))
            else:
                # Single register: size = default width
                current_offset = reg_info['offset'] + default_reg_width

    return project


def _load_register(project: MemoryMapProject, reg_info: dict, base_offset: int = 0):
    """
    Load a register or nested register structure.

    Handles:
    - Simple registers with fields
    - Register arrays (count > 1)
    - Nested registers within arrays (new format)
    """
    # Check if this has nested registers (new nested format)
    if 'registers' in reg_info and 'count' in reg_info:
        # This is a register array with nested sub-registers
        _load_nested_register_array(project, reg_info, base_offset)
        return

    # Parse fields
    fields = []
    for field_info in reg_info.get('fields', []):
        # Parse bit definition (supports both 'bit' and 'bits')
        bits_value = field_info.get('bits') or field_info.get('bit')
        if bits_value is None:
            continue

        offset, width = _parse_bits(bits_value)

        field = BitField(
            name=field_info['name'],
            offset=offset,
            width=width,
            access=_normalize_access(field_info.get('access', 'read-write')),
            description=field_info.get('description', ''),
            reset_value=field_info.get('reset', None)
        )
        fields.append(field)

    # Check if this is a register array (simple, without nested registers)
    if 'count' in reg_info:
        array = RegisterArrayAccessor(
            name=reg_info['name'],
            base_offset=base_offset + reg_info.get('offset', 0),
            count=reg_info['count'],
            stride=reg_info.get('stride', 4),
            field_template=fields,
            bus_interface=project._bus
        )
        project.register_arrays.append(array)
    else:
        # Single register
        register = Register(
            name=reg_info['name'],
            offset=base_offset + reg_info.get('offset', 0),
            bus=project._bus,
            fields=fields,
            description=reg_info.get('description', '')
        )
        project.registers.append(register)


def _load_nested_register_array(project: MemoryMapProject, array_info: dict, base_offset: int = 0):
    """
    Load nested register arrays (new format).

    Example: DESCRIPTOR[64] containing SRC_ADDR, DST_ADDR, LENGTH registers

    Creates flattened registers with hierarchical names like:
    - DESCRIPTOR[0].SRC_ADDR
    - DESCRIPTOR[0].DST_ADDR
    - DESCRIPTOR[1].SRC_ADDR

    These registers are marked with metadata to allow UI grouping.
    """
    array_name = array_info['name']
    count = array_info['count']
    stride = array_info.get('stride', 4)
    array_base = base_offset + array_info.get('offset', 0)

    # Create individual registers for each array instance
    for idx in range(count):
        instance_offset = array_base + (idx * stride)

        # Process each sub-register within this array instance
        for sub_reg_info in array_info['registers']:
            sub_reg_name = sub_reg_info['name']
            sub_reg_offset = sub_reg_info.get('offset', 0)

            # Parse fields
            fields = []
            for field_info in sub_reg_info.get('fields', []):
                bits_value = field_info.get('bits') or field_info.get('bit')
                if bits_value is None:
                    continue

                offset, width = _parse_bits(bits_value)

                field = BitField(
                    name=field_info['name'],
                    offset=offset,
                    width=width,
                    access=_normalize_access(field_info.get('access', 'read-write')),
                    description=field_info.get('description', ''),
                    reset_value=field_info.get('reset', None)
                )
                fields.append(field)

            # Create flattened register with hierarchical name using bracket notation
            register = Register(
                name=f"{array_name}[{idx}].{sub_reg_name}",
                offset=instance_offset + sub_reg_offset,
                bus=project._bus,
                fields=fields,
                description=sub_reg_info.get('description', '')
            )

            # Add metadata for UI grouping
            register._array_parent = array_name
            register._array_index = idx
            register._array_base = array_base
            register._array_count = count
            register._array_stride = stride

            project.registers.append(register)


def save_to_yaml(project: MemoryMapProject, file_path: Union[str, Path], use_new_format: bool = True) -> None:
    """
    Save a memory map project to a YAML file.

    Args:
        project: MemoryMapProject instance to save
        file_path: Destination file path
        use_new_format: If True, use new addressBlocks format; if False, use legacy format
    """
    file_path = Path(file_path)

    if use_new_format:
        _save_new_format(project, file_path)
    else:
        _save_legacy_format(project, file_path)

    # Update project file path
    project.file_path = file_path


def _save_legacy_format(project: MemoryMapProject, file_path: Path) -> None:
    """Save in legacy format: {name, description, base_address, registers}"""
    # Build YAML data structure
    data = {
        'name': project.name,
        'description': project.description,
        'base_address': project.base_address,
        'registers': []
    }

    # Add regular registers
    for register in project.registers:
        reg_data = _register_to_dict(register)
        data['registers'].append(reg_data)

    # Add register arrays
    for array in project.register_arrays:
        array_data = _register_array_to_dict(array)
        data['registers'].append(array_data)

    # Write YAML file
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)


def _save_new_format(project: MemoryMapProject, file_path: Path) -> None:
    """Save in new format: [{name, description, addressBlocks: [...]}]"""
    # Group registers by address ranges into blocks
    address_block = {
        'name': 'REGISTERS',
        'offset': 0,
        'usage': 'register',
        'defaultRegWidth': 32,
        'registers': []
    }

    # Add regular registers
    for register in project.registers:
        reg_data = _register_to_dict(register)
        address_block['registers'].append(reg_data)

    # Add register arrays
    for array in project.register_arrays:
        array_data = _register_array_to_dict(array)
        address_block['registers'].append(array_data)

    # Build memory map structure
    mem_map = {
        'name': project.name,
        'description': project.description,
        'addressBlocks': [address_block]
    }

    # Root is a list
    data = [mem_map]

    # Write YAML file
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)


def _register_to_dict(register: Register) -> dict:
    """Convert a Register to dictionary format."""
    reg_data = {
        'name': register.name,
        'offset': register.offset,
        'description': register.description,
        'fields': []
    }

    for field_name, field in register._fields.items():
        field_data = {
            'name': field.name,
            'access': field.access,
            'description': field.description
        }

        # Add reset value if specified
        if field.reset_value is not None:
            field_data['reset'] = field.reset_value

        # Format bit definition - always use bits: "[msb:lsb]" format
        high_bit = field.offset + field.width - 1
        field_data['bits'] = f'[{high_bit}:{field.offset}]'

        reg_data['fields'].append(field_data)

    return reg_data


def _register_array_to_dict(array: RegisterArrayAccessor) -> dict:
    """Convert a RegisterArrayAccessor to dictionary format."""
    array_data = {
        'name': array._name,
        'offset': array._base_offset,
        'count': array._count,
        'stride': array._stride,
        'description': f"Register array with {array._count} entries",
        'fields': []
    }

    # Add field template
    for field in array._field_template:
        field_data = {
            'name': field.name,
            'access': field.access,
            'description': field.description
        }

        # Add reset value if specified
        if field.reset_value is not None:
            field_data['reset'] = field.reset_value

        # Format bit definition - always use bits: "[msb:lsb]" format
        high_bit = field.offset + field.width - 1
        field_data['bits'] = f'[{high_bit}:{field.offset}]'

        array_data['fields'].append(field_data)

    return array_data


def create_new_project(name: str = "New Memory Map") -> MemoryMapProject:
    """Create a new, empty memory map project."""
    project = MemoryMapProject(name=name)

    # Add a sample register to get started
    sample_reg = project.add_register("control", 0x00, "Main control register")
    sample_reg._fields["enable"] = BitField("enable", 0, 1, "rw", "Enable bit")

    return project
