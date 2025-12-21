# VS Code Extension Development Plan (Detailed): FPGA Memory Map Visual Editor

This document is a detailed plan for building a Visual Studio Code extension that provides the same core workflows as the existing Qt-based Memory Map Editor, while aligning with the project’s Pydantic models.

## 1. Why (Vision, Motivation, Outcomes)

### 1.1 Motivation
Editing memory maps in YAML is efficient for version control, but it is also error-prone:
- YAML syntax errors (indentation, quoting) break tooling immediately.
- Semantic errors (bit overlaps, invalid ranges, address overlaps, invalid reset values) are easy to create and hard to spot in text.

The Qt editor already solves this with guided UI, a register outline tree, forms, a bit-field table, and a bit layout visualizer. The VS Code extension should bring those benefits to where engineers already work.

### 1.2 Business / Engineering Goals
- **Reduce integration bugs** caused by incorrect maps.
- **Improve developer throughput** by turning common edits into guided actions.
- **Keep a single source of truth**: the YAML remains the artifact; the UI is a safer interface to it.
- **Schema alignment** with `fpga_lib` Pydantic models to avoid divergence.

### 1.3 Definition of Done (V1)
V1 is “useful and safe”, not “perfect formatting”. Done means:
- Open/create/save `.memmap.yml` in a VS Code Custom Editor.
- Feature parity for the daily workflows:
  - project management (new/open/save)
  - outline navigation (registers + arrays)
  - register/array properties editing
  - bit-field table editing with add/insert/remove/move
  - bit layout visualizer
  - reset values + calculated register reset value
- Validation feedback is clear (inline + Problems panel) and prevents writing invalid states.
- Undo/redo works for core operations.

## 2. What (Scope and Feature Parity)

### 2.1 Personas
- **FPGA designer**: authors registers, bitfields, reset state.
- **Firmware developer**: consumes the map; cares about naming, offsets, access types, reset defaults.
- **Verification engineer**: uses reset values and stable layout to generate tests.

### 2.2 Feature Parity Matrix (Qt App → VS Code Extension)

The extension should explicitly implement these features from the current Qt editor:

**A) Project management**
- Create new memory map project (name, description, base address)
- Open existing YAML
- Save / Save As

**B) Navigation / Outline**
- Tree view of registers and register arrays
- Context menu on outline nodes (add/remove)
- Keyboard shortcuts for navigation and common actions

**C) Detail editor**
- Properties tab:
  - register: name, offset (hex), description, access mode
  - array: count, stride (and shared properties)
- Bit Fields tab:
  - table/grid editor for fields

**D) Bit field operations (from refactoring summary)**
- Add field at next available location
- Insert field before/after
- Remove field
- Reorder fields (Alt+Up/Down)
- Unique name generation
- Find available space and repack/recalculate offsets (where applicable)

**E) Visualization**
- Bit layout visualizer for selected register
- Hover tooltips with field info
- Highlight overlaps and gaps

**F) Reset values feature**
- Per-field optional reset value with validation against field width
- Calculated register reset value displayed in hex
- Visualizer shows reset state
- Arrays: show “N/A (Array)” (or similar) for total reset value

**G) Validation and feedback**
- Bit overlap detection
- Invalid bit range parsing
- Reset value range validation
- Address overlap detection at map level
- Show diagnostics inline + Problems panel

### 2.3 Non-goals (V1)
- Perfect preservation of YAML comments and formatting.
- HDL/C header/doc generation from within the extension.
- Multi-core project browsing beyond the current file.

## 3. UX / UI Design (What the user experiences)

### 3.1 Editor Model
- Implement a **VS Code Custom Editor** for `*.memmap.yml`.
- Support side-by-side opening (Text editor + Visual editor).

### 3.2 Layout (Mirrors Qt mental model)
- **Top action row (toolbar-like)**: Add Register, Add Array, Validate.
- **Main split view**:
  - **Left**: Outline tree of registers/arrays.
  - **Right**: Detail area with tabs:
    - **Properties**
    - **Bit Fields**
  - **Visualizer**: visible when a register is selected.

### 3.3 Interaction details
- Property edits are immediate and validated.
- Table edits support dropdowns (access type) and inline numeric validation.
- Field operations are available via:
  - buttons in the Bit Fields tab
  - right-click context menu
  - keyboard shortcuts

### 3.4 Diagnostics UX
- Inline form/table errors for local context.
- Problems panel diagnostics for scanability and navigation.

## 4. Technical Architecture (How we build it)

### 4.1 Extension Host (TypeScript)
- Use `CustomTextEditorProvider`.
- Parse YAML → normalized in-memory model.
- Apply edits back to the document via `WorkspaceEdit` (undo/redo compatible).

### 4.2 Webview Frontend
- React-based UI.
- `@vscode/webview-ui-toolkit` for theme-correct UI components.
- Message protocol:
  - `init`: send full model state
  - `applyPatch`: user edits (operations are preferable to raw text)
  - `diagnostics`: validation results

### 4.3 Validation Strategy
- **V1:** implement core validation in TypeScript (range parsing, overlaps, reset checks).
- **Optional parity mode:** Python subprocess validation using Pydantic, returning structured errors.

### 4.4 YAML serialization strategy
- V1: re-emit YAML on save.
- Keep ordering stable to reduce diff noise.

## 5. Implementation Roadmap (Phases with “Why” and Deliverables)

### Phase 0 — Requirements Lock
**Why:** avoid building the wrong schema or file target.
- Decide: edit standalone memory map YAML vs full `IpCore` document.
- Confirm file glob patterns.
- Confirm register widths (assume 32-bit first).

### Phase 1 — Scaffolding + Shared Types
**Outcome:** extension skeleton + shared type contracts.
- Scaffold TypeScript extension.
- Add schema generation pipeline from Pydantic.
- Generate TS types.

### Phase 2 — Custom Editor Skeleton
**Outcome:** open file in custom editor reliably.
- Register `customEditors`.
- Parse YAML and render UI shell.
- Implement message passing and refresh on text changes.

### Phase 3 — Project Management + Outline
**Outcome:** parity for navigation and file workflows.
- New/Open/Save/Save As commands.
- Outline tree with context menus.
- Add register/array creation flows.

### Phase 4 — Detail Editor + Bit Field Table
**Outcome:** parity for main editing workflow.
- Properties tab for register and array.
- Bit fields table with dropdown access type.
- Add/insert/remove/reorder operations.
- Helpers: unique names, find space.

### Phase 5 — Visualizer + Reset Values
**Outcome:** parity for visualization and reset defaults.
- Bit layout visualizer.
- Reset column with validation.
- Calculated register reset value display.

### Phase 6 — Diagnostics + Undo/Redo Polish
**Outcome:** safe editing with first-class VS Code integration.
- Publish diagnostics to Problems panel.
- Highlight overlaps/gaps.
- Ensure all edits route through `WorkspaceEdit`.

### Phase 7 — Testing + Packaging
**Outcome:** shippable `.vsix`.
- Add fixtures and integration tests.
- Package and document.

## 6. Testing Strategy
- Unit tests for parsing and overlap checks.
- Integration tests for open/edit/save.
- Fixture-driven regression tests (arrays, RW1C, reset values).

## 7. Risks and Mitigations
- YAML comment preservation: accept limitation; focus on semantic correctness.
- Model mismatch: schema generation + optional Python validation.
- Performance for large maps: lazy outline rendering, table virtualization.
