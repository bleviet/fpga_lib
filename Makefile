# ipcore_lib Makefile
# Provides convenient commands for testing and development

# Default target
.DEFAULT_GOAL := help

.PHONY: help test test-all test-verbose test-coverage clean install install-dev
.PHONY: test-vhdl test-verilog test-core test-generator test-parser test-roundtrip
.PHONY: test-vhdl-parser test-verilog-parser test-vhdl-generator test-ip-core
.PHONY: lint format format-check type-check quality tox build
.PHONY: discover list-tests run-examples test-summary run-demos list-scripts
.PHONY: workspace-info test-collect examples-gpio examples-register

help:
	@echo "ipcore_lib Makefile Commands:"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test              - Run all tests"
	@echo "  make test-all          - Run all tests (alias for test)"
	@echo "  make test-verbose      - Run all tests with verbose output"
	@echo "  make test-coverage     - Run tests with coverage reporting"
	@echo "  make tox               - Run tests in multiple Python versions"
	@echo ""
	@echo "Individual Test Modules:"
	@echo "  make test-core         - Run IP core tests"
	@echo "  make test-parser       - Run all parser tests"
	@echo "  make test-generator    - Run all generator tests"
	@echo "  make test-roundtrip    - Run HDL roundtrip tests"
	@echo ""
	@echo "Specific Parser Tests:"
	@echo "  make test-vhdl-parser  - Run VHDL parser tests"
	@echo "  make test-verilog-parser - Run Verilog parser tests"
	@echo ""
	@echo "Specific Generator Tests:"
	@echo "  make test-vhdl-generator - Run VHDL generator tests"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  make lint              - Run code linting (flake8)"
	@echo "  make format            - Format code with black"
	@echo "  make type-check        - Run type checking with mypy"
	@echo "  make quality           - Run all quality checks"
	@echo ""
	@echo "Development Commands:"
	@echo "  make install           - Install package in editable mode"
	@echo "  make install-dev       - Install package with development dependencies"
	@echo "  make clean             - Remove Python cache files"
	@echo "  make build             - Build distribution packages"
	@echo ""
	@echo "Discovery & Navigation Commands:"
	@echo "  make discover          - Discover all scripts and tests in workspace"
	@echo "  make list-tests        - List all test files and their test functions"
	@echo "  make list-scripts      - List all Python scripts with descriptions"
	@echo "  make run-examples      - Run all example scripts"
	@echo "  make run-demos         - Run all demo scripts"
	@echo "  make test-summary      - Show test file statistics"
	@echo "  make workspace-info    - Show complete workspace information"
	@echo "  make test-collect      - Show all discoverable tests (without running)"
	@echo ""
	@echo "Example-specific Commands:"
	@echo "  make examples-gpio     - Run all GPIO examples"
	@echo "  make examples-register - Run all register examples"
	@echo
	@echo ""
	@echo "Usage Examples:"
	@echo "  make test              # Quick test run"
	@echo "  make test-vhdl-parser  # Test only VHDL parsing"
	@echo "  make test-coverage     # Check test coverage"
	@echo "  make discover          # Find all scripts and tests"
	@echo "  make run-examples      # Execute all example scripts"

# Main test commands
test:
	python -m pytest

test-all: test

test-verbose:
	python -m pytest -v

test-coverage:
	python -m pytest --cov=ipcore_lib --cov-report=term-missing

# Individual test modules
test-core:
	python -m pytest ipcore_lib/tests/core/ -v

test-parser:
	python -m pytest ipcore_lib/tests/parser/ -v

test-generator:
	python -m pytest ipcore_lib/tests/generator/ -v

test-roundtrip:
	python -m pytest ipcore_lib/tests/parser/hdl/test_hdl_roundtrip.py -v

# Specific parser tests
test-vhdl-parser:
	python -m pytest ipcore_lib/tests/parser/hdl/test_vhdl_parser.py -v

test-verilog-parser:
	python -m pytest ipcore_lib/tests/parser/hdl/test_verilog_parser.py -v

# Specific generator tests
test-vhdl-generator:
	python -m pytest ipcore_lib/tests/generator/hdl/test_vhdl_generator.py -v

# Specific core tests
test-ip-core:
	python -m pytest ipcore_lib/tests/core/test_ip_core.py -v

# Development commands
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Advanced test commands
test-specific:
	@echo "Usage: make test-file FILE=path/to/test_file.py"
	@echo "Example: make test-file FILE=ipcore_lib/tests/core/test_ip_core.py"

