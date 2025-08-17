"""
Register Map Loader - Layer 1

This module implements the YAML-driven memory map loader that dynamically
constructs IP core drivers from human-readable memory map definitions.
"""

import yaml
from dataclasses import dataclass
from typing import List, Dict, Any, Union, Tuple
from bus_interface import AbstractBusInterface

# Import the centralized AccessType enum from the core module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from fpga_lib.core import AccessType


@dataclass
class BitField:
    """
    Represents a bit field within a register.

    Attributes:
        name: Human-readable name of the bit field
        offset: Bit position within the register (0-based)
        width: Number of bits in the field
        access: Access type (AccessType enum)
        description: Description of the bit field
    """
    name: str
    offset: int
    width: int
    access: AccessType = AccessType.RW
    description: str = ''


class Register:
    """
    Represents a hardware register with bit fields.

    This class handles bit-wise operations for reading and writing
    individual bit fields within a register, with proper access control.
    """

    def __init__(self, name: str, offset: int, bus_interface: AbstractBusInterface,
                 fields: List[BitField], description: str = ''):
        self._name = name
        self._offset = offset
        self._bus = bus_interface
        self._fields = {field.name: field for field in fields}
        self._description = description

    @property
    def name(self) -> str:
        """Get the register name."""
        return self._name

    @property
    def offset(self) -> int:
        """Get the register offset."""
        return self._offset

    @property
    def description(self) -> str:
        """Get the register description."""
        return self._description

    def read(self) -> int:
        """Read the entire register value."""
        return self._bus.read_word(self._offset)

    def write(self, value: int) -> None:
        """Write the entire register value."""
        self._bus.write_word(self._offset, value)

    def __getattr__(self, name: str):
        """
        Dynamic attribute access for bit fields.

        This creates properties for each bit field that handle
        read/write operations with proper access control.
        """
        if name not in self._fields:
            raise AttributeError(f"Register '{self._name}' has no bit-field named '{name}'")

        field = self._fields[name]
        mask = ((1 << field.width) - 1) << field.offset

        # For getter-only access, return the computed value directly
        if field.access == AccessType.WO or field.access == 'wo':
            raise AttributeError(f"Bit-field '{name}' is write-only")

        # Return the current field value
        reg_value = self.read()
        return (reg_value & mask) >> field.offset

    def __setattr__(self, name: str, value) -> None:
        """Handle setting bit field values."""
        # Handle normal attributes during initialization
        if name.startswith('_') or name in ['read', 'write', 'get_fields', 'get_field_info']:
            super().__setattr__(name, value)
            return

        # Check if this is a bit field
        if hasattr(self, '_fields') and name in self._fields:
            field = self._fields[name]
            mask = ((1 << field.width) - 1) << field.offset

            if field.access == AccessType.RO or field.access == 'ro':
                raise AttributeError(f"Bit-field '{name}' is read-only")

            # Validate value fits in field width
            max_value = (1 << field.width) - 1
            if value > max_value:
                raise ValueError(f"Value {value} exceeds field width {field.width}")

            if field.access == AccessType.RW or field.access == 'rw':
                # Read-modify-write for RW fields
                reg_value = self.read()
                cleared_val = reg_value & ~mask
                new_reg_value = cleared_val | ((value << field.offset) & mask)
            elif field.access == AccessType.RW1C or field.access == 'rw1c':
                # Read-write-1-to-clear: writing 1 clears the bit, writing 0 has no effect
                reg_value = self.read()
                clear_mask = (value << field.offset) & mask
                new_reg_value = reg_value & ~clear_mask
            else:
                # Write-only field, don't read current value
                new_reg_value = (value << field.offset) & mask

            self.write(new_reg_value)
        else:
            super().__setattr__(name, value)

    def get_fields(self) -> List[str]:
        """Get list of available field names."""
        return list(self._fields.keys())

    def get_field_info(self, field_name: str) -> BitField:
        """Get information about a specific field."""
        if field_name not in self._fields:
            raise ValueError(f"Unknown field: {field_name}")
        return self._fields[field_name]


