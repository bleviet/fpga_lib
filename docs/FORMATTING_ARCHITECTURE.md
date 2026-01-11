<!-- editorconfig-checker-disable-file -->
<!-- This file contains code examples with various indentation styles for documentation purposes -->

# Code Formatting Architecture

> Technical architecture and implementation details for the ipcore formatting system

## System Overview

The formatting system consists of multiple layers working together to enforce consistent code style:

```
┌─────────────────────────────────────────────────────────────┐
│                     Developer Workflow                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Editor Integration                      │
│  (EditorConfig, VS Code Extensions, Format on Save)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Git Pre-commit Hooks                     │
│           (pre-commit framework, .pre-commit-config)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Language-Specific Tools                    │
│  ┌──────────────┬──────────────┬──────────────┐           │
│  │    Python    │  TypeScript  │     YAML     │           │
│  │  Black       │   Prettier   │   Prettier   │           │
│  │  isort       │   ESLint     │              │           │
│  └──────────────┴──────────────┴──────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   EditorConfig Validation                    │
│            (editorconfig-checker, baseline rules)           │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. EditorConfig Layer

**Purpose**: Baseline formatting rules understood by all editors

**File**: `.editorconfig`

**Scope**: Cross-language, cross-editor standards

**Rules Applied**:
- Line endings (LF)
- Character encoding (UTF-8)
- Indentation type and size
- Trailing whitespace handling
- Final newline requirements

**Technology**: EditorConfig specification (https://editorconfig.org/)

**Integration Points**:
- Editor plugins (VS Code, PyCharm, Vim, etc.)
- `editorconfig-checker` tool in pre-commit
- Base configuration for language-specific formatters

**Configuration Structure**:

```ini
root = true

[*]                           # Global defaults
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{yml,yaml,json,ts,tsx,js,jsx,css,scss,html}]  # 2-space languages
indent_size = 2

[*.py]                        # Python-specific
indent_size = 4

[Makefile]                    # Make requires tabs
indent_style = tab

