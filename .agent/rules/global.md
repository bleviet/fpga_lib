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

## 2. Cross-Domain Boundaries
This repository is a hybrid (Python Backend + VS Code Extension).
- **Backend:** Located in `/backend`. See `python.md` for rules.
- **Extension:** Located in `/extension`. See `vscode.md` for rules.
- **IPC:** If changing the communication interface (API/JSON-RPC) between them, you MUST update both sides atomically.

## 3. General Hygiene
- **Commit Messages:** Use Conventional Commits (feat, fix, docs, chore).
- **Comments:** Do not leave commented-out code. Delete it.