# Testing VHDL AI Parser

This document provides instructions for testing the pure LLM-based VHDL parser.

## Quick Start

### Run All Tests (Excluding Integration)
```bash
cd /home/balevision/workspace/bleviet/ipcore_lib
pytest ipcore_lib/tests/test_vhdl_ai_parser.py -v -m "not integration and not slow"
```

### Run All Tests (Including Integration, Requires Ollama)
```bash
pytest ipcore_lib/tests/test_vhdl_ai_parser.py -v -m "not slow"
```

### Run Specific Test Categories
```bash
# Basic entity parsing
pytest ipcore_lib/tests/test_vhdl_ai_parser.py::TestBasicEntityParsing -v

# Port parsing
pytest ipcore_lib/tests/test_vhdl_ai_parser.py::TestPortParsing -v

# Generic/parameter extraction
pytest ipcore_lib/tests/test_vhdl_ai_parser.py::TestGenericParsing -v

# Complex expressions
pytest ipcore_lib/tests/test_vhdl_ai_parser.py::TestComplexExpressions -v

# Bus interface detection
pytest ipcore_lib/tests/test_vhdl_ai_parser.py::TestBusInterfaceDetection -v

# Error handling
pytest ipcore_lib/tests/test_vhdl_ai_parser.py::TestErrorHandling -v

# Model validation
pytest ipcore_lib/tests/test_vhdl_ai_parser.py::TestModelValidation -v
```

## Test Structure

### Test Categories

1. **TestBasicEntityParsing** (3 tests)
   - Entity name extraction
   - Description generation
   - Basic parsing validation

2. **TestPortParsing** (4 tests)
   - Port name extraction
   - Port direction detection
   - Port width calculation
   - Multiple port types

3. **TestGenericParsing** (3 tests)
   - Simple generic extraction
   - Multiple generics with different types
   - Generic default values

4. **TestComplexExpressions** (4 tests)
   - Simple subtraction (WIDTH-1)
   - Power-of-2 expressions (2**N)
   - Division expressions (WIDTH/8)
   - Complex nested expressions

5. **TestBusInterfaceDetection** (5 tests)
   - AXI4-Lite detection
   - AXI-Stream detection
   - SPI detection
   - Wishbone detection
   - No false positives

6. **TestErrorHandling** (3 tests)
   - Non-existent file handling
   - Strict mode error raising
   - Graceful degradation

7. **TestModelValidation** (3 tests)
   - Pydantic model validation
   - VLNV structure
   - Port model validation

8. **TestPerformance** (2 tests, marked `@pytest.mark.slow`)
   - Simple entity parsing time
   - Complex entity parsing time
   - Requires: `pytest-benchmark`

9. **TestIntegration** (3 tests, marked `@pytest.mark.integration`)
   - Ollama provider integration
   - OpenAI provider integration (requires API key)
   - Gemini provider integration (requires API key)

## Test Files Used

Tests use VHDL files from `examples/test_vhdl/`:

| File | Purpose | Features |
|------|---------|----------|
| `simple_counter.vhd` | Basic parsing | 1 generic, 4 ports, simple subtraction |
| `uart_transmitter.vhd` | Multiple generics | 5 generics, 6 ports, division expression |
| `fifo_buffer.vhd` | Power-of-2 expressions | 2 generics, 8 ports, 2**N expression |
| `spi_master.vhd` | SPI bus detection | 4 generics, 10 ports, SPI signals |
| `axi_stream_filter.vhd` | AXI-Stream detection | 2 generics, 10 ports, dual interfaces |
| `pwm_generator.vhd` | Multi-channel | 2 generics, 8 ports, 4 PWM channels |
| `wishbone_slave.vhd` | Wishbone detection | 3 generics, 11 ports, wb_* signals |
| `axi_example_peripheral.vhd` | AXI4-Lite detection | 24 ports, complex expressions |

## Requirements

### Basic Tests
- Python 3.11+
- `pytest`
- `ipcore_lib` package installed
- Ollama running locally (for default tests)

### Performance Tests
```bash
pip install pytest-benchmark
```

### Integration Tests

**Ollama** (default):
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start server
ollama serve

# Pull model
ollama pull gemma3:12b
```

**OpenAI** (optional):
```bash
export OPENAI_API_KEY=your-key-here
```

**Gemini** (optional):
```bash
export GEMINI_API_KEY=your-key-here
```

## Running Specific Tests

### Run a Single Test
```bash
pytest ipcore_lib/tests/test_vhdl_ai_parser.py::TestBasicEntityParsing::test_simple_counter_parsing -v
```

### Run Tests with Coverage
```bash
pytest ipcore_lib/tests/test_vhdl_ai_parser.py --cov=ipcore_lib.parser.hdl --cov-report=html
```

### Run Only Fast Tests
```bash
pytest ipcore_lib/tests/test_vhdl_ai_parser.py -v -m "not slow and not integration"
```

### Run Only Integration Tests
```bash
pytest ipcore_lib/tests/test_vhdl_ai_parser.py -v -m integration
```

### Run Performance Benchmarks
```bash
pytest ipcore_lib/tests/test_vhdl_ai_parser.py -v -m slow --benchmark-only
```

## Expected Results

### All Non-Integration Tests (25 tests)
```
========================== test session starts ==========================
collected 30 items / 3 deselected / 27 selected

