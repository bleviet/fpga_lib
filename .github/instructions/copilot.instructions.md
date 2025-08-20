---
applyTo: '**'
---
# Project-Wide Instructions for GitHub Copilot

## 1\. General Philosophy

Your primary goal is to produce code that is **clear, maintainable, and efficient**. Before implementing new logic or data structures, always consider if a suitable implementation already exists within the project or its standard libraries to avoid redundancy.

## 2\. Python Environment & Execution

  - **Environment Activation**: All Python-related shell commands must be executed within the `dev` conda environment. When providing commands, prefix them appropriately, for example:
    ```bash
    conda run -n dev python my_script.py
    conda run -n dev pytest
    ```

## 3\. Python Code Quality & Style

  - **Formatting**: Strictly adhere to the **PEP 8** style guide. All code should be formatted as if by the **`black`** code formatter.
  - **Type Hinting**: All function and method signatures **must** include type hints. Variables should also be typed where it enhances clarity.
  - **Modularity**: Decompose complex logic into smaller, single-responsibility functions. Aim for functions that are easy to understand and test in isolation.
  - **Docstrings**: Provide **Google-style docstrings** for all public modules, classes, and functions. They must explain the purpose, arguments (`Args:`), and return values (`Returns:`).
  - **Imports**: Organize imports into three groups, separated by a blank line:
    1.  Standard library imports (e.g., `os`, `sys`).
    2.  Third-party library imports (e.g., `requests`, `pandas`).
    3.  Local application/library imports.

## 4\. Documentation & Explanations

  - **Clarity is Key**: Use simple, direct, and concise language.
  - **Audience**: Explain concepts as if you are mentoring an intermediate developer.
  - **Jargon**: Avoid unnecessary jargon. If a technical term is required, define it briefly upon its first use.

## 5\. Error Handling & Security

  - **Exceptions**: Never use a generic `except Exception:`. Always catch specific exceptions (e.g., `ValueError`, `KeyError`).
  - **Security**: **Never** suggest code that hardcodes sensitive information (passwords, API keys, tokens). Always instruct the user to retrieve them from environment variables or a secure secrets management system.

## 6\. Testing

  - **Framework**: All tests must be written using the **`pytest`** framework.
  - **Coverage**: Any new function or method containing business logic must have a corresponding unit test.
  - **Mocking**: Use `unittest.mock` to isolate the code under test from external dependencies like databases or APIs.