test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify FILE parameter"; \
		echo "Usage: make test-file FILE=path/to/test_file.py"; \
		exit 1; \
	fi
	python -m pytest $(FILE) -v

test-method:
	@echo "Usage: make test-method FILE=path/to/test_file.py METHOD=TestClass::test_method"
	@echo "Example: make test-method FILE=ipcore_lib/tests/core/test_ip_core.py METHOD=TestIPCore::test_ipcore_creation"

test-method-run:
	@if [ -z "$(FILE)" ] || [ -z "$(METHOD)" ]; then \
		echo "Error: Please specify both FILE and METHOD parameters"; \
		echo "Usage: make test-method-run FILE=path/to/test_file.py METHOD=TestClass::test_method"; \
		exit 1; \
	fi
	python -m pytest $(FILE)::$(METHOD) -v

# Quick status check
status:
	@echo "Running quick test to check if everything is working..."
	python -m pytest ipcore_lib/tests/core/test_ip_core.py::TestIPCore::test_ipcore_creation -v

# NEORV32 specific tests (based on your recent work)
test-neorv32:
	python -m pytest ipcore_lib/tests/parser/hdl/test_vhdl_parser.py::TestVHDLParser::test_parse_neorv32_cfs_with_generics -v
	python -m pytest ipcore_lib/tests/parser/hdl/test_hdl_roundtrip.py -k "neorv32_top" -v

test-generics:
	python -m pytest ipcore_lib/tests/parser/hdl/test_vhdl_parser.py::TestVHDLParser::test_parse_entity_with_generics -v
	python -m pytest ipcore_lib/tests/parser/hdl/test_vhdl_parser.py::TestVHDLParser::test_parse_neorv32_cfs_with_generics -v

# Code quality commands
lint:
	flake8 ipcore_lib

format:
	black ipcore_lib

format-check:
	black --check ipcore_lib

type-check:
	mypy ipcore_lib

quality: lint format-check type-check
	@echo "All quality checks passed!"

# Advanced development commands
tox:
	tox

build:
	python -m build

# Discovery and Navigation Commands
discover:
	@echo "=== IPCORE WORKSPACE DISCOVERY ==="
	@echo ""
	@echo "📁 DIRECTORY STRUCTURE:"
	@echo "  Core Library:     ipcore_lib/"
	@echo "  Examples:         examples/"
	@echo "  Tests:            ipcore_lib/tests/"
	@echo "  Documentation:    docs/"
	@echo ""
	@echo "🐍 EXECUTABLE SCRIPTS:"
	@find ./examples -name "*.py" -type f -not -path "*/.venv/*" | sort | while read file; do \
		echo "  $$file"; \
		head -n 10 "$$file" | grep -E '""".*"""' | head -1 | sed 's/"""//g' | sed 's/^/    /'; \
	done
	@echo ""
	@echo "🧪 TEST FILES:"
	@find . -name "test_*.py" -not -path "./.pytest_cache/*" -not -path "*/.venv/*" | sort | while read file; do \
		echo "  $$file"; \
	done
	@echo ""
	@echo "📚 DEMO SCRIPTS:"
	@find . -name "*demo*.py" -not -path "./.pytest_cache/*" -not -path "*/.venv/*" | sort

list-tests:
	@echo "=== ALL TEST FUNCTIONS ==="
	@find . -name "test_*.py" -not -path "./.pytest_cache/*" -not -path "*/.venv/*" | sort | while read file; do \
		echo ""; \
		echo "📁 $$file:"; \
		python -m pytest --collect-only "$$file" 2>/dev/null | grep -E "test_[a-zA-Z0-9_]*" | sed 's/^/  /' || echo "  (No tests found)"; \
	done

list-scripts:
	@echo "=== ALL PYTHON SCRIPTS WITH DESCRIPTIONS ==="
	@find . -name "*.py" -not -path "./.pytest_cache/*" -not -path "./__pycache__/*" -not -path "*/.venv/*" | sort | while read file; do \
		echo ""; \
		echo "📄 $$file"; \
		head -n 15 "$$file" | grep -A 10 '"""' | grep -B 10 '"""' | grep -v '"""' | head -3 | sed 's/^/  /' || echo "  (No description available)"; \
	done