ipcore_lib/tests/test_vhdl_ai_parser.py::TestBasicEntityParsing::test_simple_counter_parsing PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestBasicEntityParsing::test_entity_name_extraction PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestBasicEntityParsing::test_description_generation PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestPortParsing::test_simple_counter_ports PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestPortParsing::test_port_directions PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestPortParsing::test_port_widths PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestPortParsing::test_uart_transmitter_ports PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestGenericParsing::test_simple_counter_generic PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestGenericParsing::test_uart_transmitter_generics PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestGenericParsing::test_fifo_buffer_generics PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestComplexExpressions::test_simple_subtraction PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestComplexExpressions::test_power_of_two PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestComplexExpressions::test_division_expression PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestComplexExpressions::test_axi_division_expression PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestBusInterfaceDetection::test_axi4_lite_detection PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestBusInterfaceDetection::test_axi_stream_detection PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestBusInterfaceDetection::test_spi_detection PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestBusInterfaceDetection::test_wishbone_detection PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestBusInterfaceDetection::test_no_bus_interface PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestErrorHandling::test_nonexistent_file PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestErrorHandling::test_strict_mode_on_failure PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestErrorHandling::test_graceful_degradation_on_failure PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestModelValidation::test_valid_ip_core_model PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestModelValidation::test_vlnv_structure PASSED
ipcore_lib/tests/test_vhdl_ai_parser.py::TestModelValidation::test_port_model_validation PASSED

========================== 25 passed, 5 skipped in 180.45s ==========================
```

## Troubleshooting

### "Ollama not available"
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull model
ollama pull gemma3:12b
```

### "Test files not found"
```bash
# Verify test files exist
ls -la examples/test_vhdl/*.vhd

# Check from project root
cd /home/balevision/workspace/bleviet/ipcore_lib
```

### Slow Test Execution
- Each LLM call takes 20-40 seconds
- Use `-m "not slow"` to skip performance tests
- Consider using faster model: `llama3.2:latest`

### Import Errors
```bash
# Reinstall ipcore_lib in development mode
pip install -e .
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run VHDL Parser Tests
  run: |
    pytest ipcore_lib/tests/test_vhdl_ai_parser.py -v \
      -m "not integration and not slow" \
      --junitxml=test-results.xml
```

### GitLab CI Example
```yaml
test:
  script:
    - pip install -e .
    - pytest ipcore_lib/tests/test_vhdl_ai_parser.py -v \
        -m "not integration and not slow"
  artifacts:
    when: always
    reports:
      junit: test-results.xml
```

## Test Development

### Adding New Tests

1. **Choose appropriate test class** based on what you're testing
2. **Use fixtures** for parser and test directory
3. **Follow naming convention**: `test_feature_name`
4. **Add docstring** explaining what is being tested
5. **Use markers** for slow or integration tests

### Test Template
```python
def test_new_feature(self, parser, test_vhdl_dir):
    """Test description."""
    # Arrange
    vhdl_file = test_vhdl_dir / "test_file.vhd"
    
    # Act
    ip_core = parser.parse_file(vhdl_file)
    
    # Assert
    assert ip_core.vlnv.name == "expected_name"
    assert len(ip_core.ports) == expected_count
```

### Using Markers
```python
@pytest.mark.slow
def test_performance_feature(self, parser, test_vhdl_dir):
    """Test that takes a long time."""
    pass

@pytest.mark.integration
def test_with_real_api(self, test_vhdl_dir):
    """Test with real LLM API."""
    pass
```

## Coverage

### Generate Coverage Report
```bash
pytest ipcore_lib/tests/test_vhdl_ai_parser.py \
    --cov=ipcore_lib.parser.hdl.vhdl_ai_parser \
    --cov-report=html \
    --cov-report=term
```

### View HTML Report
```bash
open htmlcov/index.html
```

## Debugging Tests

### Verbose Output
```bash
pytest ipcore_lib/tests/test_vhdl_ai_parser.py -vv
```

### Show Print Statements
```bash
pytest ipcore_lib/tests/test_vhdl_ai_parser.py -s
```

### Stop on First Failure
```bash
pytest ipcore_lib/tests/test_vhdl_ai_parser.py -x
```

### Run Failed Tests
```bash
pytest ipcore_lib/tests/test_vhdl_ai_parser.py --lf
```

### Debug with pdb
```bash
pytest ipcore_lib/tests/test_vhdl_ai_parser.py --pdb
```

## Related Documentation

- **Test VHDL Files**: `examples/test_vhdl/README.md`
- **Parser Documentation**: `docs/PURE_LLM_PARSER.md`
- **Migration Guide**: `docs/LLM_PARSER_MIGRATION.md`
- **Architecture**: `docs/plan.md`
