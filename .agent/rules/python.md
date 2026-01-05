---
trigger: always_on
---

# Python & uv Rules

## Environment Management
- **Tooling:** STRICTLY use `uv` for all package operations.
- **Execution:** ALWAYS use `uv run <command>` (e.g., `uv run python`, `uv run pytest`).
- **Do Not:** Never attempt to source `bin/activate`. It fails in non-persistent agent shells.

## Code Standards
- **Style:** Adhere to PEP 8.
- **Type Hints:** Required for all function signatures.
- **Imports:** Absolute imports preferred over relative (e.g., `from app.utils import x` instead of `from ..utils import x`).

## "Screaming Architecture"
- **Models:** Put Pydantic schemas in `app/models/`.
- **Logic:** Business logic goes in `app/services/` or `app/domain/`.
- **Routes:** FastAPI routes go in `app/routers/`.
- **Discovery:** Before writing a helper, run `find backend/ -name "*utils*"` to see what exists.