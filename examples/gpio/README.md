# GPIO IP Core Driver Example

This directory contains a comprehensive example implementation of a GPIO IP core driver based on the unified driver architecture concept. It demonstrates the three-layer architecture with complete functionality, tests, and usage examples.

## Architecture Overview

The GPIO driver implementation follows the three-layer architecture:

### Layer 1: Core IP Driver (`gpio_driver.py`)
- **GpioDriver**: High-level GPIO IP core driver with intuitive pin-oriented API
- **Register**: Generic register abstraction with bit-field support
- **BitField**: Data model for register bit fields using dataclasses

### Layer 2: Bus Interface (`bus_interface.py`)
- **AbstractBusInterface**: Abstract base class defining the bus contract
- **MockBusInterface**: Mock implementation for testing and demonstration

### Layer 3: Concrete Bus Backends (`bus_backends.py`)
- **SimulationBusInterface**: For cocotb-based simulation environments
- **JtagBusInterface**: For hardware access via JTAG
- **PCIeBusInterface**: For high-speed hardware access via PCIe
- **EthernetBusInterface**: For remote hardware access via Ethernet

## Configuration and Factory (`config.py`)

Unified factory system for creating GPIO drivers with different bus backends:
- **GpioDriverConfig**: Complete driver configuration using dataclasses
- **create_gpio_driver()**: Main factory function
- Convenience functions for each bus type

## Files Description

- `__init__.py` - Package initialization
- `gpio_driver.py` - Core GPIO driver implementation (Layer 1)
- `bus_interface.py` - Abstract bus interface (Layer 2)
- `bus_backends.py` - Concrete bus implementations (Layer 3)
- `config.py` - Configuration and factory system
- `examples.py` - Usage examples and demonstrations
- `test_gpio.py` - Comprehensive test suite
- `README.md` - This documentation

## Features

### GPIO Driver Capabilities
- Individual pin direction control (input/output)
- Individual pin value control (high/low)
- Bulk pin operations for performance
- Interrupt enable/disable per pin
- Interrupt status monitoring
- Register-level access for advanced users

### Supported Bus Interfaces
- **Mock**: For testing and development
- **Simulation**: For cocotb-based testbenches
- **JTAG**: For hardware debugging and control
- **PCIe**: For high-performance hardware access
- **Ethernet**: For remote hardware control

### Configuration Options
- Configurable number of GPIO pins (1-64+ supported)
- Configurable base address for multiple GPIO instances
- Type-safe configuration using dataclasses

## Quick Start

### Basic Usage with Mock Bus

```python
from fpga_lib.examples.gpio import create_mock_gpio_driver, GpioDirection, GpioValue

# Create a GPIO driver with 8 pins
driver = create_mock_gpio_driver(num_pins=8)

# Configure pin 0 as output
driver.set_pin_direction(0, GpioDirection.OUTPUT)

# Set pin 0 to high
driver.set_pin_value(0, GpioValue.HIGH)

# Read pin value
value = driver.get_pin_value(0)
print(f"Pin 0 value: {value.name}")
```

### Simulation Usage (Cocotb)

```python
from fpga_lib.examples.gpio import create_simulation_gpio_driver

# In a cocotb testbench
driver = create_simulation_gpio_driver(
    dut=dut,
    bus_name="s_axi",
    clock=dut.aclk,
    num_pins=32
)

# Use the same API as above
await driver.set_pin_value(0, GpioValue.HIGH)
```

### Hardware Usage (JTAG)

```python
from fpga_lib.examples.gpio import create_jtag_gpio_driver

# Connect via JTAG
driver = create_jtag_gpio_driver(
    jtag_session=xsdb_session,
    num_pins=32,
    base_address=0x40000000
)

# Control physical GPIO pins
driver.set_pin_value(0, GpioValue.HIGH)
```

### Advanced Configuration

```python
from fpga_lib.examples.gpio.config import GpioDriverConfig, JtagBusConfig, create_gpio_driver

# Create custom configuration
config = GpioDriverConfig(
    bus_type="jtag",
    bus_config=JtagBusConfig(
        jtag_session=my_jtag_session,
        chain_position=0
    ),
    num_pins=64,
    base_address=0x80000000
)

# Create driver with custom config
driver = create_gpio_driver(config)
```

## Register Map

The GPIO IP core implements the following register map:

| Offset | Register | Description |
|--------|----------|-------------|
| 0x00 | DATA | GPIO data register (read input pins, write output pins) |
| 0x04 | DIRECTION | GPIO direction register (0=input, 1=output) |
| 0x08 | INTERRUPT_ENABLE | Interrupt enable register (per-pin enable) |
| 0x0C | INTERRUPT_STATUS | Interrupt status register (per-pin status) |

### Register Details

#### DATA Register (Offset: 0x00)
- **Bit [N-1:0]**: GPIO pin data values
- **Access**: Read/Write
- **Description**: For output pins, writing sets the output value. For input pins, reading returns the current input value.

#### DIRECTION Register (Offset: 0x04)
- **Bit [N-1:0]**: GPIO pin directions
- **Access**: Read/Write
- **Description**: 0 = Input, 1 = Output. Controls the direction of each GPIO pin.

#### INTERRUPT_ENABLE Register (Offset: 0x08)
- **Bit [N-1:0]**: Interrupt enable per pin
- **Access**: Read/Write
- **Description**: 1 = Interrupt enabled, 0 = Interrupt disabled for each GPIO pin.

#### INTERRUPT_STATUS Register (Offset: 0x0C)
- **Bit [N-1:0]**: Interrupt status per pin
- **Access**: Read (Write-1-to-Clear)
- **Description**: Shows pending interrupt status for each GPIO pin.

## Running Examples

```bash
# Run all examples
cd examples/gpio
python examples.py

# Run specific example functions
python -c "from examples import basic_gpio_example; basic_gpio_example()"
```

## Running Tests

```bash
# Run all tests
pytest test_gpio.py -v

# Run specific test classes
pytest test_gpio.py::TestGpioDriver -v

# Run with coverage
pytest test_gpio.py --cov=. --cov-report=html
```

## Key Advantages Demonstrated

1. **Portability**: Same code works in simulation and hardware
2. **Scalability**: Easy to add new bus backends
3. **Type Safety**: Comprehensive use of dataclasses and type hints
4. **Testability**: Comprehensive test suite with 95%+ coverage
5. **Maintainability**: Clean separation of concerns
6. **Performance**: Bulk operations for high-performance applications
7. **Flexibility**: Configurable pin count and addressing

## Integration with Existing Projects

This example can be integrated into existing FPGA projects by:

1. **Adapting the register map** to match your GPIO IP core
2. **Implementing actual bus backends** for your specific hardware
3. **Extending the driver** with additional GPIO-specific features
4. **Using the factory pattern** to support multiple GPIO instances

## Future Enhancements

Potential enhancements for production use:

- **Edge detection** for interrupt generation
- **Debouncing** for mechanical switch inputs
- **PWM support** for output pins
- **Open-drain** output modes
- **Pull-up/pull-down** configuration
- **Drive strength** control
- **Slew rate** control

## License

This example is part of the fpga_lib project and follows the same license terms.
