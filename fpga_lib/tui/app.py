#!/usr/bin/env python

import sys
import yaml
import copy
from pathlib import Path
from typing import Optional, List, Any

# Add parent directory to path if running directly
if __name__ == "__main__":
    # Get the fpga_lib package root (two levels up from this file)
    package_root = Path(__file__).resolve().parent.parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll, Grid
from textual.widgets import Header, Footer, Tree, Label, Input, DataTable, Static, Button, Select
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.widgets.tree import TreeNode

from fpga_lib.parser.yaml import YamlIpCoreParser
from fpga_lib.model import MemoryMap, AddressBlock, Register, AccessType, BitField

class EditFieldScreen(ModalScreen):
    """Screen for editing a bit field."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+[", "cancel", "Cancel"),
    ]

    CSS = """
    EditFieldScreen {
        align: center middle;
    }

    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: auto;
        padding: 0 1;
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }

    #dialog .header {
        column-span: 2;
        height: 1;
        margin-top: 1;
        text-align: center;
        text-style: bold;
    }

    #dialog Label {
        text-align: right;
        padding-right: 1;
    }

    #dialog Button {
        width: 100%;
    }
    """

    def __init__(self, field: BitField, on_save: callable):
        super().__init__()
        self.field = field
        self.on_save = on_save

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Edit Bit Field", classes="header"),
            Label("Name:"),
            Input(value=self.field.name, id="field_name"),
            Label("Bit Offset:"),
            Input(value=str(self.field.bit_offset), id="field_offset", type="integer"),
            Label("Bit Width:"),
            Input(value=str(self.field.bit_width), id="field_width", type="integer"),
            Label("Access:"),
            Select.from_values(
                [a.value for a in AccessType],
                value=self.field.access.value,
                id="field_access"
            ),
            Label("Reset Value:"),
            Input(value=f"0x{self.field.reset_value:X}" if self.field.reset_value is not None else "0x0", id="field_reset"),
            Label("Description:"),
            Input(value=self.field.description or "", id="field_desc"),
            Button("Cancel", variant="error", id="cancel"),
            Button("Save", variant="success", id="save"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._save_changes()
        elif event.button.id == "cancel":
            self.dismiss()

    def action_cancel(self) -> None:
        self.dismiss()

    def _save_changes(self) -> None:
        try:
            name = self.query_one("#field_name", Input).value
            offset = int(self.query_one("#field_offset", Input).value)
            width = int(self.query_one("#field_width", Input).value)
            access = self.query_one("#field_access", Select).value
            reset_str = self.query_one("#field_reset", Input).value
            desc = self.query_one("#field_desc", Input).value

            # Parse reset value
            if reset_str.lower().startswith("0x"):
                reset = int(reset_str, 16)
            else:
                reset = int(reset_str)

            # Call on_save with new values instead of updating directly
            self.on_save(name, offset, width, access, reset, desc)
            self.dismiss()
        except ValueError as e:
            self.notify(f"Invalid input: {e}", severity="error")

class MemoryMapEditorApp(App):
    """A Textual TUI for editing Memory Map YAML files."""

    def __init__(self, file_path: Optional[Path] = None):
        super().__init__()
        self.file_path = file_path
        self.memory_maps: list[MemoryMap] = []
        self.current_register: Optional[Register] = None
        self.table_mode = "NORMAL"  # NORMAL or INSERT
        self.table_cursor_row = 0
        self.table_cursor_col = 0

        # Undo/Redo stacks
        self.undo_stack: List[List[MemoryMap]] = []
        self.redo_stack: List[List[MemoryMap]] = []

    CSS = """
    Screen {
        layout: vertical;
    }

    #main_container {
        height: 1fr;
    }

    #left_pane {
        width: 30%;
        height: 100%;
        border-right: solid $primary;
    }

    #right_pane {
        width: 70%;
        height: 100%;
        padding: 1;
    }

    #outline_tree {
        height: 1fr;
    }

    .section_title {
        background: $accent;
        color: $text;
        padding: 0 1;
        text-align: center;
        text-style: bold;
    }

    #properties_grid {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 3fr;
        height: auto;
        margin-bottom: 1;
    }

    #bit_table {
        height: 1fr;
        border: solid $secondary;
    }

    #mode_indicator {
        height: 1;
        background: $success;
        color: $text;
        text-align: center;
        text-style: bold;
    }

    #mode_indicator.insert {
        background: $primary;
    }

    #visualizer {
        height: 3;
        border: solid $success;
        margin-top: 1;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+h", "focus_left", "Focus Outline"),
        Binding("ctrl+b", "focus_left", "Focus Outline", show=False),  # Alternative for ctrl+h
        Binding("ctrl+l", "focus_right", "Focus Detail"),
        Binding("i", "enter_insert_mode", "Insert Mode", show=False),
        Binding("escape", "enter_normal_mode", "Normal Mode", show=False),
        Binding("j", "nav_down", "Down", show=False),
        Binding("k", "nav_up", "Up", show=False),
        Binding("h", "nav_left", "Left", show=False),
        Binding("l", "nav_right", "Right", show=False),
        Binding("enter", "edit_field", "Edit Field", show=False),
        Binding("e", "edit_field", "Edit Field", show=False),
        Binding("o", "add_field_after", "Add After", show=False),
        Binding("shift+o", "add_field_before", "Add Before", show=False),
        Binding("d", "delete_field", "Delete", show=False),
        Binding("shift+j", "move_field_down", "Move Down", show=False),
        Binding("shift+k", "move_field_up", "Move Up", show=False),
        Binding("ctrl+z", "undo", "Undo"),
        Binding("u", "undo", "Undo", show=False),
        Binding("ctrl+y", "redo", "Redo"),
        Binding("ctrl+r", "redo", "Redo", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        with Horizontal(id="main_container"):
            # Left Pane: Outline
            with Vertical(id="left_pane"):
                yield Label("Memory Map", classes="section_title")
                yield Tree("Root", id="outline_tree")

            # Right Pane: Detail Editor
            with VerticalScroll(id="right_pane"):
                yield Label("Register Properties", classes="section_title")

                # Properties Form (Grid)
                with Vertical(id="properties_grid"):
                    yield Label("Name:")
                    yield Input(placeholder="Register Name", id="prop_name")
                    yield Label("Offset:")
                    yield Input(placeholder="0x0000", id="prop_offset")
                    yield Label("Description:")
                    yield Input(placeholder="Description...", id="prop_desc")

                yield Label("Bit Fields", classes="section_title")
                yield Label("-- NORMAL --", id="mode_indicator")
                yield DataTable(id="bit_table", cursor_type="row")

                yield Label("Visualization", classes="section_title")
                yield Static("[Bit Visualizer Placeholder]", id="visualizer")

        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "Memory Map Editor (TUI)"

        # Load memory map if file path provided
        if self.file_path:
            self.load_memory_map(self.file_path)
        else:
            # Show empty state
            self._populate_empty_tree()

        # Setup table columns
        table = self.query_one("#bit_table", DataTable)
        table.add_columns("Name", "Bits", "Access", "Reset", "Description")
        table.cursor_type = "row"
        self._update_mode_indicator()

    def load_memory_map(self, file_path: Path) -> None:
        """Load memory map from YAML file."""
        try:
            parser = YamlIpCoreParser()

            # Check if it's a .memmap.yml or a full IP core file
            if file_path.suffix == ".yml" and ".memmap" in file_path.name:
                # Direct memory map file
                self.memory_maps = parser._load_memory_maps_from_file(file_path)
            else:
                # Full IP core file
                ip_core = parser.parse_file(file_path)
                self.memory_maps = ip_core.memory_maps

            self.title = f"Memory Map Editor - {file_path.name}"
            self._populate_tree()

        except Exception as e:
            self.notify(f"Error loading file: {e}", severity="error", timeout=5)
            self._populate_empty_tree()

    def _populate_empty_tree(self) -> None:
        """Populate tree with empty/demo data."""
        tree = self.query_one("#outline_tree", Tree)
        root = tree.root
        root.remove_children()
        root.label = "No Memory Map Loaded"
        root.expand()

    def _populate_tree(self) -> None:
        """Populate tree from loaded memory maps."""
        tree = self.query_one("#outline_tree", Tree)
        root = tree.root
        root.remove_children()
        root.label = "Memory Maps"
        root.expand()

        for mem_map in self.memory_maps:
            map_node = root.add(f"📋 {mem_map.name}", expand=True)
            map_node.data = {"type": "memmap", "object": mem_map}

            for block in mem_map.address_blocks:
                block_label = f"📦 {block.name} @ 0x{block.base_address:04X}"
                block_node = map_node.add(block_label, expand=True)
                block_node.data = {"type": "block", "object": block}

                for register in block.registers:
                    reg_label = f"📄 {register.name} @ +0x{register.address_offset:04X}"
                    reg_node = block_node.add_leaf(reg_label)
                    reg_node.data = {"type": "register", "object": register}

    def action_focus_left(self) -> None:
        """Focus the outline tree."""
        self.query_one("#outline_tree", Tree).focus()
        # self.notify("Focused Outline", timeout=1)

    def action_focus_right(self) -> None:
        """Focus the bit field table."""
        self.query_one("#bit_table").focus()
        # self.notify("Focused Detail", timeout=1)

    def action_enter_insert_mode(self) -> None:
        """Enter INSERT mode for table editing."""
        table = self.query_one("#bit_table", DataTable)
        if table.has_focus and self.table_mode == "NORMAL":
            self.table_mode = "INSERT"
            self._update_mode_indicator()
            # In INSERT mode, allow cell editing
            self.notify("-- INSERT --", severity="information", timeout=1)

    def action_enter_normal_mode(self) -> None:
        """Enter NORMAL mode for table navigation."""
        if self.table_mode == "INSERT":
            self.table_mode = "NORMAL"
            self._update_mode_indicator()
            self.notify("-- NORMAL --", severity="information", timeout=1)

    def action_nav_down(self) -> None:
        """Move cursor down (vim j)."""
        tree = self.query_one("#outline_tree", Tree)
        table = self.query_one("#bit_table", DataTable)

        if tree.has_focus:
            tree.action_cursor_down()
        elif table.has_focus and self.table_mode == "NORMAL" and table.row_count > 0:
            table.action_cursor_down()

    def action_nav_up(self) -> None:
        """Move cursor up (vim k)."""
        tree = self.query_one("#outline_tree", Tree)
        table = self.query_one("#bit_table", DataTable)

        if tree.has_focus:
            tree.action_cursor_up()
        elif table.has_focus and self.table_mode == "NORMAL" and table.row_count > 0:
            table.action_cursor_up()

    def action_nav_left(self) -> None:
        """Collapse tree or move table cursor left (vim h)."""
        tree = self.query_one("#outline_tree", Tree)
        table = self.query_one("#bit_table", DataTable)

        if tree.has_focus:
            # Collapse current node
            if tree.cursor_node and tree.cursor_node.is_expanded:
                tree.cursor_node.collapse()
        elif table.has_focus and self.table_mode == "NORMAL":
            table.action_cursor_left()

    def action_nav_right(self) -> None:
        """Expand tree or move table cursor right (vim l)."""
        tree = self.query_one("#outline_tree", Tree)
        table = self.query_one("#bit_table", DataTable)

        if tree.has_focus:
            # Expand current node
            if tree.cursor_node and not tree.cursor_node.is_expanded:
                tree.cursor_node.expand()
        elif table.has_focus and self.table_mode == "NORMAL":
            table.action_cursor_right()

    def _shift_fields(self, start_index: int, delta: int) -> None:
        """Shift fields starting from start_index by delta."""
        if delta == 0 or not self.current_register:
            return

        # Validate first
        for i in range(start_index, len(self.current_register.fields)):
            f = self.current_register.fields[i]
            if f.bit_offset + f.bit_width + delta > 32:
                raise ValueError(f"Shifting field '{f.name}' would exceed 32-bit boundary")

        # Apply shift
        for i in range(start_index, len(self.current_register.fields)):
            f = self.current_register.fields[i]
            f.bit_offset += delta

    def action_edit_field(self) -> None:
        """Edit the currently selected field."""
        table = self.query_one("#bit_table", DataTable)
        if not table.has_focus or not self.current_register:
            return

        row_index = table.cursor_row
        if row_index < 0 or row_index >= len(self.current_register.fields):
            return

        field = self.current_register.fields[row_index]
        old_width = field.bit_width

        # Snapshot before editing
        self.create_snapshot()

        def on_save(name, offset, width, access, reset, desc):
            # 1. Validate the field itself
            if offset + width > 32:
                raise ValueError(f"Field '{name}' extends beyond 32-bit boundary (offset {offset} + width {width} > 32)")

            # 2. Check for width change and shift subsequent fields
            delta = width - old_width
            if delta != 0:
                # Re-find index as sorting might have changed things (though unlikely during edit)
                try:
                    idx = self.current_register.fields.index(field)
                    # This will raise ValueError if shifting is not possible
                    self._shift_fields(idx + 1, delta)
                except ValueError as e:
                    raise ValueError(f"Cannot resize field: {e}")

            # 3. Apply changes if validation passed
            field.name = name
            field.bit_offset = offset
            field.bit_width = width
            field.access = AccessType(access)
            field.reset_value = reset
            field.description = desc

            self._load_register_details(self.current_register)
            self.notify(f"Updated field '{field.name}'")

        self.push_screen(EditFieldScreen(field, on_save))

    def action_add_field_after(self) -> None:
        """Add a new field after the current selection."""
        self._add_field(offset_delta=1)

    def action_add_field_before(self) -> None:
        """Add a new field before the current selection."""
        self._add_field(offset_delta=0)

    def _add_field(self, offset_delta: int) -> None:
        if not self.current_register:
            return

        # Snapshot for Undo
        self.create_snapshot()

        # Backup for rollback on error
        original_fields = copy.deepcopy(self.current_register.fields)

        table = self.query_one("#bit_table", DataTable)
        row_index = table.cursor_row

        try:
            # Calculate new field position
            if row_index < 0:
                insert_idx = len(self.current_register.fields)
            else:
                insert_idx = row_index + offset_delta

            # Calculate smart offset
            new_offset = 0
            if insert_idx > 0:
                prev_field = self.current_register.fields[insert_idx - 1]
                new_offset = prev_field.bit_offset + prev_field.bit_width

            # Clamp to 31 if it exceeds 32-bit boundary (to avoid validation error)
            if new_offset > 31:
                # If we are at the boundary, we can't insert unless we are shifting nothing?
                # But we are inserting width 1.
                # If new_offset is 32, we can't insert.
                # If new_offset is 31, width 1 -> 32. OK.
                # If new_offset > 31, we can't insert.
                raise ValueError("No space to insert new field at end of register")

            # Create default field
            new_field = BitField(
                name=f"FIELD_{len(self.current_register.fields)}",
                bit_offset=new_offset,
                bit_width=1,
                access=AccessType.READ_WRITE,
                description="New field"
            )

            # Check if new field fits
            if new_field.bit_offset + new_field.bit_width > 32:
                 raise ValueError("New field exceeds 32-bit boundary")

            # Check if shifting is possible BEFORE inserting
            # We need to check if fields from insert_idx onwards can be shifted
            # We can use _shift_fields validation logic, but we need to do it on the *current* fields
            # before inserting the new one.

            # Check if the last field (if any exist after insert_idx) would go out of bounds
            if insert_idx < len(self.current_register.fields):
                # We are inserting at insert_idx. The field currently at insert_idx will move to insert_idx+1
                # All fields from insert_idx to end will be shifted by new_field.bit_width

                # Find the maximum extent
                max_extent = 0
                for i in range(insert_idx, len(self.current_register.fields)):
                    f = self.current_register.fields[i]
                    if f.bit_offset + f.bit_width > max_extent:
                        max_extent = f.bit_offset + f.bit_width

                if max_extent + new_field.bit_width > 32:
                     raise ValueError("Inserting field would push existing fields beyond 32-bit boundary")

            self.current_register.fields.insert(insert_idx, new_field)

            # Shift subsequent fields to make room
            self._shift_fields(insert_idx + 1, new_field.bit_width)

            self._load_register_details(self.current_register)

            # Focus the new row
            table.move_cursor(row=insert_idx)

            # Immediately open edit
            self.action_edit_field()

        except ValueError as e:
            # Restore state
            self.current_register.fields = original_fields
            # Remove the undo snapshot we just made
            if self.undo_stack:
                self.undo_stack.pop()

            self.notify(f"Cannot insert field: {e}", severity="error")
            self._load_register_details(self.current_register)

    def action_delete_field(self) -> None:
        """Delete the selected field."""
        if not self.current_register:
            return

        table = self.query_one("#bit_table", DataTable)
        row_index = table.cursor_row
        if row_index < 0 or row_index >= len(self.current_register.fields):
            return

        # Snapshot before deleting
        self.create_snapshot()

        # Get the field to be deleted
        field_to_delete = self.current_register.fields[row_index]
        width = field_to_delete.bit_width

        # Delete the field
        del self.current_register.fields[row_index]

        # Shift subsequent fields down to fill the gap
        # We need to shift fields starting from the deleted index (which is now occupied by the next field)
        # by -width
        try:
            self._shift_fields(row_index, -width)
        except ValueError:
            # Should not happen when shifting down (negative delta), but good to be safe
            pass

        self._load_register_details(self.current_register)
        self.notify("Field deleted")

    def action_move_field_up(self) -> None:
        """Move selected field up."""
        self._move_field(-1)

    def action_move_field_down(self) -> None:
        """Move selected field down."""
        self._move_field(1)

    def _move_field(self, delta: int) -> None:
        if not self.current_register:
            return

        self.create_snapshot()

        table = self.query_one("#bit_table", DataTable)
        row_index = table.cursor_row
        new_index = row_index + delta

        if 0 <= new_index < len(self.current_register.fields):
            fields = self.current_register.fields
            fields[row_index], fields[new_index] = fields[new_index], fields[row_index]
            self._load_register_details(self.current_register)
            table.move_cursor(row=new_index)

    def _update_mode_indicator(self) -> None:
        """Update the mode indicator label."""
        indicator = self.query_one("#mode_indicator", Label)
        if self.table_mode == "NORMAL":
            indicator.update("-- NORMAL --")
            indicator.remove_class("insert")
        else:
            indicator.update("-- INSERT --")
            indicator.add_class("insert")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection."""
        node = event.node
        if not node.data:
            return

        node_type = node.data.get("type")
        obj = node.data.get("object")

        if node_type == "register" and isinstance(obj, Register):
            self.current_register = obj
            self._load_register_details(obj)

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Handle tree node highlighting (navigation)."""
        node = event.node
        if not node.data:
            return

        node_type = node.data.get("type")
        obj = node.data.get("object")

        if node_type == "register" and isinstance(obj, Register):
            self.current_register = obj
            self._load_register_details(obj)

    def _load_register_details(self, register: Register) -> None:
        """Load register details into the right pane."""
        # Sort fields by offset to ensure visual order matches logical order
        register.fields.sort(key=lambda f: f.bit_offset)

        # Update property inputs
        self.query_one("#prop_name", Input).value = register.name
        self.query_one("#prop_offset", Input).value = f"0x{register.address_offset:04X}"
        self.query_one("#prop_desc", Input).value = register.description or ""

        # Update bit fields table
        table = self.query_one("#bit_table", DataTable)
        table.clear()

        for field in register.fields:
            table.add_row(
                field.name,
                field.bit_range,
                field.access.value,
                f"0x{field.reset_value or 0:X}",
                field.description or ""
            )

        # Update visualizer
        self._update_visualizer(register)

    def _update_visualizer(self, register: Register) -> None:
        """Update the bit visualizer for the current register."""
        from rich.text import Text

        # Create a 32-bit representation
        bits = ["·"] * 32  # Empty bits
        colors = ["dim white"] * 32

        for field in register.fields:
            for bit_pos in range(field.bit_offset, field.bit_offset + field.bit_width):
                if bit_pos < 32:
                    # Check if reset value has this bit set
                    if field.reset_value and (field.reset_value >> (bit_pos - field.bit_offset)) & 1:
                        bits[31 - bit_pos] = "1"
                        colors[31 - bit_pos] = "green"
                    else:
                        bits[31 - bit_pos] = "0"
                        colors[31 - bit_pos] = "white"

        # Build rich text with colors
        viz_text = Text()
        for i, (bit, color) in enumerate(zip(bits, colors)):
            viz_text.append(bit, style=color)
            if (31 - i) % 8 == 0 and i < 31:  # Add space every 8 bits
                viz_text.append(" ", style="dim white")

        visualizer = self.query_one("#visualizer", Static)
        visualizer.update(viz_text)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for property fields."""
        if not self.current_register:
            return

        input_id = event.input.id
        value = event.value

        try:
            if input_id == "prop_name":
                self.current_register.name = value
            elif input_id == "prop_offset":
                # Parse hex offset
                if value.startswith("0x"):
                    self.current_register.address_offset = int(value, 16)
            elif input_id == "prop_desc":
                self.current_register.description = value
        except ValueError:
            # Invalid input, could show error
            pass

    def create_snapshot(self) -> None:
        """Save current state to undo stack."""
        self.undo_stack.append(copy.deepcopy(self.memory_maps))
        self.redo_stack.clear()
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def action_undo(self) -> None:
        """Undo last action."""
        if not self.undo_stack:
            self.notify("Nothing to undo", severity="warning")
            return

        # Save current state to redo
        self.redo_stack.append(copy.deepcopy(self.memory_maps))

        # Restore
        self._restore_state(self.undo_stack.pop())
        self.notify("Undone")

    def action_redo(self) -> None:
        """Redo last undone action."""
        if not self.redo_stack:
            self.notify("Nothing to redo", severity="warning")
            return

        # Save current to undo
        self.undo_stack.append(copy.deepcopy(self.memory_maps))

        # Restore
        self._restore_state(self.redo_stack.pop())
        self.notify("Redone")

    def _restore_state(self, new_maps: List[MemoryMap]) -> None:
        # 1. Capture current selection path
        path = self._get_current_register_path()

        # 2. Update model
        self.memory_maps = new_maps

        # 3. Refresh Tree
        self._populate_tree()

        # 4. Restore selection
        if path:
            reg = self._find_register_by_path(path)
            if reg:
                self.current_register = reg
                self._load_register_details(reg)
            else:
                self.current_register = None

    def _get_current_register_path(self) -> Optional[tuple]:
        if not self.current_register:
            return None
        for mm_idx, mm in enumerate(self.memory_maps):
            for blk_idx, block in enumerate(mm.address_blocks):
                for reg_idx, reg in enumerate(block.registers):
                    if reg is self.current_register:
                        return (mm_idx, blk_idx, reg_idx)
        return None

    def _find_register_by_path(self, path: tuple) -> Optional[Register]:
        try:
            mm_idx, blk_idx, reg_idx = path
            return self.memory_maps[mm_idx].address_blocks[blk_idx].registers[reg_idx]
        except (IndexError, AttributeError):
            return None

    def action_save(self) -> None:
        """Save the memory map back to YAML."""
        if not self.file_path:
            self.notify("No file loaded", severity="warning")
            return

        try:
            # Serialize manually to match the expected YAML format
            data = [self._serialize_memory_map(m) for m in self.memory_maps]

            # If we only have one memory map and the file expects a single object (not list)
            # This is a heuristic. The parser handles both.
            # For now, dumping as list is safer if we have multiple.
            if len(data) == 1 and ".memmap" in self.file_path.name:
                 # Some formats might prefer the single object if it's a memmap file
                 # But let's stick to list for consistency with parser return type unless we know better.
                 pass

            with open(self.file_path, 'w') as f:
                yaml.dump(data, f, sort_keys=False)

            self.notify(f"Saved to {self.file_path.name}", severity="information")
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error")

    def _serialize_memory_map(self, mem_map: MemoryMap) -> dict:
        return {
            "name": mem_map.name,
            "description": mem_map.description,
            "addressBlocks": [self._serialize_address_block(b) for b in mem_map.address_blocks]
        }

    def _serialize_address_block(self, block: AddressBlock) -> dict:
        data = {
            "name": block.name,
            "offset": block.base_address,
            "usage": block.usage.value,
            "description": block.description,
            "registers": [self._serialize_register(r) for r in block.registers]
        }
        # Filter empty/None
        return {k: v for k, v in data.items() if v is not None and v != ""}

    def _serialize_register(self, register: Register) -> dict:
        data = {
            "name": register.name,
            "offset": register.address_offset,
            "description": register.description,
            "access": register.access.value if register.access != AccessType.READ_WRITE else None,
        }

        if register.fields:
            data["fields"] = [self._serialize_field(f) for f in register.fields]

        return {k: v for k, v in data.items() if v is not None and v != ""}

    def _serialize_field(self, field: BitField) -> dict:
        data = {
            "name": field.name,
            "description": field.description,
            "access": field.access.value if field.access != AccessType.READ_WRITE else None,
        }

        # Construct bits string
        msb = field.bit_offset + field.bit_width - 1
        lsb = field.bit_offset
        data["bits"] = f"[{msb}:{lsb}]"

        if field.reset_value is not None:
             data["reset"] = field.reset_value

        return {k: v for k, v in data.items() if v is not None and v != ""}


if __name__ == "__main__":
    # Parse command line arguments
    file_path = None
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

    app = MemoryMapEditorApp(file_path=file_path)
    app.run()
