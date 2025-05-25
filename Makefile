# fpga_lib Makefile
# Provides convenient commands for testing and development

# Default target
.DEFAULT_GOAL := help

.PHONY: help test test-all test-verbose test-coverage clean install install-dev
.PHONY: test-vhdl test-verilog test-core test-generator test-parser test-roundtrip
.PHONY: test-vhdl-parser test-verilog-parser test-vhdl-generator test-ip-core
.PHONY: lint format format-check type-check quality tox build

help:
	@echo "fpga_lib Makefile Commands:"
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
	@echo
	@echo ""
	@echo "Usage Examples:"
	@echo "  make test              # Quick test run"
	@echo "  make test-vhdl-parser  # Test only VHDL parsing"
	@echo "  make test-coverage     # Check test coverage"

# Main test commands
test:
	python -m pytest

test-all: test

test-verbose:
	python -m pytest -v

test-coverage:
	python -m pytest --cov=fpga_lib --cov-report=term-missing

# Individual test modules
test-core:
	python -m pytest fpga_lib/tests/core/ -v

test-parser:
	python -m pytest fpga_lib/tests/parser/ -v

test-generator:
	python -m pytest fpga_lib/tests/generator/ -v

test-roundtrip:
	python -m pytest fpga_lib/tests/parser/hdl/test_hdl_roundtrip.py -v

# Specific parser tests
test-vhdl-parser:
	python -m pytest fpga_lib/tests/parser/hdl/test_vhdl_parser.py -v

test-verilog-parser:
	python -m pytest fpga_lib/tests/parser/hdl/test_verilog_parser.py -v

# Specific generator tests
test-vhdl-generator:
	python -m pytest fpga_lib/tests/generator/hdl/test_vhdl_generator.py -v

# Specific core tests
test-ip-core:
	python -m pytest fpga_lib/tests/core/test_ip_core.py -v

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
	@echo "Example: make test-file FILE=fpga_lib/tests/core/test_ip_core.py"

test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify FILE parameter"; \
		echo "Usage: make test-file FILE=path/to/test_file.py"; \
		exit 1; \
	fi
	python -m pytest $(FILE) -v

test-method:
	@echo "Usage: make test-method FILE=path/to/test_file.py METHOD=TestClass::test_method"
	@echo "Example: make test-method FILE=fpga_lib/tests/core/test_ip_core.py METHOD=TestIPCore::test_ipcore_creation"

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
	python -m pytest fpga_lib/tests/core/test_ip_core.py::TestIPCore::test_ipcore_creation -v

# NEORV32 specific tests (based on your recent work)
test-neorv32:
	python -m pytest fpga_lib/tests/parser/hdl/test_vhdl_parser.py::TestVHDLParser::test_parse_neorv32_cfs_with_generics -v
	python -m pytest fpga_lib/tests/parser/hdl/test_hdl_roundtrip.py -k "neorv32_top" -v

test-generics:
	python -m pytest fpga_lib/tests/parser/hdl/test_vhdl_parser.py::TestVHDLParser::test_parse_entity_with_generics -v
	python -m pytest fpga_lib/tests/parser/hdl/test_vhdl_parser.py::TestVHDLParser::test_parse_neorv32_cfs_with_generics -v

# Code quality commands
lint:
	flake8 fpga_lib

format:
	black fpga_lib

format-check:
	black --check fpga_lib

type-check:
	mypy fpga_lib

quality: lint format-check type-check
	@echo "All quality checks passed!"

# Advanced development commands
tox:
	tox

build:
	python -m build
