"""
Register utility functions for validation, testing, and documentation.

This module provides utility functions for working with registers including
layout validation, test pattern generation, and documentation generation.
"""

from typing import List, Union, Any
from .bit_field import BitField
from .register_def import Register

try:
    from bitstring import BitArray
    BITSTRING_AVAILABLE = True
except ImportError:
    BITSTRING_AVAILABLE = False
    BitArray = None


def validate_register_layout(fields: List[BitField]) -> bool:
    """
    Validate that bit fields don't overlap in a register layout.

    Args:
        fields: List of BitField objects to validate

    Returns:
        True if layout is valid, False if fields overlap
    """
    if BITSTRING_AVAILABLE:
        used_bits = BitArray(length=32)

        for field in fields:
            field_mask = BitArray(length=32)
            field_mask[field.offset:field.offset + field.width] = '1' * field.width

            # Check for overlaps using bitstring operations
            if (used_bits & field_mask).any():
                return False

            used_bits |= field_mask
    else:
        # Fallback validation without bitstring
        used_bits = [False] * 32

        for field in fields:
            for bit_pos in range(field.offset, field.offset + field.width):
                if used_bits[bit_pos]:
                    return False
                used_bits[bit_pos] = True

    return True


def generate_test_patterns(fields: List[BitField], reg_width: int = 32) -> List[Union[int, Any]]:
    """
    Generate comprehensive test patterns for a register using bitstring if available.

    Args:
        fields: List of BitField objects
        reg_width: Width of the register in bits

    Returns:
        List of test patterns (BitArray if available, otherwise int)
    """
    patterns = []

    if BITSTRING_AVAILABLE:
        # Walking ones pattern
        for i in range(reg_width):
            walking_one = BitArray(length=reg_width)
            walking_one[i] = 1
            patterns.append(walking_one)

        # Walking zeros pattern
        for i in range(reg_width):
            walking_zero = BitArray('1' * reg_width)
            walking_zero[i] = 0
            patterns.append(walking_zero)

        # Field-specific patterns
        for field in fields:
            if field.access in ['rw', 'wo', 'w1sc']:
                # All ones in this field
                pattern = BitArray(length=reg_width)
                pattern[field.offset:field.offset + field.width] = '1' * field.width
                patterns.append(pattern)

                # Alternating pattern in this field
                if field.width > 1:
                    alt_pattern = BitArray(length=reg_width)
                    field_alt = BitArray('01' * (field.width // 2) + '0' * (field.width % 2))
                    alt_pattern[field.offset:field.offset + field.width] = field_alt
                    patterns.append(alt_pattern)
    else:
        # Fallback patterns without bitstring
        for i in range(min(reg_width, 8)):  # Limit for performance
            patterns.append(1 << i)
            patterns.append(~(1 << i) & ((1 << reg_width) - 1))

        for field in fields:
            if field.access in ['rw', 'wo', 'w1sc']:
                field_mask = ((1 << field.width) - 1) << field.offset
                patterns.append(field_mask)

    return patterns


def generate_register_documentation(register: Register) -> str:
    """
    Generate human-readable documentation for a register with bit diagrams.

    Args:
        register: Register object to document

    Returns:
        Formatted documentation string with ASCII bit diagrams
    """
    doc = []

    doc.append(f"\n## {register.name.upper()} (Offset: 0x{register.offset:04X})")
    doc.append(f"Width: {register.width} bits")

    if register.description:
        doc.append(f"Description: {register.description}")

    if register.fields:
        doc.append("\n### Bit Layout:")
        doc.append("```")

        # Create bit position header (adjust for register width)
        bit_header = "Bit: " + "".join(f"{i%10:1d}" for i in range(register.width-1, -1, -1))
        doc.append(bit_header)

        # Create field visualization
        field_line = "     " + "".join("." for _ in range(register.width))
        field_chars = list(field_line)

        for field in register.fields:
            # Mark field boundaries
            for i in range(field.offset, field.offset + field.width):
                pos = 5 + (register.width - 1 - i)  # Account for "Bit: " prefix
                if i == field.offset:
                    field_chars[pos] = '['
                elif i == field.offset + field.width - 1:
                    field_chars[pos] = ']'
                else:
                    field_chars[pos] = '-'

        doc.append("".join(field_chars))
        doc.append("```")

        # Field details table
        doc.append("\n### Fields:")
        doc.append("| Field | Bits | Access | Reset | Description |")
        doc.append("|-------|------|--------|-------|-------------|")

        for field in register.fields:
            if field.width == 1:
                bits_str = str(field.offset)
            else:
                bits_str = f"{field.offset + field.width - 1}:{field.offset}"

            reset_val = field.reset_value if field.reset_value is not None else 'N/A'
            access_str = field.access.upper()
            desc = field.description or ''

            doc.append(f"| {field.name} | {bits_str} | {access_str} | {reset_val} | {desc} |")

    return '\n'.join(doc)
