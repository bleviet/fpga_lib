# Visual Styling Guidelines for VS Code Extension

**For:** Antigravity AI & GitHub Copilot  
**Target:** VS Code WebView UI Components

---

## Core Principles

1. **Theme-First Design:** All UI must adapt to VS Code's active theme (Light, Dark, High Contrast, or Custom)
2. **8-Point Grid System:** All spacing and sizing follows strict 8px base unit
3. **Zero Hardcoding:** Never use fixed colors - always use VS Code CSS variables
4. **Semantic Typography:** Technical data uses monospace, UI text uses system font

---

## 1. Color System

### Rule: Use VS Code CSS Variables Only

**FORBIDDEN:**
```jsx
// ❌ Never do this
bg-gray-50 dark:bg-[#1e1e1e]
text-blue-600
border-gray-300
```

**REQUIRED:**
```jsx
// ✅ Always do this
bg-[var(--vscode-editor-background)]
text-[var(--vscode-editor-foreground)]
border-[var(--vscode-panel-border)]
```

### Variable Reference

**Backgrounds:**
```jsx
bg-[var(--vscode-editor-background)]              // Main canvas
bg-[var(--vscode-sideBar-background)]             // Panels, cards
bg-[var(--vscode-input-background)]               // Form inputs
bg-[var(--vscode-button-background)]              // Primary buttons
bg-[var(--vscode-button-secondaryBackground)]     // Secondary buttons
```

**Text:**
```jsx
text-[var(--vscode-editor-foreground)]            // Primary text
text-[var(--vscode-descriptionForeground)]        // Secondary/muted text
text-[var(--vscode-input-foreground)]             // Input text
text-[var(--vscode-button-foreground)]            // Button text
```

**Borders:**
```jsx
border-[var(--vscode-panel-border)]               // Subtle borders
border-[var(--vscode-input-border)]               // Input borders
border-[var(--vscode-focusBorder)]                // Focus indicators
```

**Interactive States:**
```jsx
hover:bg-[var(--vscode-list-hoverBackground)]     // Hover state
hover:bg-[var(--vscode-button-hoverBackground)]   // Button hover
focus:ring-[var(--vscode-focusBorder)]            // Focus ring
```

**Status/Semantic Colors:**
```jsx
// Use VS Code semantic colors when available
text-[var(--vscode-errorForeground)]              // Errors
text-[var(--vscode-editorWarning-foreground)]     // Warnings
// For success, if no variable exists, use theme-appropriate green
```

---

## 2. The 8-Point Grid System

All spacing, sizing, and layout MUST follow the 8-point grid.

### Grid Scale

| Value | Pixels | Tailwind | Usage |
|-------|--------|----------|-------|
| 0.5 | 2px | `...-0.5` | Micro spacing (rare) |
| 1 | 4px | `...-1` | Tight grouping (icon + text) |
| 2 | 8px | `...-2` | Standard spacing |
| 3 | 12px | `...-3` | Allowed (maintains 4px rhythm) |
| 4 | 16px | `...-4` | Container padding |
| 6 | 24px | `...-6` | Section gaps |
| 8 | 32px | `...-8` | Major separation |
| 10 | 40px | `...-10` | Input height |
| 12 | 48px | `...-12` | Large touch targets |

### Component Heights

```jsx
h-8   // 32px - Small buttons, compact inputs
h-10  // 40px - Standard inputs, buttons
h-12  // 48px - Large touch targets
```

### Container Padding

```jsx
p-4   // 16px - Standard container padding
p-6   // 24px - Spacious containers
```

### Element Spacing

```jsx
gap-2  // 8px - Standard gap between items
gap-4  // 16px - Comfortable gap
gap-6  // 24px - Section gaps
```

**FORBIDDEN:**
```jsx
// ❌ Never use arbitrary values
w-[250px]
mt-[13px]
gap-[15px]
```

---

## 3. Typography

### Font Families

```jsx
font-sans  // System font for UI text
font-mono  // Monospace for technical data
```

### Usage Rules

