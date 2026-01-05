"""
Bit Field Operations

Business logic for managing bit fields including validation, offset calculation,
and field manipulation operations.
"""

from typing import List, Tuple, Optional
from fpga_lib.core import BitField, Register, RegisterArrayAccessor


class BitFieldOperations:
    """Encapsulates bit field manipulation logic."""

    @staticmethod
    def get_sorted_fields(item) -> List[BitField]:
        """Get fields sorted by offset."""
        if isinstance(item, Register):
            fields = list(item._fields.values())
        elif isinstance(item, RegisterArrayAccessor):
            fields = list(item._field_template)
        else:
            return []
        return sorted(fields, key=lambda f: f.offset)

    @staticmethod
    def update_item_fields(item, fields_list: List[BitField]):
        """Update the item with the modified fields list."""
        if isinstance(item, Register):
            item._fields = {field.name: field for field in fields_list}
        elif isinstance(item, RegisterArrayAccessor):
            item._field_template = fields_list

    @staticmethod
    def validate_field_fits(new_field: BitField, existing_fields: List[BitField],
                           exclude_field: Optional[BitField] = None) -> Tuple[bool, str]:
        """
        Validate that a field fits within the 32-bit register without overlaps.

        Returns:
            tuple: (is_valid, error_message)
        """
        if new_field.offset < 0:
            return False, "Offset cannot be negative"

        if new_field.width < 1 or new_field.width > 32:
            return False, "Width must be between 1 and 32"

        if new_field.offset + new_field.width > 32:
            return False, f"Field extends beyond register (bit {new_field.offset + new_field.width - 1} > 31)"

        # Check for overlaps with existing fields
        for existing_field in existing_fields:
            if exclude_field and existing_field == exclude_field:
                continue

            # Check if fields overlap
            if not (new_field.offset + new_field.width <= existing_field.offset or
                    existing_field.offset + existing_field.width <= new_field.offset):
                return False, f"Field overlaps with '{existing_field.name}' (bits {existing_field.offset}-{existing_field.offset + existing_field.width - 1})"

        return True, ""

    @staticmethod
    def find_available_space(fields_list: List[BitField], width: int) -> int:
        """
        Find available space for a field of given width.

        Returns:
            int: Available offset, or -1 if no space
        """
        if width < 1 or width > 32:
            return -1

        if not fields_list:
            return 0 if width <= 32 else -1

        # Sort fields by offset
        sorted_fields = sorted(fields_list, key=lambda f: f.offset)

        # Check space at the beginning
        if sorted_fields[0].offset >= width:
            return 0

        # Check gaps between fields
        for i in range(len(sorted_fields) - 1):
            current_end = sorted_fields[i].offset + sorted_fields[i].width
            next_start = sorted_fields[i + 1].offset
            gap_size = next_start - current_end

            if gap_size >= width:
                return current_end

        # Check space at the end
        last_field = sorted_fields[-1]
        last_end = last_field.offset + last_field.width
        if last_end + width <= 32:
            return last_end

        return -1  # No space available

    @staticmethod
    def recalculate_offsets(fields_list: List[BitField]):
        """Recalculate field offsets to pack them sequentially."""
        fields_list.sort(key=lambda f: f.offset)
        current_offset = 0
        for field in fields_list:
            field.offset = current_offset
            current_offset += field.width

    @staticmethod
    def recalculate_offsets_preserving_field(fields_list: List[BitField],
                                            preserve_field: BitField):
        """
        Recalculate field offsets while preserving the position of a specific field.
        Other fields are packed around it.
        """
        if preserve_field not in fields_list:
            return

        # Remove the preserved field from the list temporarily
        other_fields = [f for f in fields_list if f != preserve_field]
        other_fields.sort(key=lambda f: f.offset)

        preserved_start = preserve_field.offset
        preserved_end = preserve_field.offset + preserve_field.width

        # Separate fields before and after the preserved field
        fields_before = [f for f in other_fields if f.offset < preserved_start]
        fields_after = [f for f in other_fields if f.offset >= preserved_start]

        # Pack fields before the preserved field
        current_offset = 0
        for field in fields_before:
            if current_offset + field.width <= preserved_start:
                field.offset = current_offset
                current_offset += field.width
            else:
                # Move to after preserved field
                fields_after.append(field)

        # Pack fields after the preserved field
        current_offset = preserved_end
        for field in fields_after:
            field.offset = current_offset
            current_offset += field.width

    @staticmethod
    def generate_unique_field_name(existing_names: set, base_name: str = "field") -> str:
        """Generate a unique field name."""
        counter = 0
        while True:
            field_name = f"{base_name}_{counter}"
            if field_name not in existing_names:
                return field_name
            counter += 1

    @staticmethod
    def check_field_overlaps_and_gaps(field: BitField, all_fields: List[BitField]) -> Tuple[bool, bool]:
        """
        Check if a field has overlaps or gaps.

        Returns:
            tuple: (has_overlap, has_gap)
        """
        has_overlap = False
        has_gap = False

        # Check for overlaps
        for other_field in all_fields:
            if other_field != field:
                field_end = field.offset + field.width - 1
                other_end = other_field.offset + other_field.width - 1

                if (field.offset <= other_end and field_end >= other_field.offset):
                    has_overlap = True
                    break

        # Check for gaps
        if not has_overlap:
            sorted_fields = sorted(all_fields, key=lambda f: f.offset)
            field_index = sorted_fields.index(field)

            if field_index > 0:
                prev_field = sorted_fields[field_index - 1]
                expected_offset = prev_field.offset + prev_field.width
                if field.offset > expected_offset:
                    has_gap = True

        return has_overlap, has_gap
