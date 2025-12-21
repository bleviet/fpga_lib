# VS Code Extension Wireframe + UI/UX Plan

This document drafts the intended **VS Code extension** UX for editing `*.memmap.yml` (and optionally full IP-core YAML files) using a **Custom Editor** with a VS Code-native look.

It is designed to align with the existing Qt GUI and Textual TUI workflows.

---

## 0) Product definition (V1)

### Primary job-to-be-done
Edit memory-map YAML safely (registers + arrays + bitfields) without fighting YAML syntax, while staying in VS Code.

### Non-goals (V1)
- Perfect preservation of YAML formatting/comments.
- HDL/C header generation from the extension.
- Managing multiple cores/projects from a single UI.

### File targets (recommended)
- V1: `*.memmap.yml` custom editor.
- V2: full `*.yml` IP-core files that contain memory maps.

---

## 1) Information architecture

### Entities
- Memory Map
- Address Block
- Register
- Register Array (if represented distinctly)
- Bit Field

### Views
- **Custom Editor (Visual)** — primary editing surface.
- **Text Editor (YAML)** — always available; must stay synchronized.

### Navigation model
- Master-detail.
- Selection in the Outline drives the right-pane editor.

---

## 2) Wireframe (ASCII)

### 2.1 Main editor layout (Custom Editor)

```
+-----------------------------------------------------------------------------------+
| Header row: [File name]  [Validate] [Save]                         [Problems: 0] |
+------------------------------+----------------------------------------------------+
| OUTLINE (30%)                | DETAILS (70%)                                      |
|------------------------------|----------------------------------------------------|
| Search: [______________]     | Breadcrumb: MemoryMap > Block > Register           |
|                              |----------------------------------------------------|
| Memory Maps                  | Tabs:  [Properties]  [Bit Fields]  [Preview]       |
|  ▸ map0                       |                                                    |
|    ▾ blockA @ 0x0000         |  Properties tab (context-sensitive)                |
|      ▸ reg_ctrl @ +0x0010    |  - Name         [ reg_ctrl____________ ]           |
|      ▸ reg_stat @ +0x0014    |  - Offset (hex) [ 0x0010___________ ]              |
|      ▸ reg_data[0..7]        |  - Desc         [____________________]             |
|                              |  - Access       [ RW v ]                            |
|------------------------------|----------------------------------------------------|
| Context actions              | Bit visualizer (register only)                     |
| - + Register                 |  31                                               0|
| - + Array                    |  [ fieldA ][ fieldB ][....free....][ fieldC ]      |
| - Delete                     |  Hover -> tooltip (name, range, access, reset)     |
+------------------------------+----------------------------------------------------+
| Status bar: key hints + validation summary                                        |
+-----------------------------------------------------------------------------------+
```

Notes:
- `Preview` tab is optional; if you want strict V1 parity, it can be omitted.
- The visualizer can live below the tabs or inside the Bit Fields tab.

### 2.2 Bit Fields tab (table + actions)

```
+----------------------------------------------------+
| Bit Fields                                         |
| [ + Add ] [ Insert Before ] [ Insert After ] [Del] |
| [ Move Up ] [ Move Down ]                          |
|----------------------------------------------------|
| Name        | Bits  | Access | Reset | Description  |
|-------------+-------+--------+-------+--------------|
| enable      | 0     | RW     | 0x0   | ...          |
| mode        | 2:1   | RW     | 0x1   | ...          |
| done        | 8     | RO     | 0x0   | ...          |
+----------------------------------------------------+
```

Inline editing:
- `Enter` / `F2` / `i` edits the current cell.
- `Esc` cancels.
- `e` opens the full edit dialog (advanced editing).

### 2.3 "Edit Bit Field" dialog (kept)

```
+-------------------- Edit Bit Field ---------------------+
| Name:        [ enable__________ ]                        |
| Bit Offset:  [ 0 ]     Bit Width: [ 1 ]                  |
| Access:      [ RW v ]                                    |
| Reset:       [ 0x0___________ ]                          |
| Description: [______________________________]            |
| [Cancel]                                   [Save]        |
+----------------------------------------------------------+
```

---

## 3) Interaction design

### 3.1 Keybindings (V1)

Global:
- `Ctrl+S` Save
- `Ctrl+Q` Quit/Close editor (optional)
- `Ctrl+H` Focus outline
- `Ctrl+L` Focus details

Outline:
- `j/k` move selection
- `Enter` expand/collapse

Bit field table:
- `h/j/k/l` move between cells
- `i`, `F2`, `Enter` start inline edit
- `Enter` commit inline edit
- `Esc` cancel inline edit
- `e` open Edit Bit Field dialog
- `o/O` insert after/before (optional)
- `d` delete (optional)

### 3.2 Mouse interactions
- Outline: click selects.
- Table: click cell selects; double-click starts inline edit.
- Visualizer: hover shows tooltip; click selects corresponding bitfield row.

### 3.3 Validation feedback
- Inline: invalid fields show red border + helper text.
- Diagnostics: report to VS Code Problems panel with file/line when possible.
- Visualizer: overlaps highlighted in red; gaps optionally styled.

---

## 4) Extension architecture (implementation plan)

### 4.1 Extension host (TypeScript)
- Contribute a `customEditors` entry for `*.memmap.yml`.
- Implement `CustomTextEditorProvider`.
- Parse YAML to a normalized in-memory model (JSON-like).
- Apply user actions to the model and write back to `TextDocument` via `WorkspaceEdit` so Undo/Redo works.

### 4.2 Webview UI (React + VS Code UI Toolkit)
- Use `@vscode/webview-ui-toolkit` components for theme-native inputs.
- State:
  - `documentModel`
  - `selection` (selected node id + type)
  - `uiState` (expanded tree nodes, table cursor, inline edit state)

### 4.3 Messaging contract
Host → Webview:
- `init`: `{ model, selection? }`
- `update`: `{ model, diagnostics }` (full refresh for V1)
- `diagnostics`: `{ diagnostics[] }`

Webview → Host:
- `select`: `{ nodeId }`
- `op`: `{ kind, payload }` (preferred)
  - `setRegisterProp`, `addField`, `deleteField`, `moveField`, `setFieldProp`, etc.

### 4.4 Model + validation strategy
- V1 validation in TypeScript:
  - YAML parse errors
  - bit range parsing
  - overlaps
  - reset width bounds
- Optional parity mode:
  - call Python validation (Pydantic) on save or on-demand Validate.

---

## 5) Delivery roadmap (practical)

### Milestone 1 — Skeleton
- Custom editor opens `.memmap.yml` and renders empty layout.
- Message passing works.

### Milestone 2 — Outline + selection
- Tree renders memory map / blocks / registers.
- Selecting updates details pane.

### Milestone 3 — Register properties + writeback
- Edit name/offset/desc and persists to YAML.
- Undo/Redo works.

### Milestone 4 — Bitfields table + dialog
- Table editing (add/insert/delete/move).
- Keep modal dialog for advanced edits.

### Milestone 5 — Visualizer + diagnostics
- Visualizer renders bit allocations.
- Overlaps flagged, Problems panel integration.

---

## 6) Open questions (to lock before coding)

1) Are memory maps always 32-bit registers, or variable width?
2) Should the extension own only `*.memmap.yml`, or also full `*.yml` IP-core files?
3) Do you want comment/format preservation, or is stable ordering sufficient?
