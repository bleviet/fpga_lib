# LLM Instructions: Frontend, Design System & Theming

You are an expert Frontend Developer specializing in **Tailwind CSS** and **VS Code Webviews**.
When generating code for this repository, you must strictly adhere to the design system rules defined below, use the **8-point grid system** for layout, and ensure fully responsive **Dark Mode** support.

## 1. Design System Rules (Strict Visual Style)
Always follow the visual style defined in `resources/register-editor-v2.html`.

### Colors & Palette (Light / Dark Mode Strategy)
All color classes **must** include a dark mode counterpart. Use the `dark:` modifier.

- **Backgrounds:** - Canvas: `bg-gray-50 dark:bg-[#1e1e1e]` (Matches VS Code default).
  - Panels/Cards: `bg-white dark:bg-[#252526]` (Matches VS Code sidebar/panels).
- **Primary Action:** - Text: `text-indigo-600 dark:text-indigo-400`.
  - Backgrounds: `bg-indigo-600 dark:bg-indigo-600`.
- **Borders:** - Subtle: `border-gray-200 dark:border-gray-700`.
  - Inputs/Strong: `border-gray-300 dark:border-gray-600`.
- **Text:**
  - Primary: `text-gray-900 dark:text-gray-100`.
  - Secondary: `text-gray-500 dark:text-gray-400`.
- **Highlights:** `ring-indigo-500` (Focus states).

### Typography
- **Fonts:** - Sans: `font-sans` (Inter).
  - Mono: `font-mono` (JetBrains Mono) — Use for hex codes, bits, and register addresses.
- **Section Headers:** `text-xs uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400`.
- **Base Size:** `text-sm` (Standard for VS Code extensions).

### Component Styles
- **Buttons:** - Base: `rounded-md transition-colors font-medium`.
  - Hover (Secondary): `hover:bg-indigo-50 dark:hover:bg-white/10`.
  - Hover (Primary): `hover:bg-indigo-700`.
- **Inputs:** - Standard: `bg-white dark:bg-[#3c3c3c] border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500`.
- **Tables:** - Layout: `w-full text-left border-collapse`.
  - Headers: Sticky positioning with background context (`bg-gray-50 dark:bg-[#1e1e1e]`).
  - Rows: `hover:bg-gray-50 dark:hover:bg-[#2a2d2e]`.

## 2. The 8-Point Grid System (Layout & Spacing)
All layout and spacing must follow the **8-point grid** to maintain strict visual rhythm.

- **2px (0.5):** Micro-spacing (e.g., inside borders).
- **4px (1):** Tight grouping (icon + text).
- **8px (2):** Standard component spacing.
- **16px (4):** Container padding.
- **24px (6):** Section gaps.
- **32px (8):** Major separation.

**Vertical Rhythm:**
- Standard Inputs/Buttons: `h-8` (32px) or `h-10` (40px).
- Large Touch Targets: `h-12` (48px).

## 3. VS Code WebView Constraints
- **Environment:** The app runs inside an Electron WebView (VS Code).
- **Theme Awareness:** The extension must seamlessly switch between Light and Dark modes. Tailwind's `dark` class is toggled on the `html` element by the webview logic.
- **Scrollbars:** Use standard native scrolling; do not implement custom scrollbars unless specified.

## 4. Code Generation Rules

**✅ DO:**
- Check if a component exists in `register-editor-v2.html` before creating a new one.
- Use `clsx` or string interpolation for conditional classes.
- Use `font-mono` for ANY technical data (0x00, Bit [31:0]).
- **ALWAYS** include `dark:` classes for background, text, and border colors.

**❌ DO NOT:**
- Invent new CSS classes. Use Tailwind utilities only.
- Use arbitrary pixel values (e.g., `width: 250px`). Use `w-64`.
- Use `blue-600` or generic colors. STRICTLY use `indigo-600` as the primary brand color.
- Forget to inverse text colors (e.g., black text on dark background).

## 5. Example Usage

```jsx
// Example: A conforming Input Field with Dark Mode Support
const SearchInput = () => (
  <div className="relative">
    <input 
      type="text" 
      className="
        w-full h-10 pl-3 pr-10               // 8-pt Grid (h-10 = 40px)
        text-sm font-sans                    // Typography
        text-gray-900 dark:text-gray-100     // Adaptive Text Color
        bg-white dark:bg-[#3c3c3c]           // Adaptive Background
        border border-gray-300 dark:border-gray-600 // Adaptive Border
        rounded-lg shadow-sm                 // Specific Component Style
        focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 // Primary Color
        placeholder-gray-400 dark:placeholder-gray-500
      "
      placeholder="Search registers..."
    />
    <span className="absolute right-3 top-2.5 text-xs font-mono text-gray-400 dark:text-gray-500">
      CMD+K
    </span>
  </div>
);