class IpCoreDriver:
    """
    Container for all register objects.

    This class is dynamically populated by the YAML loader with
    register objects based on the memory map definition.
    """

    def __init__(self, bus_interface: AbstractBusInterface, name: str = "IP Core"):
        self._bus = bus_interface
        self._name = name
        self._registers = {}

    def add_register(self, register: Register) -> None:
        """Add a register to the driver."""
        self._registers[register.name] = register
        setattr(self, register.name, register)

    def get_registers(self) -> Dict[str, Register]:
        """Get all registers in the driver."""
        return self._registers.copy()

    def get_register_summary(self) -> Dict[str, int]:
        """Get a summary of all register values for debugging."""
        return {name: reg.read() for name, reg in self._registers.items()}


def _parse_bits(bits_def: Union[int, str, List]) -> Tuple[int, int]:
    """
    Helper function to parse bit definitions from YAML.

    Supports:
    - Single bit: bit: 0
    - Bit range: bits: [7:4]
    - List format: bits: [7, 4] (high, low)

    Returns:
        Tuple of (offset, width)
    """
    if isinstance(bits_def, int):
        return bits_def, 1

    if isinstance(bits_def, str) and ':' in bits_def:
        # Handle "7:4" format
        high, low = map(int, bits_def.strip('[]').split(':'))
        return low, (high - low + 1)

    if isinstance(bits_def, list) and len(bits_def) == 2:
        # Handle [high, low] format
        high, low = bits_def
        if isinstance(high, str) and ':' in high:
            # Handle ["7:4"] format
            high, low = map(int, high.split(':'))
        return low, (high - low + 1)

    raise ValueError(f"Invalid bit definition: {bits_def}")


def _access_enum_to_string(access: AccessType) -> str:
    """Convert AccessType enum to string format for core register module."""
    if access == AccessType.RO:
        return 'ro'
    elif access == AccessType.WO:
        return 'wo'
    elif access == AccessType.RW:
        return 'rw'
    elif access == AccessType.RW1C:
        return 'rw1c'
    else:
        raise ValueError(f"Unknown access type: {access}")


