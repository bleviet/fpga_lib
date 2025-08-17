"""
Memory Map Core - Model Layer

Pure Python implementation of memory map data structures and business logic.
Integrates with fpga_lib.core register abstractions.
"""

import yaml
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Tuple
from pathlib import Path
import sys
import os

# Add fpga_lib to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fpga_lib.core import BitField, Register, AbstractBusInterface, RegisterArrayAccessor


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


def _parse_bits(bits_def: Union[str, int]) -> Tuple[int, int]:
    """Helper to parse 'bit: 0' or 'bits: [7:4]' into offset and width."""
    if isinstance(bits_def, int):
        return bits_def, 1
    if isinstance(bits_def, str):
        if ':' in bits_def:
            # Handle '[7:4]' format
            clean_def = bits_def.strip('[]')
            high, low = map(int, clean_def.split(':'))
            return low, (high - low + 1)
        else:
            # Handle single bit as string
            return int(bits_def), 1
    raise ValueError(f"Invalid bit definition: {bits_def}")


def load_from_yaml(file_path: Union[str, Path]) -> MemoryMapProject:
    """
    Load a memory map project from a YAML file.

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

    if not isinstance(data, dict):
        raise ValueError("Invalid YAML structure: root must be a dictionary")

    # Create project with metadata
    project = MemoryMapProject(
        name=data.get('name', file_path.stem),
        description=data.get('description', ''),
        base_address=data.get('base_address', 0x40000000),
        file_path=file_path
    )

    # Load registers
    for reg_info in data.get('registers', []):
        fields = []
        for field_info in reg_info.get('fields', []):
            # Parse bit definition
            offset, width = _parse_bits(field_info.get('bit') or field_info.get('bits', 0))

            field = BitField(
                name=field_info['name'],
                offset=offset,
                width=width,
                access=field_info.get('access', 'rw').lower(),
                description=field_info.get('description', ''),
                reset_value=field_info.get('reset', None)
            )
            fields.append(field)

        # Check if this is a register array
        if 'count' in reg_info:
            array = RegisterArrayAccessor(
                name=reg_info['name'],
                base_offset=reg_info['offset'],
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
                offset=reg_info['offset'],
                bus=project._bus,
                fields=fields,
                description=reg_info.get('description', '')
            )
            project.registers.append(register)

    return project


def save_to_yaml(project: MemoryMapProject, file_path: Union[str, Path]) -> None:
    """
    Save a memory map project to a YAML file.

    Args:
        project: MemoryMapProject instance to save
        file_path: Destination file path
    """
    file_path = Path(file_path)

    # Build YAML data structure
    data = {
        'name': project.name,
        'description': project.description,
        'base_address': project.base_address,
        'registers': []
    }

    # Add regular registers
    for register in project.registers:
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

            # Format bit definition
            if field.width == 1:
                field_data['bit'] = field.offset
            else:
                high_bit = field.offset + field.width - 1
                field_data['bits'] = f'[{high_bit}:{field.offset}]'

            reg_data['fields'].append(field_data)

        data['registers'].append(reg_data)

    # Add register arrays
    for array in project.register_arrays:
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

            if field.width == 1:
                field_data['bit'] = field.offset
            else:
                high_bit = field.offset + field.width - 1
                field_data['bits'] = f'[{high_bit}:{field.offset}]'

            array_data['fields'].append(field_data)

        data['registers'].append(array_data)

    # Write YAML file
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)

    # Update project file path
    project.file_path = file_path


def create_new_project(name: str = "New Memory Map") -> MemoryMapProject:
    """Create a new, empty memory map project."""
    project = MemoryMapProject(name=name)

    # Add a sample register to get started
    sample_reg = project.add_register("control", 0x00, "Main control register")
    sample_reg._fields["enable"] = BitField("enable", 0, 1, "rw", "Enable bit")

    return project
