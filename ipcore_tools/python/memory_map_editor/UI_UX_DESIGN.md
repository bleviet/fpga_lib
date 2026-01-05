# Memory Map Editor UI/UX Design Documentation (Qt / PySide6)

This document describes the current UI/UX design of the Memory Map Editor located in `examples/gui/memory_map_editor/`. It is intended as a reference for maintainers and as a parity target for future ports (e.g., a VS Code extension).

## 1. UX Goals and Design Principles

### 1.1 Goals
- Make memory map editing **guided and visual**, reducing YAML syntax/semantic mistakes.
- Provide **fast keyboard-centric workflows** for common operations (insert/remove/reorder).
- Provide **immediate feedback** on mistakes (overlaps, gaps, invalid values).
- Keep the editor usable for both:
  - structured specification authoring (names, offsets, bit ranges, resets)
  - debug/bring-up workflows (live values compared to reset defaults)

### 1.2 Principles
- **Master–detail layout**: outline on the left, editor on the right.
- **Progressive disclosure**: show details only for the selected item.
- **Prevent invalid states when possible**: validate edits and highlight conflicts.
- **Keyboard-first usability**: vim-like navigation and modal editing in tables.
- **Visual diagnostics**: use color and layout to show overlaps/gaps and reset/live differences.

## 2. Information Architecture

The application is organized around the `MemoryMapProject` model:
- Project metadata: name, description, base address
- Items:
  - Registers
  - Register arrays

In the UI, these appear as selectable nodes in an outline tree, with details shown in a dedicated editor panel.

## 3. Main Window Layout

The primary UI container is `MainWindow` in `gui/main_window.py`.

### 3.1 Window Structure
- **Menu bar**
- **Toolbar** (quick access)
- **Status bar** (project, validation, zoom)
- **Central area**: horizontal splitter with two panes

```
+--------------------------------------------------------------+
| Menu Bar                                                     |
+--------------------------------------------------------------+
| Toolbar (New/Open/Save/Validate/Zoom)                         |
+---------------------------+----------------------------------+
| Memory Map Outline        | Register Detail Form              |
| (tree + quick actions)    |  - Bit Fields table (left)        |
|                           |  - Properties (right/top)         |
|                           |  - Bit visualizer (right/bottom)  |
+---------------------------+----------------------------------+
| Status Bar (Project | Validation | Zoom)                      |
+--------------------------------------------------------------+
```

### 3.2 Splitter Behavior
- The main splitter divides **Outline (left)** and **Detail (right)**.
- Outline has min/max widths (so it stays usable).

### 3.3 Focus and Keyboard Usability
The app explicitly supports panel focus and keyboard navigation:
- On show, focus is placed on the outline tree (for “vim-style navigation”).
- `Ctrl+H` focuses the left (outline) panel.
- `Ctrl+L` focuses the right (bit field table) panel.
- The focused panel receives a **blue focus border** (visual focus indicator).

## 4. Menus and Global Commands

Implemented in `MainWindow._setup_menu_bar()`.

### 4.1 File Menu
- New (`Ctrl+N`)
- Open (`Ctrl+O`)
- Save (`Ctrl+S`)
- Save As (`Ctrl+Shift+S`)
- Exit (`Ctrl+Q`)

### 4.2 Edit Menu
- Validate Memory Map (`Ctrl+R`)
  - Runs conflict checks and surfaces errors to the user.

### 4.3 View Menu
- Refresh (`F5`)
- Zoom In / Zoom Out (standard Qt zoom shortcuts)
- Reset Zoom (`Ctrl+0`)
- Display Settings…
  - Provides text size and UI scaling controls (scaling requires restart to fully apply).

### 4.4 Help Menu
- Keyboard Shortcuts (`F1`)
- About

## 5. Status Bar Feedback

The status bar is used for lightweight feedback:
- Project information (“Ready”, current state)
- Validation indicator (errors/warnings)
- Zoom level (“Zoom: 100%”, etc.)

