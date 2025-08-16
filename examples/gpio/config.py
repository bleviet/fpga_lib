"""
Configuration and Factory Module

This module implements the unified factory and configuration system
described in the concept document. It provides a clean interface for
creating GPIO drivers with different bus backends.
"""

from dataclasses import dataclass
from typing import Any, Union, Optional
from gpio_driver import GpioDriver
from bus_interface import AbstractBusInterface, MockBusInterface
from bus_backends import (
    SimulationBusInterface,
    JtagBusInterface,
    PCIeBusInterface,
    EthernetBusInterface
)


@dataclass
class MockBusConfig:
    """Configuration for mock bus interface (testing)."""
    pass


@dataclass
class SimulationBusConfig:
    """Configuration for simulation bus interface (cocotb)."""
    dut: Any
    bus_name: str
    clock: Any


@dataclass
class JtagBusConfig:
    """Configuration for JTAG bus interface (hardware)."""
    jtag_session: Any
    chain_position: int = 0


@dataclass
class PCIeBusConfig:
    """Configuration for PCIe bus interface (high-speed hardware)."""
    device_path: str


@dataclass
class EthernetBusConfig:
    """Configuration for Ethernet bus interface (remote hardware)."""
    host: str
    port: int
    protocol: str = "tcp"


# Union type for all possible bus configurations
BusConfig = Union[
    MockBusConfig,
    SimulationBusConfig,
    JtagBusConfig,
    PCIeBusConfig,
    EthernetBusConfig
]


@dataclass
class GpioDriverConfig:
    """
    Complete configuration for GPIO driver creation.

    Attributes:
        bus_type: Type of bus interface ("mock", "simulation", "jtag", "pcie", "ethernet")
        bus_config: Bus-specific configuration
        num_pins: Number of GPIO pins (default: 32)
        base_address: Base address of GPIO registers (default: 0x0)
    """
    bus_type: str
    bus_config: BusConfig
    num_pins: int = 32
    base_address: int = 0x0


def create_bus_interface(bus_type: str, bus_config: BusConfig) -> AbstractBusInterface:
    """
    Factory function to create the appropriate bus interface.

    Args:
        bus_type: Type of bus interface to create
        bus_config: Configuration for the bus interface

    Returns:
        Concrete bus interface instance

    Raises:
        ValueError: If bus_type is not supported
        TypeError: If bus_config doesn't match bus_type
    """
    bus_type = bus_type.lower()

    if bus_type == "mock":
        if not isinstance(bus_config, MockBusConfig):
            raise TypeError(f"Expected MockBusConfig for bus_type 'mock', got {type(bus_config)}")
        return MockBusInterface()

    elif bus_type == "simulation":
        if not isinstance(bus_config, SimulationBusConfig):
            raise TypeError(f"Expected SimulationBusConfig for bus_type 'simulation', got {type(bus_config)}")
        return SimulationBusInterface(
            dut=bus_config.dut,
            bus_name=bus_config.bus_name,
            clock=bus_config.clock
        )

    elif bus_type == "jtag":
        if not isinstance(bus_config, JtagBusConfig):
            raise TypeError(f"Expected JtagBusConfig for bus_type 'jtag', got {type(bus_config)}")
        return JtagBusInterface(
            jtag_session=bus_config.jtag_session,
            chain_position=bus_config.chain_position
        )

    elif bus_type == "pcie":
        if not isinstance(bus_config, PCIeBusConfig):
            raise TypeError(f"Expected PCIeBusConfig for bus_type 'pcie', got {type(bus_config)}")
        return PCIeBusInterface(device_path=bus_config.device_path)

    elif bus_type == "ethernet":
        if not isinstance(bus_config, EthernetBusConfig):
            raise TypeError(f"Expected EthernetBusConfig for bus_type 'ethernet', got {type(bus_config)}")
        return EthernetBusInterface(
            host=bus_config.host,
            port=bus_config.port,
            protocol=bus_config.protocol
        )

    else:
        supported_types = ["mock", "simulation", "jtag", "pcie", "ethernet"]
        raise ValueError(f"Unsupported bus_type '{bus_type}'. Supported types: {supported_types}")


