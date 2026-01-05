---
trigger: always_on
---

# VS Code Extension Rules

## Tech Stack
- **Language:** TypeScript (Strict Mode).
- **Package Manager:** `npm`.
- **Framework:** VS Code Extension API (`@types/vscode`).

## Workflow
- **Build:** `npm run compile` is the source of truth.
- **Test:** `npm test` runs the Extension Host tests.
- **UI Rules:** - Use `vscode.window.showInformationMessage` for user feedback.
  - Do not use `console.log` for production; use an `OutputChannel`.

## Manifest Integrity (`package.json`)
- **Commands:** If you add a command in code, you MUST add it to `contributes.commands` in `package.json`.
- **Keybindings:** Check for conflicts before adding new keybindings.

## UI & Design System (Webviews)

### 1. The 8-Point Grid System
Strictly adhere to the 8-point spatial system for all layout, spacing, and sizing.
- **Base Unit:** 8px.
- **Sub-Unit:** 4px (only for fine-tuning inside components).
- **Tailwind Mapping:**
  - `class="...-1"` = 4px (0.25rem) -> *Sub-unit*
  - `class="...-2"` = 8px (0.5rem) -> *1x Base Unit*
  - `class="...-3"` = 12px (0.75rem) -> *Allowed for 4px rhythm*
  - `class="...-4"` = 16px (1rem)    -> *2x Base Unit*
  - `class="...-8"` = 32px (2rem)    -> *4x Base Unit*
- **Forbidden:** Do NOT use arbitrary values like `w-[13px]` or `mt-[5px]`. Always snap to the nearest grid step.

### 2. Tailwind CSS & Theming
- **Theme Support:** The UI must support VS Code Light, Dark, and High Contrast themes automatically.
- **Color Variables:** Do NOT hardcode hex colors (e.g., `#ffffff`).
  - Use VS Code CSS variables extended in Tailwind config.
  - Example: `bg-[var(--vscode-editor-background)]` or `text-[var(--vscode-editor-foreground)]`.
- **Flex/Grid:** Use Flexbox and Grid utility classes for layout. Avoid absolute positioning unless creating overlays/modals.

### 3. Component Structure
- **Container:** Major sections should use `p-4` (16px) padding.
- **Spacing:** Use `gap-2` (8px) or `gap-4` (16px) for lists and form groups.
- **Interactivity:** Interactive elements must have `hover:bg-...` states that respect the VS Code theme contrast guidelines.

### 3. Adaptive Theming & Color Schemes
The UI must automatically inherit the user's current VS Code theme (Light, Dark, High Contrast, or Custom).

- **Zero Hardcoding Policy:**
  - **FORBIDDEN:** Never use hex codes (`#ffffff`, `#000000`) or standard Tailwind color scales (`bg-gray-50`, `text-slate-900`) for base UI elements.
  - **REQUIRED:** You MUST use VS Code CSS Variables. This ensures the extension looks correct in *any* theme.

- **Variable Mapping (Tailwind):**
  - Use arbitrary values referencing the variables:
    - **Background:** `bg-[var(--vscode-editor-background)]`
    - **Text:** `text-[var(--vscode-editor-foreground)]`
    - **Borders:** `border-[var(--vscode-panel-border)]`
    - **Inputs:** `bg-[var(--vscode-input-background)]`, `text-[var(--vscode-input-foreground)]`
    - **Buttons:** `bg-[var(--vscode-button-background)]`, `text-[var(--vscode-button-foreground)]`

- **Interactive States:**
  - Hover and Focus states must also use theme variables to ensure contrast.
  - Example: `hover:bg-[var(--vscode-list-hoverBackground)]` instead of `hover:bg-gray-200`.

- **High Contrast Support:**
  - Always verify that borders are visible when `var(--vscode-highContrast-border)` is active.
  - Do not rely on shadows (`box-shadow`) alone for hierarchy, as these are often disabled in High Contrast mode.