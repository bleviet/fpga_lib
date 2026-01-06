---
trigger: always_on
---

# VS Code Extension Rules

## Location & Tech Stack
- **Path:** `ipcore_tools/vscode/ipcore_editor/`
- **Language:** TypeScript (Strict Mode).
- **Package Manager:** `npm`.
- **Framework:** VS Code Extension API (`@types/vscode`).
- **UI Framework:** React for webview components.
- **Templates:** Nunjucks for VHDL generation.

## Workflow
- **Build:** `npm run compile` is the source of truth.
- **Test:** `npm test` runs the Extension Host tests.
- **Template Sync:** `npm run sync-templates` copies Jinja2 templates from `fpga_lib/generator/hdl/templates/` to `src/generator/templates/`.
- **UI Rules:**
  - Use `vscode.window.showInformationMessage` for user feedback.
  - Do not use `console.log` for production; use an `OutputChannel`.

## Manifest Integrity (`package.json`)
- **Commands:** If you add a command in code, you MUST add it to `contributes.commands`.
  - Existing commands: `createIpCore`, `createMemoryMap`, `generateVHDL`, `generateVHDLWithBus`
- **Custom Editors:** `fpgaMemoryMap.editor` (*.memmap.yml), `fpgaIpCore.editor` (*.yml)
- **Keybindings:** Check for conflicts before adding new keybindings.

## Architecture
- **Entry Point:** `src/extension.ts` - Registers providers and commands on activation.
- **Providers:** `src/providers/` - Custom editor providers (MemoryMapEditorProvider, IpCoreEditorProvider).
- **Commands:** `src/commands/` - File creation and VHDL generation commands.
- **Services:** `src/services/` - DocumentManager, HtmlGenerator, ImportResolver, MessageHandler, YamlValidator.
- **Generator:** `src/generator/` - TypeScript VHDL generator (parallel to Python implementation).
- **Webview:** `src/webview/` - React components for visual editors.

## UI & Design System (Webviews)

**All visual styling rules are centralized in:**
📄 **[visual-styling.md](visual-styling.md)**

This includes:
- VS Code CSS variable usage (REQUIRED)
- 8-point grid system (STRICT)
- Typography rules (font-mono for technical data)
- Component patterns
- Color system
- Dark mode support

For complete guidelines, examples, and component patterns:
👉 **[Read visual-styling.md](visual-styling.md)**