def create_gpio_driver(config: GpioDriverConfig) -> GpioDriver:
    """
    Factory function to create a GPIO driver with the specified configuration.

    This is the main factory function that users should call to create
    GPIO driver instances. It handles all the complexity of creating
    the appropriate bus interface and configuring the driver.

    Args:
        config: Complete configuration for the GPIO driver

    Returns:
        Configured GPIO driver instance

    Example:
        # Create a mock driver for testing
        config = GpioDriverConfig(
            bus_type="mock",
            bus_config=MockBusConfig(),
            num_pins=16
        )
        driver = create_gpio_driver(config)

        # Create a simulation driver for cocotb
        config = GpioDriverConfig(
            bus_type="simulation",
            bus_config=SimulationBusConfig(
                dut=dut,
                bus_name="s_axi",
                clock=dut.aclk
            )
        )
        driver = create_gpio_driver(config)

        # Create a JTAG driver for hardware
        config = GpioDriverConfig(
            bus_type="jtag",
            bus_config=JtagBusConfig(jtag_session=xsdb_session)
        )
        driver = create_gpio_driver(config)
    """
    # Create the appropriate bus interface
    bus_interface = create_bus_interface(config.bus_type, config.bus_config)

    # Create and return the GPIO driver
    return GpioDriver(
        bus=bus_interface,
        num_pins=config.num_pins,
        base_address=config.base_address
    )


# Convenience functions for common configurations

def create_mock_gpio_driver(num_pins: int = 32, base_address: int = 0) -> GpioDriver:
    """
    Create a mock GPIO driver for testing.

    Args:
        num_pins: Number of GPIO pins
        base_address: Base address of GPIO registers

    Returns:
        GPIO driver with mock bus interface
    """
    config = GpioDriverConfig(
        bus_type="mock",
        bus_config=MockBusConfig(),
        num_pins=num_pins,
        base_address=base_address
    )
    return create_gpio_driver(config)


def create_simulation_gpio_driver(dut: Any, bus_name: str, clock: Any,
                                 num_pins: int = 32, base_address: int = 0) -> GpioDriver:
    """
    Create a simulation GPIO driver for cocotb testbenches.

    Args:
        dut: The DUT object from cocotb
        bus_name: Name of the bus interface in the DUT
        clock: Clock signal for synchronization
        num_pins: Number of GPIO pins
        base_address: Base address of GPIO registers

    Returns:
        GPIO driver with simulation bus interface
    """
    config = GpioDriverConfig(
        bus_type="simulation",
        bus_config=SimulationBusConfig(dut=dut, bus_name=bus_name, clock=clock),
        num_pins=num_pins,
        base_address=base_address
    )
    return create_gpio_driver(config)


def create_jtag_gpio_driver(jtag_session: Any, chain_position: int = 0,
                           num_pins: int = 32, base_address: int = 0) -> GpioDriver:
    """
    Create a JTAG GPIO driver for hardware access.

    Args:
        jtag_session: JTAG session object
        chain_position: Position in the JTAG chain
        num_pins: Number of GPIO pins
        base_address: Base address of GPIO registers

    Returns:
        GPIO driver with JTAG bus interface
    """
    config = GpioDriverConfig(
        bus_type="jtag",
        bus_config=JtagBusConfig(jtag_session=jtag_session, chain_position=chain_position),
        num_pins=num_pins,
        base_address=base_address
    )
    return create_gpio_driver(config)


def create_pcie_gpio_driver(device_path: str, num_pins: int = 32, base_address: int = 0) -> GpioDriver:
    """
    Create a PCIe GPIO driver for high-speed hardware access.

    Args:
        device_path: Path to the PCIe device
        num_pins: Number of GPIO pins
        base_address: Base address of GPIO registers

    Returns:
        GPIO driver with PCIe bus interface
    """
    config = GpioDriverConfig(
        bus_type="pcie",
        bus_config=PCIeBusConfig(device_path=device_path),
        num_pins=num_pins,
        base_address=base_address
    )
    return create_gpio_driver(config)


def create_ethernet_gpio_driver(host: str, port: int, protocol: str = "tcp",
                               num_pins: int = 32, base_address: int = 0) -> GpioDriver:
    """
    Create an Ethernet GPIO driver for remote hardware access.

    Args:
        host: Hostname or IP address
        port: Port number
        protocol: Communication protocol ("tcp" or "udp")
        num_pins: Number of GPIO pins
        base_address: Base address of GPIO registers

    Returns:
        GPIO driver with Ethernet bus interface
    """
    config = GpioDriverConfig(
        bus_type="ethernet",
        bus_config=EthernetBusConfig(host=host, port=port, protocol=protocol),
        num_pins=num_pins,
        base_address=base_address
    )
    return create_gpio_driver(config)