[*.md]                        # Markdown special case
trim_trailing_whitespace = false
```

### 2. Python Formatting Stack

#### Black (Code Formatter)

**Purpose**: Opinionated Python code formatter

**Version**: 25.12.0

**Configuration**: `pyproject.toml`

```toml
[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  \.eggs
  | \.git
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

**Behavior**:
- Reformats all Python code to consistent style
- Enforces PEP 8 with some modern adjustments
- Non-configurable (by design) except line length and target Python version
- Preserves semantic meaning of code

**Integration**:
- Pre-commit hook: `black`
- VS Code extension: `ms-python.black-formatter`
- Command line: `uv run black <path>`

**Excluded from Black**:
- Virtual environments (.venv, venv)
- Build artifacts (build/, dist/)
- Cache directories

#### isort (Import Sorter)

**Purpose**: Sort and organize Python imports

**Version**: 7.0.0

**Configuration**: `pyproject.toml`

```toml
[tool.isort]
profile = "black"                    # Compatible with Black
line_length = 100                    # Match Black
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

**Behavior**:
- Groups imports: stdlib, third-party, first-party, local
- Sorts alphabetically within groups
- Formats multi-line imports consistently
- Removes unused imports (with additional tools)

**Integration**:
- Pre-commit hook: `isort`
- VS Code: Code action on save
- Command line: `uv run isort <path>`

**Import Order**:
1. Standard library imports
2. Related third party imports
3. Local application/library imports
4. Relative imports

### 3. TypeScript/JavaScript Formatting Stack

#### Prettier (Code Formatter)

**Purpose**: Opinionated formatter for TypeScript, JavaScript, JSON, YAML

**Version**: 4.0.0-alpha.8

**Configuration**: `ipcore_tools/vscode/ipcore_editor/.prettierrc.js`

```javascript
module.exports = {
  semi: true,                // Require semicolons
  trailingComma: 'es5',     // Trailing commas where valid in ES5
  singleQuote: true,        // Use single quotes
  printWidth: 100,          // Line length
  tabWidth: 2,              // 2-space indentation
  useTabs: false,           // Use spaces, not tabs
  arrowParens: 'always',    // Always wrap arrow function params
  endOfLine: 'lf',          // Unix line endings
  bracketSpacing: true,     // Spaces in object literals
};
```

**Behavior**:
- Parses code to AST (Abstract Syntax Tree)
- Reprints with consistent style
- Minimal configuration options (opinionated)
- Supports TypeScript, JSX, JSON, YAML, Markdown, CSS

**Integration**:
- Pre-commit hook: `prettier`
- VS Code extension: `esbenp.prettier-vscode`
- NPM scripts: `npm run format`
- Husky hook: In VSCode extension directory

**File Patterns**:
- TypeScript: `*.ts`
- React TypeScript: `*.tsx`
- JavaScript: `*.js`, `*.jsx`
- YAML: `*.yml`, `*.yaml`
- JSON: `*.json`

#### ESLint (Linter)

**Purpose**: Static analysis and linting for TypeScript/JavaScript

**Integration**:
- Configured in VSCode extension project
- Runs via NPM scripts
- Not in pre-commit hooks (intentional - slower, focuses on logic not style)

### 4. Pre-commit Hook Framework

**Purpose**: Automated checks before git commit

**Configuration**: `.pre-commit-config.yaml`

**Hook Execution Order**:

```yaml
repos:
  # 1. Basic file hygiene
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - trailing-whitespace      # Remove trailing spaces
      - end-of-file-fixer       # Ensure final newline
      - check-yaml              # Validate YAML syntax
      - check-added-large-files # Prevent huge files
      - mixed-line-ending       # Enforce LF

  # 2. Python formatting
  - repo: https://github.com/psf/black
    hooks:
      - black                   # Format Python code
        language_version: python3.13

  # 3. Python import sorting
  - repo: https://github.com/pycqa/isort
    hooks:
      - isort                   # Sort Python imports

  # 4. TypeScript/JavaScript/YAML formatting
  - repo: https://github.com/pre-commit/mirrors-prettier
    hooks:
      - prettier                # Format TS/JS/YAML/JSON

  # 5. EditorConfig validation
  - repo: https://github.com/editorconfig-checker/editorconfig-checker.python
    hooks:
      - editorconfig-checker    # Validate all rules
```

**Hook Behavior**:
- **Auto-fixing hooks**: trailing-whitespace, end-of-file-fixer, black, isort, prettier
  - Modify files in place
  - Fail the commit
  - User must `git add` modified files and commit again
- **Validation hooks**: check-yaml, editorconfig-checker
  - Don't modify files
  - Report errors
  - User must fix manually

**Performance Optimization**:
- Hooks only run on staged files (not entire codebase)
- Cached by pre-commit framework
- Parallel execution where possible

### 5. Husky Integration (VSCode Extension)

**Purpose**: Git hooks for VSCode extension directory

**Location**: `.husky/pre-commit`

**Configuration**:

```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

cd ipcore_tools/vscode/ipcore_editor
npx lint-staged
```

**lint-staged Configuration** (`package.json`):

```json
{
  "lint-staged": {
    "*.{ts,tsx,js,jsx}": [
      "prettier --write",
      "eslint --fix"
    ],
    "*.{json,css,scss,md}": [
      "prettier --write"
    ]
  }
}
```

**Relationship to Root Pre-commit**:
- Husky runs in VSCode extension directory only
- Root pre-commit hooks handle entire repository
- Both can coexist (Husky is subset for extension dev)

## Workflow Integration

### Developer Commit Workflow

```
Developer writes code
        │
        ▼
git add <files>
        │
        ▼
git commit -m "message"
        │
        ▼
┌───────────────────────────┐
│  Pre-commit hooks trigger │
└───────────────────────────┘
        │
        ├─► trailing-whitespace    ──► Auto-fix
        ├─► end-of-file-fixer     ──► Auto-fix
        ├─► check-yaml            ──► Validate
        ├─► check-added-large-files ──► Validate
        ├─► mixed-line-ending     ──► Auto-fix
        ├─► black                 ──► Auto-fix
        ├─► isort                 ──► Auto-fix
        ├─► prettier              ──► Auto-fix
        └─► editorconfig-checker  ──► Validate
        │
        ▼
   All passed?
        │
    ┌───┴───┐
    │       │
   Yes      No
    │       │
    ▼       ▼
 Commit  Commit blocked
 Success    │
            ▼
       Files modified
            │
            ▼
       git add -u
            │
            ▼
       git commit
```

### CI/CD Integration (Future)

**Planned**: GitHub Actions workflow for PR validation

```yaml
# .github/workflows/formatting-check.yml
name: Code Formatting Check

on: [pull_request, push]

jobs:
  formatting:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Check Python formatting
        run: |
          pip install black isort
          black --check ipcore_lib/ scripts/
          isort --check-only ipcore_lib/ scripts/

      - name: Check TypeScript formatting
        run: |
          cd ipcore_tools/vscode/ipcore_editor
          npm ci
          npm run format:check
          npm run lint
```

## Special Cases and Exceptions

### 1. YAML in Python Test Fixtures

**Problem**: Python uses 4-space indentation, YAML uses 2-space

**Solution**: Disable EditorConfig checker for specific files

**Implementation**:

```python
"""Test module docstring."""

# editorconfig-checker-disable-file
# This file contains YAML fixtures that use 2-space indentation per YAML standard

def test_yaml_parsing():
    yaml_content = """
apiVersion: v1
data:
  key: value
"""
```

**Files Affected**:
- `ipcore_lib/tests/parser/test_yaml_parser.py`

### 2. Documentation with Code Examples

**Problem**: Markdown docs contain code examples with specific indentation

**Solution**: Disable EditorConfig checker for documentation files

**Implementation**:

```markdown
<!-- editorconfig-checker-disable-file -->
<!-- This file contains YAML examples with 2-space indentation per YAML standard -->

# Documentation Title

Example YAML:
```yaml
key:
  nested: value
```
```

**Files Affected**:
- `ipcore_spec/docs/IP_YAML_SPEC.md`
- `ipcore_spec/examples/led/README.md`

### 3. Generated Files

**Problem**: Code generators may produce non-standard formatting

**Solution**: Exclude from formatting tools

**Implementation**:
- Add to `.prettierignore`
- Add to Black's `extend-exclude` in `pyproject.toml`
- Not committed to repository (in `.gitignore`)

### 4. Third-party Code

**Problem**: Vendored/copied code from external sources

**Solution**: Preserve original formatting

**Implementation**:
- Document in comments
- Exclude from formatters
- Consider submodules instead

## Configuration File Reference

### Root Level

```
ipcore/
├── .editorconfig                 # Baseline formatting rules
├── .pre-commit-config.yaml       # Pre-commit hooks
├── pyproject.toml                # Black, isort, pytest config
└── .husky/
    └── pre-commit                # Git hook for VSCode extension
```

### VSCode Extension

```
ipcore_tools/vscode/ipcore_editor/
├── .prettierrc.js                # Prettier configuration
├── .prettierignore               # Files to skip
├── .eslintrc.json                # ESLint rules
├── package.json                  # NPM scripts, lint-staged
└── tsconfig.json                 # TypeScript compiler options
```

### Python Tools (pyproject.toml)

```toml
[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']

[tool.isort]
profile = "black"
line_length = 100

[tool.pytest.ini_options]
# Test configuration (separate concern)
```

## Tool Version Management

### Python Tools

**Managed by**: `uv` (Python package manager)

**Version Pinning**: Specified in pre-commit config

```yaml
- repo: https://github.com/psf/black
  rev: 25.12.0                    # Pinned version
```

**Update Process**:

```bash
pre-commit autoupdate              # Update all hooks
uv pip install --upgrade black isort  # Update local tools
```

### Node Tools

**Managed by**: `npm` / `package.json`

**Version Pinning**: `package.json` dependencies

```json
{
  "devDependencies": {
    "prettier": "^4.0.0-alpha.8",
    "eslint": "^8.x.x"
  }
}
```

**Update Process**:

```bash
cd ipcore_tools/vscode/ipcore_editor
npm update                         # Update within semver ranges
npm outdated                       # Check for major updates
```

## Performance Considerations

### Pre-commit Hook Performance

**Optimization Strategies**:
1. **Incremental Execution**: Only run on staged files
2. **Caching**: Pre-commit framework caches environments
3. **Parallel Execution**: Independent hooks run in parallel
4. **Skip on Amend**: `SKIP=hook-id git commit --amend`

**Typical Execution Times**:
- Small change (1-3 files): 2-5 seconds
- Medium change (10-20 files): 5-10 seconds
- Large change (50+ files): 10-30 seconds

**Bottlenecks**:
- Black: Python AST parsing (slowest)
- Prettier: Multi-language support
- editorconfig-checker: File traversal

### Editor Integration Performance

**VS Code**:
- Format on save: <100ms for typical files
- Large files (>1000 lines): 500ms-2s
- Async formatting (non-blocking)

**Optimization**:
- Format only modified ranges (where supported)
- Disable for very large files
- Use keyboard shortcut instead of save

## Debugging and Troubleshooting

### Enable Verbose Output

```bash
# Pre-commit verbose mode
pre-commit run --verbose --all-files

# Specific hook verbose
pre-commit run black --verbose
```

### Check Hook Installation

```bash
pre-commit --version
pre-commit run --all-files --show-diff-on-failure
```

### Manual Hook Execution

```bash
# Run Black manually
uv run black --check ipcore_lib/

# Run Prettier manually
cd ipcore_tools/vscode/ipcore_editor
npx prettier --check "src/**/*.{ts,tsx}"
```

### Bypass Hooks (Emergency Only)

```bash
# Skip all hooks
git commit --no-verify -m "emergency commit"

# Disable hooks temporarily
pre-commit uninstall
# ... do work ...
pre-commit install
```

## Design Decisions

### Why Black for Python?

**Rationale**:
- Opinionated (fewer debates)
- Fast and reliable
- Widely adopted in Python community
- Compatible with most Python versions
- Minimal configuration needed

**Alternatives Considered**: autopep8, yapf

### Why Prettier for TypeScript?

**Rationale**:
- De facto standard for TypeScript/React
- Multi-language support (YAML, JSON, etc.)
- Good VSCode integration
- Fast and reliable
- Active development

**Alternatives Considered**: tslint (deprecated), dprint

### Why Pre-commit Framework?

**Rationale**:
- Language-agnostic
- Consistent interface across tools
- Built-in caching and performance optimization
- Large ecosystem of hooks
- Easy to add/remove tools

**Alternatives Considered**: Husky alone, custom shell scripts

### Why Not Format in CI Only?

**Rationale**:
- Faster feedback (catch issues before push)
- Reduces CI failures
- Keeps formatting out of PR diffs
- Better developer experience

**Tradeoff**: Requires local setup

## Future Enhancements

### Planned

1. **CI/CD Integration**: GitHub Actions for PR validation
2. **Pre-push Hooks**: Additional validation before push
3. **VHDL Formatting**: When suitable formatter available
4. **Commit Message Linting**: Conventional commits validation

### Under Consideration

1. **Type Checking**: mypy for Python, stricter TypeScript
2. **Security Scanning**: bandit, safety checks
3. **Complexity Metrics**: radon, code climate
4. **Documentation Coverage**: docstring validation

## Maintenance

### Regular Tasks

**Monthly**:
- Update tool versions: `pre-commit autoupdate`
- Review new formatter features
- Check for deprecations

**Quarterly**:
- Review formatting rules
- Gather team feedback
- Update documentation

**Annually**:
- Evaluate new tools
- Consider rule changes
- Major version upgrades

### Version Compatibility Matrix

| Tool | Current Version | Python Support | Node Support |
|------|----------------|----------------|--------------|
| Black | 25.12.0 | 3.8-3.13 | N/A |
| isort | 7.0.0 | 3.8+ | N/A |
| Prettier | 4.0.0-alpha.8 | N/A | 18+ |
| pre-commit | 4.5.1 | 3.8+ | N/A |

## References

- [EditorConfig Specification](https://editorconfig.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [Prettier Documentation](https://prettier.io/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