def load_from_yaml(yaml_path: str, bus_interface: AbstractBusInterface,
                   driver_name: str = "GPIO Driver") -> IpCoreDriver:
    """
    Load a register map from YAML and build a driver object.

    Args:
        yaml_path: Path to the YAML memory map file
        bus_interface: Bus interface for hardware communication
        driver_name: Name for the driver instance

    Returns:
        Configured IP core driver with all registers

    Raises:
        FileNotFoundError: If YAML file doesn't exist
        ValueError: If YAML format is invalid
    """
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Memory map file not found: {yaml_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format in {yaml_path}: {e}")

    if 'registers' not in data:
        raise ValueError("YAML file must contain a 'registers' section")

    driver = IpCoreDriver(bus_interface, driver_name)

    for reg_info in data['registers']:
        # Validate required fields
        if 'name' not in reg_info or 'offset' not in reg_info:
            raise ValueError("Each register must have 'name' and 'offset' fields")

        fields = []

        # Process bit fields if they exist
        for field_info in reg_info.get('fields', []):
            if 'name' not in field_info:
                raise ValueError("Each field must have a 'name'")

            # Parse bit definition
            if 'bit' in field_info:
                offset, width = _parse_bits(field_info['bit'])
            elif 'bits' in field_info:
                offset, width = _parse_bits(field_info['bits'])
            else:
                raise ValueError(f"Field '{field_info['name']}' must specify 'bit' or 'bits'")

            # Parse access type
            access_str = field_info.get('access', 'rw').upper()
            try:
                access = AccessType[access_str]
            except KeyError:
                raise ValueError(f"Invalid access type '{access_str}'. Must be 'ro', 'rw', 'wo', or 'rw1c'")

            fields.append(BitField(
                name=field_info['name'],
                offset=offset,
                width=width,
                access=_access_enum_to_string(access),
                description=field_info.get('description', '')
            ))

        # Create register object
        register = Register(
            name=reg_info['name'],
            offset=reg_info['offset'],
            bus_interface=bus_interface,
            fields=fields,
            description=reg_info.get('description', '')
        )

        driver.add_register(register)

    return driver


def validate_yaml_memory_map(yaml_path: str) -> List[str]:
    """
    Validate a YAML memory map file and return any issues found.

    Args:
        yaml_path: Path to the YAML file to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        return [f"File not found: {yaml_path}"]
    except yaml.YAMLError as e:
        return [f"Invalid YAML format: {e}"]

    if not isinstance(data, dict):
        errors.append("Root element must be a dictionary")
        return errors

    if 'registers' not in data:
        errors.append("Missing 'registers' section")
        return errors

    if not isinstance(data['registers'], list):
        errors.append("'registers' must be a list")
        return errors

    register_names = set()
    register_offsets = set()

    for i, reg_info in enumerate(data['registers']):
        reg_prefix = f"Register {i}"

        if not isinstance(reg_info, dict):
            errors.append(f"{reg_prefix}: Must be a dictionary")
            continue

        # Check required fields
        if 'name' not in reg_info:
            errors.append(f"{reg_prefix}: Missing 'name' field")
        elif reg_info['name'] in register_names:
            errors.append(f"{reg_prefix}: Duplicate register name '{reg_info['name']}'")
        else:
            register_names.add(reg_info['name'])

        if 'offset' not in reg_info:
            errors.append(f"{reg_prefix}: Missing 'offset' field")
        elif not isinstance(reg_info['offset'], int):
            errors.append(f"{reg_prefix}: 'offset' must be an integer")
        elif reg_info['offset'] in register_offsets:
            errors.append(f"{reg_prefix}: Duplicate offset 0x{reg_info['offset']:X}")
        else:
            register_offsets.add(reg_info['offset'])

        # Validate fields if present
        if 'fields' in reg_info:
            if not isinstance(reg_info['fields'], list):
                errors.append(f"{reg_prefix}: 'fields' must be a list")
                continue

            field_names = set()
            used_bits = set()

            for j, field_info in enumerate(reg_info['fields']):
                field_prefix = f"{reg_prefix}, Field {j}"

                if not isinstance(field_info, dict):
                    errors.append(f"{field_prefix}: Must be a dictionary")
                    continue

                if 'name' not in field_info:
                    errors.append(f"{field_prefix}: Missing 'name' field")
                elif field_info['name'] in field_names:
                    errors.append(f"{field_prefix}: Duplicate field name '{field_info['name']}'")
                else:
                    field_names.add(field_info['name'])

                # Check bit definition
                has_bit = 'bit' in field_info
                has_bits = 'bits' in field_info

                if not has_bit and not has_bits:
                    errors.append(f"{field_prefix}: Must specify 'bit' or 'bits'")
                elif has_bit and has_bits:
                    errors.append(f"{field_prefix}: Cannot specify both 'bit' and 'bits'")
                else:
                    try:
                        if has_bit:
                            bit_def = field_info['bit']
                        else:
                            bit_def = field_info['bits']
                        offset, width = _parse_bits(bit_def)

                        # Check for bit overlap
                        field_bits = set(range(offset, offset + width))
                        if field_bits & used_bits:
                            errors.append(f"{field_prefix}: Bit overlap with other fields")
                        used_bits.update(field_bits)

                        # Check for valid bit range
                        if offset < 0 or offset + width > 32:
                            errors.append(f"{field_prefix}: Bits out of valid range (0-31)")

                    except ValueError as e:
                        errors.append(f"{field_prefix}: {e}")

                # Check access type
                if 'access' in field_info:
                    access = field_info['access'].upper()
                    if access not in ['RO', 'RW', 'WO', 'RW1C']:
                        errors.append(f"{field_prefix}: Invalid access type '{access}'. Must be 'ro', 'rw', 'wo', or 'rw1c'")

    return errors