Additionally, panel focus updates are reflected temporarily in the status bar (e.g., “Focus: Memory Map Outline”).

## 6. Left Pane: Memory Map Outline (Tree)

Implemented in `gui/memory_map_outline.py`.

### 6.1 Purpose
- Primary navigation for registers and arrays.
- Fast structural edits (insert/remove/move items).

### 6.2 Visual Design
- Header: “Memory Map” title + action buttons.
- Tree widget with columns:
  - **Name**
  - **Address**
  - **Type**
- Alternating row colors to improve scanability.
- Arrays are expandable/collapsible.

### 6.3 Outline Actions (Header Buttons)
- Expand all arrays / Collapse all arrays
- Insert register before / after selection
- Insert array before / after selection
- Remove selected register/array
- Move selected item up / down

### 6.4 Keyboard Shortcuts (Outline)
The outline supports a vim-inspired workflow:
- Insert register after: `o`
- Insert register before: `Shift+O`
- Insert array after: `a`
- Insert array before: `Shift+A`
- Delete selected item: `d,d`
- Move item up/down: `Alt+Up` / `Alt+Down` (also `Alt+k` / `Alt+j`)
- Navigate within tree:
  - `j` / `k` for down/up
  - `h` collapse
  - `l` expand

### 6.5 Selection → Detail Binding
- Selecting a tree item emits `current_item_changed`, driving the right-hand detail panel.

## 7. Right Pane: Register Detail Form (Coordinator)

Implemented in `gui/register_detail_form.py`.

### 7.1 Composition
The detail form composes three sub-components:
- **BitFieldTableWidget** (left within the right pane)
- **RegisterPropertiesWidget** (right/top)
- **BitFieldVisualizer** (right/bottom)

It is effectively a mediator:
- property edits trigger refreshes in the table and visualizer
- field edits trigger recalculation of register reset values

### 7.2 Enabled / Disabled State
- With no selection: controls are disabled and the visualizer shows an empty state message.
- With a register selected: all controls enabled.

## 8. Register Properties Widget

Implemented in `gui/register_properties_widget.py`.

### 8.1 Purpose
- Edit top-level properties of a register or a register array.
- Show computed reset value.
- Support live debug value entry.

### 8.2 Fields
**For registers**:
- Name (text)
- Address/Offset (hex spinbox, `0x` prefix)
- Description (multi-line; committed on focus loss)
- Reset Value (read-only; computed from bit field resets)
- Live Value (editable; parsed from hex/bin/dec)

**For arrays**:
- Name
- Base address
- Count
- Stride
- Reset value shown as “N/A (Array)”

### 8.3 Reset Value UX
- Reset is not edited at the register level.
- Reset is derived from fields, displayed as `0x????????` and updated live.

### 8.4 Live Value UX (Debug)
- When a register is selected, the UI ensures a default live value exists:
  - if no live value exists, it initializes live = reset
  - it also initializes per-field live values for consistency
- Editing the live register value:
  - updates the current debug set’s register value
  - propagates to per-field live values
  - invalid inputs are rejected with a warning dialog

## 9. Bit Field Table Widget

Implemented in `gui/bit_field_table_widget.py`.

### 9.1 Purpose
- Primary structured editing surface for bit fields.
- Provides both mouse/UI controls and a keyboard/vim-inspired workflow.

### 9.2 Table Columns
The table uses 7 columns:
- Name
- Bits
- Width
- Access (dropdown delegate)
- Reset Value
- Live Value
- Description

### 9.3 Field Toolbar (Top Row)
- Add field (`+`)
- Insert before (`⬆`, shortcut `Shift+O`)
- Insert after (`⬇`, shortcut `o`)
- Remove (`trash`, shortcut `d,d`)
- Move up (`△`, shortcut `Alt+Up` / `Alt+k`)
- Move down (`▽`, shortcut `Alt+Down` / `Alt+j`)
- Recalculate offsets / Pack sequentially (`⚡`)