**ALWAYS use `font-mono` for:**
- Register addresses: `0x0000`, `0x00FF`
- Bit ranges: `[31:0]`, `[7:4]`
- Hex values: `0xDEADBEEF`
- Binary values: `0b1010`
- Technical identifiers

**Use `font-sans` for:**
- Labels, descriptions
- Button text
- General UI text

### Type Scale

```jsx
text-xs    // 12px - Small labels, captions
text-sm    // 14px - Standard UI text (DEFAULT)
text-base  // 16px - Emphasis
text-lg    // 18px - Headings
```

### Section Headers

```jsx
className="
  text-xs uppercase tracking-wider font-bold
  text-[var(--vscode-descriptionForeground)]
"
```

---

## 4. Component Patterns

### Buttons

**Primary Button:**
```jsx
className="
  px-4 py-2 rounded-md             // 8-pt grid
  bg-[var(--vscode-button-background)]
  text-[var(--vscode-button-foreground)]
  hover:bg-[var(--vscode-button-hoverBackground)]
  focus:ring-2 focus:ring-[var(--vscode-focusBorder)]
  font-medium text-sm
"
```

**Secondary/Ghost Button:**
```jsx
className="
  px-4 py-2 rounded-md
  bg-[var(--vscode-button-secondaryBackground)]
  text-[var(--vscode-button-secondaryForeground)]
  hover:bg-[var(--vscode-button-secondaryHoverBackground)]
  focus:ring-2 focus:ring-[var(--vscode-focusBorder)]
  font-medium text-sm
"
```

### Input Fields

```jsx
className="
  w-full h-10 px-3                // 8-pt grid (40px height)
  text-sm font-sans
  bg-[var(--vscode-input-background)]
  text-[var(--vscode-input-foreground)]
  border border-[var(--vscode-input-border)]
  rounded-lg
  focus:ring-2 focus:ring-[var(--vscode-focusBorder)]
  focus:outline-none
  placeholder-[var(--vscode-input-placeholderForeground)]
"
```

### Tables

**Table Container:**
```jsx
className="w-full text-left border-collapse"
```

**Table Headers:**
```jsx
className="
  sticky top-0 z-10
  bg-[var(--vscode-editor-background)]
  border-b border-[var(--vscode-panel-border)]
  text-xs uppercase tracking-wider font-bold
  text-[var(--vscode-descriptionForeground)]
  px-4 py-2                       // 8-pt grid
"
```

**Table Rows:**
```jsx
className="
  hover:bg-[var(--vscode-list-hoverBackground)]
  border-b border-[var(--vscode-panel-border)]
  text-sm
  text-[var(--vscode-editor-foreground)]
"
```

**Table Cells:**
```jsx
className="px-4 py-2 font-mono"   // For technical data
className="px-4 py-2 font-sans"   // For text labels
```

### Panels/Cards

```jsx
className="
  p-4                             // 8-pt grid padding
  bg-[var(--vscode-sideBar-background)]
  border border-[var(--vscode-panel-border)]
  rounded-lg
"
```

---

## 5. Layout Guidelines

### Flexbox & Grid

**Preferred layout tools:**
```jsx
flex items-center justify-between gap-4
grid grid-cols-2 gap-4
```

**Avoid:** Absolute positioning unless for overlays/modals

### Container Structure

```jsx
// Major section
<div className="p-6 bg-[var(--vscode-editor-background)]">
  
  // Card/Panel
  <div className="p-4 bg-[var(--vscode-sideBar-background)] border border-[var(--vscode-panel-border)] rounded-lg">
    
    // Content with spacing
    <div className="flex flex-col gap-4">
      <div>...</div>
      <div>...</div>
    </div>
    
  </div>
</div>
```

---

## 6. Dark Mode & Theme Support

### Automatic Adaptation

VS Code webviews automatically toggle the `dark` class on the HTML element.

**Your code does NOT need `dark:` classes** when using VS Code variables:
```jsx
// ✅ This automatically adapts
bg-[var(--vscode-editor-background)]

// ❌ Don't do this with VS Code variables
bg-[var(--vscode-editor-background)] dark:bg-[var(--vscode-editor-background)]
```

