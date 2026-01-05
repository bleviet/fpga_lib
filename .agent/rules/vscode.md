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

**All visual styling rules are centralized in:**
📄 **[../../.github/instructions/visual-styling.md](../../.github/instructions/visual-styling.md)**

This includes:
- VS Code CSS variable usage (REQUIRED)
- 8-point grid system (STRICT)
- Typography rules (font-mono for technical data)
- Component patterns
- Color system
- Dark mode support

**Quick Summary:**
- ✅ Use `var(--vscode-*)` for ALL colors
- ✅ Follow 8-point grid (no arbitrary px values)
- ✅ Use `font-mono` for addresses, hex, bits
- ❌ Never use hardcoded colors or Tailwind color scales
- ❌ Never use arbitrary spacing (`mt-[13px]`)

For complete guidelines, examples, and component patterns:
👉 **[Read visual-styling.md](../../.github/instructions/visual-styling.md)**