### 9.4 Modal Editing (Vim-like “Normal/Insert”)
The table has an explicit mode concept:
- **Normal mode**: navigation and structure edits; cell editing disabled.
- **Insert mode**: enables cell editing.

Mode switching:
- Enter insert mode: `i`
- Return to normal mode: `Esc` or `Ctrl+[`

The current mode is displayed in a prominent label:
- “-- NORMAL --” (green)
- “-- INSERT --” (blue)

### 9.5 Keyboard Navigation (Normal Mode)
- `j` / `k` move row selection
- `h` / `l` move column selection

### 9.6 Validation and Visual Highlighting
The table provides immediate visual diagnostics:
- **Overlaps**: entire row highlighted light red.
- **Gaps**: rows with gaps from previous field highlighted light yellow.
- **Live differs from reset**: live value cells highlighted light green.

Additionally, field insert/add operations validate that the new field fits within the 32-bit space.

### 9.7 Arrays and Templates
When editing a register array element, the table can propagate template changes:
- Adding a field also updates the array’s `_field_template`.
- Emits `array_template_changed` so the rest of the UI can refresh the outline.

## 10. Bit Field Visualizer

Implemented in `gui/bit_field_visualizer.py`.

### 10.1 Purpose
Provide a spatial visualization of a register’s layout:
- 32-bit bar (bit 31 on the left → bit 0 on the right)
- Color-coded regions per field
- Error highlighting (overlaps)

### 10.2 Visual Encoding
- Background is a light gray.
- Fields get palette colors (cycled).
- Unused bits are near-white.
- Overlaps are colored red.

### 10.3 Reset Visualization
- Each bit cell shows the reset bit (0/1) for that position.
- Reset “1” is drawn with green text; reset “0” uses gray text.

### 10.4 Debug Mode: Reset vs Live
Debug mode expands visualization into two rows:
- Top row: reset bits
- Bottom row: live bits

The visualizer compares live vs reset:
- if a debug set has a live value for the register, it uses that
- otherwise it mirrors reset bits as a baseline (so live doesn’t misleadingly show zeros)

### 10.5 Direct Manipulation of Live Bits
In debug mode, the live row supports click-and-drag bit toggling:
- Click a live bit: toggles that bit (0→1 or 1→0)
- Drag across bits: sets each crossed bit to the same target value
- On mouse release: the visualizer notifies parent widgets to refresh the live displays

This makes it possible to quickly model “what-if” scenarios for register state and see differences.

### 10.6 Legend and Scrollability
- The visualizer is wrapped in a scroll area.
- A legend explains the meaning of colors (Field / Unused / Overlap).
- The header shows context text such as:
  - “Register: NAME (N fields)”
  - “Array: NAME (N fields per entry)”

## 11. Validation UX

There are two layers of validation experience:

1) **Local visual validation**
- Table row highlighting for overlaps/gaps.
- Visualizer red overlap cells.

2) **Project-level validation**
- Run via “Validate Memory Map” (`Ctrl+R`).
- Uses model-level checks (e.g., address overlaps and field bounds).

## 12. Accessibility and Usability Considerations

### 12.1 Text Size and Scaling
- Zoom in/out/reset affects application font size.
- Display Settings dialog offers:
  - font size adjustment
  - UI scale factor (requires restart)

### 12.2 Error Prevention
- Default values are chosen to keep new entities valid:
  - new fields default to 1-bit RW with reset 0
  - insert logic shifts subsequent fields to keep the map contiguous

### 12.3 Discoverability
- Most buttons include tooltips with their keyboard shortcuts.
- Help menu provides a “Keyboard Shortcuts” entry.

## 13. Notes for VS Code Port (Parity Targets)

If porting this to a VS Code extension, the parity-critical UX elements are:
- Master–detail split layout (outline + detail editor)
- Quick insert/remove/move actions on both outline items and fields
- Vim-like workflows (optional but central to current UX)
- Clear overlap/gap visualization
- Reset values + computed register reset value
- Debug view (live vs reset) including fast toggling of bits
