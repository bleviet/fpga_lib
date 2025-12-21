# VS Code Extension Development Plan: FPGA Memory Map Visual Editor

This document provides a detailed, step-by-step development plan for building the FPGA Memory Map Visual Editor extension for Visual Studio Code.

## Phase 1: Project Initialization & Schema Generation
**Goal:** Set up the development environment and generate the data contracts (schemas) that will ensure parity between the Python backend and the TypeScript frontend.

### 1.1. Workspace Setup
- [ ] **Initialize Extension:** Use `yo code` to scaffold a new TypeScript extension.
    - Name: `fpga-memory-map-editor`
    - Type: `New Extension (TypeScript)`
- [ ] **Repository Structure:** Create a `vscode-extension` folder in the root of the repo to keep it separate from the Python library, or decide on a monorepo structure.
- [ ] **Dependencies:** Install necessary npm packages:
    - `react`, `react-dom` (Frontend framework)
    - `@vscode/webview-ui-toolkit` (UI components)
    - `@vscode/codicons` (Icons)
    - `js-yaml` (YAML parsing/dumping)
    - `json-schema-to-typescript` (Code generation)

### 1.2. Schema Generation Pipeline
- [ ] **Python Script:** Create `scripts/generate_schema.py` in the root workspace.
    - Import `IpCore` from `fpga_lib.model.core`.
    - Use `IpCore.model_json_schema()` to generate the full JSON schema.
    - Save output to `vscode-extension/schemas/ip_core.schema.json`.
- [ ] **TypeScript Generation:** Create a script in `vscode-extension/package.json` to run `json-schema-to-typescript`.
    - Input: `schemas/ip_core.schema.json`
    - Output: `src/webview/types/ipCore.d.ts`
    - **Outcome:** We now have TypeScript interfaces (`IpCore`, `Register`, `BitField`) that exactly match the Python models.

## Phase 2: The Custom Editor Skeleton
**Goal:** Create a working extension that can open a `.memmap.yml` file and display its raw content in a custom webview.

### 2.1. Extension Registration
- [ ] **package.json:** Configure the `customEditors` contribution point.
    - `viewType`: `fpgaMemoryMap.editor`
    - `displayName`: "Memory Map Visual Editor"
    - `selector`: `[{ "filenamePattern": "*.memmap.yml" }]`
- [ ] **Activation:** Register the `CustomTextEditorProvider` in `src/extension.ts`.

### 2.2. Document Handling (Extension Host)
- [ ] **Document Model:** Create a `MemoryMapDocument` class that implements `vscode.CustomDocument`.
- [ ] **Parsing:** In `resolveCustomTextEditor`, read the document text.
    - Use `js-yaml` to parse the YAML content into a JSON object.
    - **Error Handling:** Handle invalid YAML gracefully (show error message).

### 2.3. Webview Setup (Frontend)
- [ ] **React Entry Point:** Create `src/webview/index.tsx`.
- [ ] **Build Script:** Configure `webpack` or `esbuild` to bundle the React app into a single `.js` file that can be injected into the Webview HTML.
- [ ] **Message Passing:**
    - **Host -> Webview:** Send the initial JSON data (`type: 'init', data: ...`).
    - **Webview:** Receive the message and store it in React state.
    - **Render:** Display a simple `JSON.stringify(data)` to verify the pipeline works.

## Phase 3: UI Implementation (The "View")
**Goal:** Replace the raw JSON dump with the actual GUI components (Tree View, Forms, Visualizer).

### 3.1. Layout & Navigation
- [ ] **Main Layout:** Create a CSS Grid layout with a Sidebar (30%) and Main Content (70%).
- [ ] **Tree View Component:**
    - Iterate through `memory_maps[0].address_blocks[0].registers`.
    - Render a recursive tree structure.
    - Implement selection logic: Clicking an item updates the `selectedId` state.

### 3.2. Detail Forms
- [ ] **Form Component:** Create a generic `DetailsPanel` that renders different forms based on the selected item type (Register vs. RegisterArray).
- [ ] **Input Fields:** Use `<VSCodeTextField>`, `<VSCodeDropdown>`, etc., from the UI Toolkit.
- [ ] **Binding:** Bind input values to the selected object's properties.

### 3.3. BitField Visualizer (The Core Feature)
- [ ] **Component Structure:** Create `BitFieldVisualizer.tsx`.
- [ ] **Rendering:**
    - Render a container representing 32 bits (width: 100%).
    - Calculate the width and position of each bitfield based on `lsb` and `msb`.
    - Render colored rectangles for occupied bits.
- [ ] **Interactivity:**
    - Implement hover tooltips showing field name and range.
    - (Later) Implement click-to-select and drag-to-resize.

## Phase 4: Two-Way Synchronization (The "Controller")
**Goal:** Make the editor editable. Changes in UI update the file; changes in the file update the UI.

### 4.1. Webview -> Extension Host
- [ ] **Action Dispatching:** When a user changes a form field:
    - Update local React state immediately (optimistic UI).
    - Send message to Host: `{ type: 'update', path: ['registers', 0, 'name'], value: 'newName' }`.
- [ ] **Applying Edits:** In the Extension Host:
    - Receive the update message.
    - Calculate the text edit required for the YAML file.
    - *Note:* Updating YAML while preserving comments is hard.
    - **Strategy:** For V1, we might regenerate the full YAML for the modified object or the whole file using `js-yaml`.
    - Apply `vscode.WorkspaceEdit`.

### 4.2. Extension Host -> Webview
- [ ] **File Watcher:** Listen for `onDidChangeTextDocument`.
- [ ] **Debounce:** Wait for the user to stop typing (e.g., 500ms).
- [ ] **Reparse & Push:** Parse the new YAML and send the full new state to the Webview.
- [ ] **State Reconciliation:** The React app needs to update its data without losing the user's current selection or scroll position.

## Phase 5: Validation & Advanced Features
**Goal:** Enforce the Pydantic rules and add polish.

### 5.1. Frontend Validation
- [ ] **Schema Validation:** Use the generated TypeScript types to validate inputs.
    - Example: Ensure `address_offset` is a valid hex string or integer.
    - Example: Ensure `name` matches the regex pattern.
- [ ] **Visual Feedback:** Show red borders/error text for invalid inputs.

### 5.2. Logic Validation (Overlap Detection)
- [ ] **Overlap Logic:** Port the Python overlap detection logic to TypeScript.
    - Check if `offset + width` of any register overlaps with another.
- [ ] **Visualizer Update:** Highlight overlapping regions in red in the BitField Visualizer.

### 5.3. Python Integration (Optional/Phase 6)
- [ ] **Validation Service:** If TypeScript logic is insufficient, spawn a Python process.
- [ ] **Linting:** Run `IpCore.model_validate()` on save and report diagnostics to the VS Code "Problems" panel.

## Phase 6: Packaging & Release
- [ ] **E2E Testing:** Use VS Code Extension Test Runner.
- [ ] **Bundling:** Run `vsce package` to create the `.vsix` file.
- [ ] **Documentation:** Write a `README.md` with screenshots and usage instructions.
