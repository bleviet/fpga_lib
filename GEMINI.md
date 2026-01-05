# Project Agent Configuration

## Rule Imports
Please strictly follow the rules defined in the `.agent/rules/` directory:
1. **Global Rules:** `.agent/rules/global.md` (Apply always)
2. **Contextual Rules:**
   - If working in `/fpga_lib` -> Apply `.agent/rules/python.md`
   - If working in `/vscode-extension` -> Apply `.agent/rules/vscode.md`

## Quick Start
- Read `MAP.md` immediately.
- If this is a Python task, remember: `uv run` only!