---
trigger: always_on
---

# Global Agent Protocols

## 1. The "Map First" Doctrine
- **Mandatory Read:** At the start of EVERY task, read `MAP.md` in the root directory.
- **Registration:** You are responsible for keeping `MAP.md` updated.
  - If you create a file: Add it to the map.
  - If you refactor: Update the description.
- **Reuse:** Never create a new utility if one exists in the map.

## 2. General Hygiene
- **Commit Messages:** Use Conventional Commits (feat, fix, docs, chore, test).
- **Comments:** Do not leave commented-out code. Delete it.
- **Documentation:** Keep README files up-to-date when changing functionality.

## 3. Project Structure Awareness
- **Python Backend:** Core library is in `/fpga_lib/` with models, parsers, generators, runtime, and drivers.
- **Tools:** Standalone tools in `/ipcore_tools/` (Python GUI/TUI editors, VSCode extension).
- **Schemas:** IP Core and Memory Map specifications in `/ipcore_spec/`.
- **Tests:** All tests are in `/fpga_lib/tests/` with subdirectories matching the source structure.
