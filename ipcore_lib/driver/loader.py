from dataclasses import dataclass
from typing import Any, Dict, List

import yaml

from ipcore_lib.runtime.register import (
    AbstractBusInterface,
    AccessType,
    BitField,
    Register,
    RegisterArrayAccessor,
)


@dataclass
class AddressBlock:
    """Simple container for registers within an address block."""

    _name: str
    _offset: int
    _bus: AbstractBusInterface


class IpCoreDriver:
    """Root driver object containing address blocks."""

    def __init__(self, bus_interface: AbstractBusInterface):
        self._bus = bus_interface


def _parse_bits(bits_def: Any) -> tuple[int, int]:
    """Helper to parse 'bit: 0' (int) or 'bits: [7:4]' (str) into (offset, width)."""
    if isinstance(bits_def, int):
        return bits_def, 1
    if isinstance(bits_def, str) and ":" in bits_def:
        # Expected format like "[7:4]" or "7:4"
        clean = bits_def.strip("[]")
        high_s, low_s = clean.split(":")
        high, low = int(high_s), int(low_s)
        return low, (high - low + 1)
    # Fallback/Default
    try:
        val = int(bits_def)
        return val, 1
    except:
        pass
    raise ValueError(f"Invalid bit definition: {bits_def}")


def load_driver(yaml_path: str, bus_interface: AbstractBusInterface) -> IpCoreDriver:
    """
    Loads a memory map from a YAML file and returns a configured IpCoreDriver.
    """
    driver = IpCoreDriver(bus_interface)

    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    # Validation: data should be a list of maps, or a single map dict?
    # The generated yaml from VHDLGenerator might need to be checked.
    # Concept doc showed a list: `- name: CSR_MAP ...`

    if isinstance(data, dict):
        # Maybe wrapped in a root key? or just one map?
        # If specific list format is expected, handle it.
        # Let's assume list of maps for now based on concept.
        data_list = [data]
    elif isinstance(data, list):
        data_list = data
    else:
        raise ValueError("Invalid YAML format: expected list or dict at root")

    for mem_map in data_list:
        # Each memory map contains address blocks
        for block_info in mem_map.get("addressBlocks", []):
            block_name = block_info["name"]
            block_offset = block_info.get("offset", 0)
            default_reg_width = block_info.get("defaultRegWidth", 32)

            # Create a block container
            block_obj = AddressBlock(_name=block_name, _offset=block_offset, _bus=bus_interface)

            # Auto-assign offsets if not specified
            auto_offset = 0
            for reg_info in block_info.get("registers") or []:
                # Get register offset (auto-assign if not present)
                if "offset" in reg_info:
                    reg_offset = reg_info["offset"]
                else:
                    # Auto-assign sequential offset based on register width
                    reg_offset = auto_offset
                    reg_width = reg_info.get("width", default_reg_width)
                    auto_offset += reg_width // 8  # Advance by register size in bytes

                # Calculate absolute offset
                reg_abs_offset = block_offset + reg_offset

                # Parse fields
                fields = []
                for field_info in reg_info.get("fields", []):
                    # Handle 'bits' vs 'bit' naming if needed, though yaml gen should be consistent
                    bits_val = field_info.get("bits")
                    if bits_val is None:
                        bits_val = field_info.get("bit", 0)

                    offset, width = _parse_bits(bits_val)

                    acc_str = field_info.get("access", "read-write").lower()
                    # Clean up Enum string representation if present (e.g., "AccessType.READ_WRITE")
                    if "accesstype." in acc_str:
                        acc_str = acc_str.split(".")[-1]
                    # Normalize underscores and dashes
                    acc_str = acc_str.replace("_", "-")

                    # Map standard YAML access strings to AccessType enum
                    access_map = {
                        "read-only": AccessType.RO,
                        "readonly": AccessType.RO,
                        "ro": AccessType.RO,
                        "write-only": AccessType.WO,
                        "writeonly": AccessType.WO,
                        "wo": AccessType.WO,
                        "read-write": AccessType.RW,
                        "readwrite": AccessType.RW,
                        "rw": AccessType.RW,
                        "write-1-to-clear": AccessType.RW1C,
                        "write1toclear": AccessType.RW1C,
                        "read-write-1-to-clear": AccessType.RW1C,
                        "rw1c": AccessType.RW1C,
                    }
                    access_type = access_map.get(acc_str, AccessType.RW)

                    fields.append(
                        BitField(
                            name=field_info["name"],
                            offset=offset,
                            width=width,
                            access=access_type,
                            description=field_info.get("description", ""),
                        )
                    )

                # Check for array
                if "count" in reg_info:
                    accessor = RegisterArrayAccessor(
                        name=reg_info["name"],
                        base_offset=reg_abs_offset,
                        count=reg_info["count"],
                        stride=reg_info.get("stride", 4),
                        field_template=fields,
                        bus_interface=bus_interface,
                    )
                    setattr(block_obj, reg_info["name"], accessor)
                else:
                    register = Register(
                        name=reg_info["name"],
                        offset=reg_abs_offset,
                        bus=bus_interface,
                        fields=fields,
                    )
                    setattr(block_obj, reg_info["name"], register)

            # Attach block to driver
            setattr(driver, block_name, block_obj)

    return driver
