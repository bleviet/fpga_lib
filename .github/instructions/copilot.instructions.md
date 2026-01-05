# GitHub Copilot Instructions

**For:** VS Code Extension Development

---

## Visual Styling & UI Guidelines

All frontend code MUST follow the unified visual styling guidelines:

**📄 See:** [visual-styling.md](./visual-styling.md)

This includes:
- VS Code theme variable usage (required)
- 8-point grid system
- Typography rules
- Component patterns

---

## Additional Copilot-Specific Context

### Code Generation Rules

**✅ DO:**
- Use VS Code CSS variables for ALL colors
- Follow 8-point grid strictly
- Use `font-mono` for technical data (addresses, hex, bits)
- Include proper TypeScript types
- Use `clsx` or template literals for conditional classes

**❌ DO NOT:**
- Use hardcoded colors (#ffffff, bg-gray-50)
- Use arbitrary pixel values (width: 250px - use w-64)
- Forget hover/focus states
- Use `console.log` (use VS Code OutputChannel instead)

### TypeScript Standards

- **Strict Mode:** Always enabled
- **Types:** Explicit return types for functions
- **Props:** Use TypeScript interfaces, not PropTypes
- **Imports:** Use absolute imports where configured

### React Patterns

- **Hooks:** Prefer functional components with hooks
- **State:** Use `useState` for local, context for shared
- **Effects:** Include dependency arrays
- **Memoization:** Use `useMemo`/`useCallback` for expensive operations

### Testing

- **Framework:** Jest + React Testing Library
- **Coverage:** Aim for >80% on new code
- **Pattern:** Arrange-Act-Assert

---

For detailed visual styling rules, typography, color system, and component examples:
👉 **[Read visual-styling.md](./visual-styling.md)**
