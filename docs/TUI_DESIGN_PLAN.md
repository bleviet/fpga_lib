# Memory Map Editor TUI Design Plan

This document outlines the design for a **Terminal User Interface (TUI)** version of the Memory Map Editor, based on the existing [UI/UX Design](examples/gui/memory_map_editor/UI_UX_DESIGN.md).

## 1. Technology Stack

- **Language**: Python 3.x
- **Framework**: **[Textual](https://textual.textualize.io/)**
  - *Why?* Textual provides modern CSS-based layout, robust widget support (Tree, DataTable), and excellent keyboard handling, which fits the "vim-like" requirement perfectly.
- **Data Model**: Reuse existing `fpga_lib.model` (Pydantic models).
- **Persistence**: Reuse `fpga_lib.parser.yaml` (YAML loading/saving).

## 2. Architecture

The application will follow a Model-View-Controller (MVC) pattern, adapted for Textual's event-driven architecture.

```
fpga_lib/
  tui/
    __init__.py
    app.py              # Main App class
    screens/
      main_screen.py    # The primary editor screen
      help_screen.py    # Keyboard shortcuts help
    widgets/
      outline.py        # Tree widget for memory map
      register_form.py  # Right pane container
      bit_table.py      # DataTable for bit fields
      visualizer.py     # Custom widget for 32-bit visualization
    controllers/        # Optional: logic to bridge UI events to Model updates
```

## 3. UI Layout Mapping

We will map the Qt layout to Textual containers.

| Qt Component | Textual Equivalent | Notes |
|---|---|---|
| **MainWindow** | `App` / `Screen` | The root container. |
| **Menu Bar** | `Header` | Textual's Header shows the title and clock; menus can be simulated or triggered via command palette. |
| **Status Bar** | `Footer` | Shows key bindings and status messages. |
| **Splitter** | `Horizontal` container | Holds the Outline and Detail pane. |
| **Outline (Left)** | `Tree` widget | Native support for hierarchy and expansion. |
| **Detail (Right)** | `VerticalScroll` | Container for the form elements. |

### 3.1 Detailed Layout Structure

```
Screen
├── Header
├── Horizontal (Main Split)
│   ├── Vertical (Left Pane - CSS: width: 30%)
│   │   ├── Label ("Memory Map")
│   │   └── Tree (id="outline_tree")
│   └── Vertical (Right Pane - CSS: width: 70%)
│       ├── RegisterProperties (Grid layout)
│       │   ├── Input (Name)
│       │   ├── Input (Offset)
│       │   └── Input (Description)
│       ├── Label ("Bit Fields")
│       ├── DataTable (id="bit_table")
│       └── BitVisualizer (id="visualizer")
└── Footer
```

## 4. Component Design

### 4.1 Memory Map Outline (`Tree`)
- **Data**: Populated from `MemoryMap.address_blocks` and `registers`.
- **Interaction**:
  - `CursorMove`: Updates the "Current Selection".
  - `Enter`: Expands/Collapses nodes.
  - **Shortcuts**:
    - `j`/`k`: Navigate up/down.
    - `d,d`: Delete node.
    - `a`/`A`: Add array.
    - `o`/`O`: Add register.

### 4.2 Register Properties
- **Widgets**: `Input` widgets for Name, Offset, Description.
- **Behavior**:
  - Changes update the underlying Pydantic model immediately (or on blur).
  - "Live Value" input for debug mode.

### 4.3 Bit Field Table (`DataTable`)
- **Columns**: Name, Bits, Access, Reset, Description.
- **Editing**:
  - Table uses **cell cursor** navigation: `j/k/h/l` moves between cells.
  - **Inline edit** (simple cells): `Enter` / `F2` / `i` starts inline editing, `Enter` commits, `Esc` cancels.
  - **Full edit dialog** (advanced): `e` opens the bit-field dialog (offset/width/access/reset/desc).
- **Visuals**:
  - Use `Rich` text styling to highlight overlaps (red background) or gaps (yellow text).

### 4.4 Bit Visualizer (Custom Widget)
- **Rendering**: Use `Rich` segments to render a 32-character bar.
  - `[on red]1[/]` for overlaps.
  - `[on green]1[/]` for set bits.
  - `[on grey]0[/]` for cleared bits.
- **Interaction**:
  - Mouse click events can toggle bits (Textual supports mouse events).
  - Keyboard navigation (left/right arrows + space to toggle) for TUI purists.

## 5. Key Bindings & UX

The app will implement a **Mode Manager** to handle the Vim-like bindings.

| Context | Key | Action |
|---|---|---|
| **Global** | `Ctrl+q` | Quit |
| **Global** | `Ctrl+s` | Save |
| **Global** | `Ctrl+h` | Focus Outline |
| **Global** | `Ctrl+l` | Focus Detail Pane |
| **Outline** | `j`/`k` | Move selection |
| **Outline** | `o` | Insert Register After |
| **Table** | `i` | Enter Edit Mode (focus cell) |
| **Table** | `Esc` | Exit Edit Mode |

## 6. Implementation Plan

1.  **Scaffold**: Create `tui/app.py` and basic layout.
2.  **Model Loading**: Integrate `YamlIpCoreParser` to load a `.memmap.yml` file into the Tree.
3.  **Detail View**: Implement the right pane to show details for the selected Tree node.
4.  **Editing Logic**: Connect `Input` widgets to the Pydantic models.
5.  **Table Widget**: Implement the `DataTable` with add/remove row logic.
6.  **Visualizer**: Build the custom renderable for the bit bar.
7.  **Save**: Serialize the Pydantic models back to YAML.

## 7. Feasibility Notes

- **Bit Visualizer**: Textual is excellent at rendering colored blocks/text, so the visualizer will look very similar to the GUI version, just "blockier".
- **Modal Editing**: Textual's `push_screen` or widget switching makes modal editing straightforward.
- **Clipboard**: System clipboard integration is supported by Textual.

This design achieves near-parity with the Qt application while running entirely in the terminal.
