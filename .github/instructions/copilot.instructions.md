# Repository Instructions

## ⚠️ Context Loading Protocol
**You are strictly bound by the external rule files in this repository.**
Because these rules are modular, you must **actively read** the relevant file before answering complex queries.

1. **Global Logic:** Always refer to `.agent/rules/global.md` for architecture decisions.
2. **Python/FPGA Tasks:** If the user asks about `.py` files or `ipcore`, you MUST read `.agent/rules/python.md`.
3. **VS Code Tasks:** If the user asks about the extension, you MUST read `.agent/rules/vscode.md`.

## Quick Summary (Always Active)
* **Package Manager:** Use `uv` for Python, `npm` for TS.
* **Style:** Snake_case for Python, camelCase for TS.
* **Design:** Tailwind CSS with 8-point grid.