workspace-info:
	@echo "=== COMPLETE WORKSPACE INFORMATION ==="
	@echo ""
	@echo "📊 STATISTICS:"
	@echo "  Total Python files: $$(find . -name '*.py' -not -path './.pytest_cache/*' -not -path './__pycache__/*' -not -path '*/.venv/*' | wc -l)"
	@echo "  Test files:         $$(find . -name 'test_*.py' -not -path '*/.venv/*' | wc -l)"
	@echo "  Example scripts:    $$(find ./examples -name '*.py' -type f -not -path '*/.venv/*' | wc -l)"
	@echo "  Core modules:       $$(find ./ipcore_lib -name '*.py' -not -name 'test_*' -not -path '*/.venv/*' | wc -l)"
	@echo ""
	@echo "📁 MODULE BREAKDOWN:"
	@echo "  Core tests:         $$(find ./ipcore_lib/tests/core -name 'test_*.py' -not -path '*/.venv/*' | wc -l) files"
	@echo "  Parser tests:       $$(find ./ipcore_lib/tests/parser -name 'test_*.py' -not -path '*/.venv/*' | wc -l) files"
	@echo "  Generator tests:    $$(find ./ipcore_lib/tests/generator -name 'test_*.py' -not -path '*/.venv/*' | wc -l) files"
	@echo "  GPIO examples:      $$(find ./examples/gpio -name '*.py' -not -path '*/.venv/*' | wc -l) files"
	@echo "  Register examples:  $$(find ./examples/register -name '*.py' -not -path '*/.venv/*' | wc -l) files"

test-collect:
	@echo "=== DISCOVERABLE TESTS (WITHOUT RUNNING) ==="
	@python -m pytest --collect-only -q

test-summary:
	@echo "=== TEST SUMMARY ==="
	@echo "Total test files: $$(find . -name 'test_*.py' | wc -l)"
	@echo "Core tests:       $$(find ./ipcore_lib/tests/core -name 'test_*.py' | wc -l)"
	@echo "Parser tests:     $$(find ./ipcore_lib/tests/parser -name 'test_*.py' | wc -l)"
	@echo "Generator tests:  $$(find ./ipcore_lib/tests/generator -name 'test_*.py' | wc -l)"
	@echo ""
	@echo "Running quick test collection..."
	@python -m pytest --collect-only 2>/dev/null | grep -E "(test_[a-zA-Z0-9_]*|collected [0-9]+ item)" | tail -1

run-examples:
	@echo "=== RUNNING ALL EXAMPLE SCRIPTS ==="
	@find ./examples -name "*.py" -type f -not -path "*/.venv/*" | sort | while read script; do \
		echo ""; \
		echo "🚀 Running $$script..."; \
		echo ""; \
		cd "$$(dirname "$$script")" && python "$$(basename "$$script")" && echo "✅ Completed successfully" || echo "❌ Failed"; \
		cd - > /dev/null; \
		echo ""; \
	done

run-demos:
	@echo "=== RUNNING ALL DEMO SCRIPTS ==="
	@find . -name "*demo*.py" -not -path "./.pytest_cache/*" | sort | while read script; do \
		echo ""; \
		echo "🎯 Running $$script..."; \
		echo ""; \
		cd "$$(dirname "$$script")" && python "$$(basename "$$script")" && echo "✅ Completed successfully" || echo "❌ Failed"; \
		cd - > /dev/null; \
		echo ""; \
	done

# Example-specific commands
examples-gpio:
	@echo "=== RUNNING GPIO EXAMPLES ==="
	@cd examples/gpio && echo "🎯 Running GPIO demo..." && python demo.py
	@echo ""
	@cd examples/gpio && echo "🎯 Running YAML demo..." && python yaml_demo.py
	@echo ""
	@cd examples/gpio && echo "🎯 Running GPIO examples..." && python examples.py
	@echo ""
	@cd examples/gpio && echo "🎯 Running GPIO tests..." && python test_gpio.py

examples-register:
	@echo "=== RUNNING REGISTER EXAMPLES ==="
	@cd examples/register && echo "🎯 Running register basics..." && python register_basics.py
	@echo ""
	@cd examples/register && echo "🎯 Running multi IP core demo..." && python multi_ip_core_demo.py
	@echo ""
	@cd examples/register && echo "🎯 Running register array example..." && python register_array_example.py
	@echo ""
	@cd examples/register && echo "🎯 Running core classes test..." && python test_core_classes.py
