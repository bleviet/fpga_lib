<!-- editorconfig-checker-disable-file -->
<!-- This file contains code examples with various indentation styles for documentation purposes -->

# Code Formatting Guide

> Developer guide for code formatting standards and tools in the ipcore project

## Quick Start

### For Python Development

```bash
# Format your Python code
uv run black ipcore_lib/ scripts/
uv run isort ipcore_lib/ scripts/

# Or let pre-commit hooks do it automatically on commit
git commit -m "your message"
```

### For TypeScript/VSCode Extension Development

```bash
cd ipcore_tools/vscode/ipcore_editor

# Format all TypeScript files
npm run format

# Check formatting without making changes
npm run format:check

# Fix all formatting and linting issues
npm run fix-all
```

## Overview

This project uses automated code formatting to maintain consistent code style across all contributions. Formatting is enforced through:

1. **EditorConfig** - Baseline formatting rules for all editors
2. **Language-specific formatters** - Black (Python), Prettier (TypeScript/JS/YAML)
3. **Pre-commit hooks** - Automatic formatting on git commit
4. **Import sorting** - isort (Python), ESLint (TypeScript)

## Formatting Standards

### Python (`.py` files)

- **Formatter**: [Black](https://black.readthedocs.io/)
- **Import Sorter**: [isort](https://pycqa.github.io/isort/)
- **Line Length**: 100 characters
- **Indentation**: 4 spaces (PEP 8)
- **Target Python**: 3.8 - 3.12

**Configuration**: `pyproject.toml`

```toml
[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']

[tool.isort]
profile = "black"
line_length = 100
```

### TypeScript/JavaScript (`.ts`, `.tsx`, `.js`, `.jsx` files)

- **Formatter**: [Prettier](https://prettier.io/)
- **Linter**: ESLint
- **Indentation**: 2 spaces
- **Line Length**: 100 characters
- **Quotes**: Single quotes
- **Semicolons**: Required
- **Trailing Commas**: ES5 compatible

**Configuration**: `ipcore_tools/vscode/ipcore_editor/.prettierrc.js`

```javascript
module.exports = {
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  printWidth: 100,
  tabWidth: 2,
  useTabs: false,
  arrowParens: 'always',
  endOfLine: 'lf',
};
```

### YAML (`.yml`, `.yaml` files)

- **Formatter**: Prettier
- **Indentation**: 2 spaces (YAML standard)
- **Line Length**: 100 characters

### JSON (`.json` files)

- **Formatter**: Prettier
- **Indentation**: 2 spaces
- **Trailing Commas**: Not allowed (JSON standard)

### Other Files

- **Makefile**: Tabs (required by Make)
- **Markdown**: 4 spaces, no trailing whitespace trimming on lines
- **Line Endings**: LF (`\n`) for all files
- **Encoding**: UTF-8
- **Trailing Whitespace**: Trimmed automatically (except Markdown)
- **Final Newline**: Required for all files

## Pre-commit Hooks

Pre-commit hooks automatically format your code when you commit. They're configured in `.pre-commit-config.yaml`.

### Installation

Pre-commit hooks are installed automatically if you use `uv` or if you run:

```bash
uv run pre-commit install
# or
pip install pre-commit
pre-commit install
```

### What Hooks Do

1. **trailing-whitespace**: Remove trailing spaces
2. **end-of-file-fixer**: Ensure files end with newline
3. **check-yaml**: Validate YAML syntax
4. **check-added-large-files**: Prevent large file commits
5. **mixed-line-ending**: Enforce LF line endings
6. **black**: Format Python code
7. **isort**: Sort Python imports
8. **prettier**: Format TypeScript/JS/YAML/JSON
9. **editorconfig-checker**: Verify EditorConfig compliance

### Manual Execution

Run hooks on all files:

```bash
pre-commit run --all-files
```

Run specific hook:

```bash
pre-commit run black --all-files
pre-commit run prettier --all-files
```

Skip hooks (not recommended):

```bash
git commit --no-verify -m "message"
```

## Editor Setup

### VS Code

Install these extensions:

1. **EditorConfig for VS Code** (`editorconfig.editorconfig`)
2. **Python** (`ms-python.python`)
3. **Black Formatter** (`ms-python.black-formatter`)
4. **isort** (`ms-python.isort`)
5. **Prettier** (`esbenp.prettier-vscode`)
6. **ESLint** (`dbaeumer.vscode-eslint`)

**Settings** (`.vscode/settings.json`):

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "python.formatting.provider": "black",
  "isort.check": true
}
```

### PyCharm / IntelliJ IDEA

1. Install **EditorConfig** plugin (usually built-in)
2. Configure Black:
   - Settings → Tools → Black
   - Enable "Run Black on save"
3. Configure isort:
   - Settings → Tools → Python Integrated Tools → isort
   - Enable isort

### Vim / Neovim

Install plugins:

```vim
" Using vim-plug
Plug 'editorconfig/editorconfig-vim'
Plug 'psf/black', { 'branch': 'stable' }
Plug 'prettier/vim-prettier'

" Configure auto-format
autocmd BufWritePre *.py execute ':Black'
autocmd BufWritePre *.ts,*.tsx,*.js,*.jsx,*.json,*.yaml,*.yml execute ':Prettier'
```

## Special Cases

### YAML Test Fixtures in Python Files

Some Python test files contain multiline YAML strings. These use 2-space indentation (YAML standard) even though they're in Python files (which normally use 4 spaces).

**Example**: `ipcore_lib/tests/parser/test_yaml_parser.py`

These files have `# editorconfig-checker-disable-file` at the top to prevent EditorConfig violations.

### Markdown Documentation with Code Examples

Documentation files containing code examples with specific indentation requirements have EditorConfig checking disabled:

```markdown
<!-- editorconfig-checker-disable-file -->
<!-- This file contains YAML examples with 2-space indentation per YAML standard -->
```

## Troubleshooting

### Pre-commit hooks are failing

**Check installed tools**:

```bash
# Check Python tools
uv run black --version
uv run isort --version

# Check Node tools
cd ipcore_tools/vscode/ipcore_editor
npx prettier --version
```

**Update pre-commit hooks**:

```bash
pre-commit autoupdate
pre-commit install --install-hooks
```

### Files keep getting reformatted

This is expected behavior. Commit the formatted files:

```bash
git add -u
git commit -m "style: Apply automated formatting"
```

### Conflicts with existing code style

Automated formatting has been applied to the entire codebase. If you see formatting changes:

1. Pull latest changes: `git pull origin <branch>`
2. Let pre-commit hooks format your changes
3. Resolve any merge conflicts
4. Commit the results

### Black and isort disagree on imports

This shouldn't happen - isort is configured with `profile = "black"` for compatibility. If it does:

1. Update both tools: `pip install --upgrade black isort`
2. Check `pyproject.toml` configuration
3. Run isort after black: `black . && isort .`

### EditorConfig violations in YAML

If you see "Wrong amount of left-padding spaces" errors for YAML:

- YAML uses 2-space indentation (standard)
- Python uses 4-space indentation
- For YAML test fixtures in Python files, add `# editorconfig-checker-disable-file`

## NPM Scripts (VSCode Extension)

```bash
cd ipcore_tools/vscode/ipcore_editor

# Format all files
npm run format

# Check formatting without changes
npm run format:check

# Fix linting issues
npm run lint:fix

# Run all checks
npm run check-all

# Fix all issues
npm run fix-all
```

**Available scripts**:

| Script | Description |
|--------|-------------|
| `format` | Format TypeScript/TSX with Prettier |
| `format:check` | Check formatting without changes |
| `lint` | Run ESLint checks |
| `lint:fix` | Fix ESLint issues automatically |
| `check-all` | Run format check + lint + type check |
| `fix-all` | Run format + lint:fix |
| `compile` | Compile TypeScript to JavaScript |
| `watch` | Compile in watch mode |

## Best Practices

### Before Starting Work

```bash
# Update to latest code
git pull origin <branch>

# Install/update pre-commit hooks
pre-commit install
```

### During Development

- Let your editor format on save
- Don't worry about formatting - tools handle it
- Focus on code logic and structure

### Before Committing

```bash
# Pre-commit hooks run automatically
git add <files>
git commit -m "message"

# Or manually format everything
pre-commit run --all-files
```

### Reviewing PRs

- Ignore formatting changes in diffs
- Focus on logic and functionality
- Formatting is enforced automatically

## Related Documentation

- [Architecture Documentation](./FORMATTING_ARCHITECTURE.md) - Technical implementation details
- [EditorConfig Specification](../.editorconfig) - Baseline formatting rules
- [Python Configuration](../pyproject.toml) - Black and isort settings
- [Pre-commit Configuration](../.pre-commit-config.yaml) - Hook configuration

## Getting Help

**Formatting issues?**
1. Check this guide
2. Review [FORMATTING_ARCHITECTURE.md](./FORMATTING_ARCHITECTURE.md)
3. Ask in team chat or create an issue

**Want to change formatting rules?**
1. Discuss with team first
2. Update configuration files
3. Run `pre-commit run --all-files` on entire codebase
4. Submit PR with justification
