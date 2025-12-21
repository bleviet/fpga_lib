# FPGA Memory Map Visual Editor (VS Code Extension)

This extension provides a visual editor for FPGA memory map YAML files (`*.memmap.yml`).

## Development Setup

1.  **Install Dependencies:**
    ```bash
    cd vscode-extension
    npm install
    ```

2.  **Generate TypeScript Types:**
    ```bash
    npm run generate-types
    ```

3.  **Compile:**
    ```bash
    npm run compile
    ```

4.  **Run/Debug:**
    - Open this folder in VS Code.
    - Press `F5` to launch the Extension Development Host.
    - Open a `.memmap.yml` file to see the editor.

## Architecture

-   **Extension Host (`src/extension.ts`):** Registers the `CustomTextEditorProvider`. Handles file I/O and synchronization.
-   **Webview (`src/webview/index.tsx`):** React application that renders the UI.
-   **Schemas (`schemas/`):** JSON schemas generated from Python Pydantic models.
-   **Types (`src/webview/types/`):** TypeScript interfaces generated from JSON schemas.

## Scripts

-   `npm run compile`: Compiles both the extension and the webview using Webpack.
-   `npm run watch`: Watches for changes and recompiles.
-   `npm run generate-types`: Regenerates TypeScript types from the JSON schemas.