Only use `dark:` if you absolutely need different behavior in dark mode that VS Code variables don't provide.

### High Contrast Support

VS Code provides `--vscode-highContrast-border` when high contrast is active.

**Always ensure borders are visible:**
```jsx
border border-[var(--vscode-panel-border)]
```

**Don't rely solely on shadows:**
```jsx
// ❌ Bad - shadows may be disabled in high contrast
shadow-lg

// ✅ Good - visible border + optional shadow
border border-[var(--vscode-panel-border)] shadow-sm
```

---

## 7. Examples

### Complete Form Field

```tsx
const RegisterNameField = ({ value, onChange }: Props) => (
  <div className="flex flex-col gap-2">
    <label className="
      text-xs uppercase tracking-wider font-bold
      text-[var(--vscode-descriptionForeground)]
    ">
      Register Name
    </label>
    <input
      type="text"
      value={value}
      onChange={onChange}
      className="
        w-full h-10 px-3
        text-sm font-sans
        bg-[var(--vscode-input-background)]
        text-[var(--vscode-input-foreground)]
        border border-[var(--vscode-input-border)]
        rounded-lg
        focus:ring-2 focus:ring-[var(--vscode-focusBorder)]
        focus:outline-none
        placeholder-[var(--vscode-input-placeholderForeground)]
      "
      placeholder="Enter register name"
    />
  </div>
);
```

### Register Address Display

```tsx
const AddressDisplay = ({ address }: { address: number }) => (
  <div className="
    px-3 py-1.5
    bg-[var(--vscode-sideBar-background)]
    border border-[var(--vscode-panel-border)]
    rounded-md
  ">
    <span className="
      text-sm font-mono
      text-[var(--vscode-editor-foreground)]
    ">
      0x{address.toString(16).toUpperCase().padStart(4, '0')}
    </span>
  </div>
);
```

### Interactive Table Row

```tsx
const RegisterRow = ({ register, onClick }: Props) => (
  <tr
    onClick={onClick}
    className="
      cursor-pointer
      hover:bg-[var(--vscode-list-hoverBackground)]
      border-b border-[var(--vscode-panel-border)]
    "
  >
    <td className="px-4 py-2">
      <span className="text-sm font-mono text-[var(--vscode-editor-foreground)]">
        0x{register.offset.toString(16).padStart(4, '0')}
      </span>
    </td>
    <td className="px-4 py-2">
      <span className="text-sm font-sans text-[var(--vscode-editor-foreground)]">
        {register.name}
      </span>
    </td>
  </tr>
);
```

---

## 8. Checklist

Before submitting code, verify:

- [ ] All colors use `var(--vscode-*)` variables
- [ ] No hardcoded hex colors (`#ffffff`, `#000000`)
- [ ] No Tailwind color scales (`bg-gray-50`, `text-blue-600`)
- [ ] All spacing follows 8-point grid (no `mt-[13px]`)
- [ ] Technical data uses `font-mono`
- [ ] UI text uses `font-sans`
- [ ] Interactive elements have hover states
- [ ] Focus states use `var(--vscode-focusBorder)`
- [ ] Borders are visible (for high contrast)
- [ ] Component heights use grid values (`h-8`, `h-10`, `h-12`)

---

## 9. Common VS Code CSS Variables

```css
/* Backgrounds */
--vscode-editor-background
--vscode-sideBar-background
--vscode-input-background
--vscode-button-background
--vscode-button-secondaryBackground

/* Foregrounds */
--vscode-editor-foreground
--vscode-descriptionForeground
--vscode-input-foreground
--vscode-button-foreground
--vscode-errorForeground

/* Borders */
--vscode-panel-border
--vscode-input-border
--vscode-focusBorder

/* Interactive */
--vscode-list-hoverBackground
--vscode-button-hoverBackground
--vscode-list-activeSelectionBackground
```

**Full list:** https://code.visualstudio.com/api/references/theme-color

---

**Last Updated:** 2026-01-05  
**Applies To:** All VS Code extension webview code
