"""
Configuration and Factory Module

This module implements the updated unified factory and configuration system
based on YAML-driven memory map definitions. It provides a clean interface for
creating IP core drivers with different bus backends.
"""

from dataclasses import dataclass
from typing import Any, Union, Optional
from memory_map_loader import load_from_yaml, IpCoreDriver
from gpio_wrapper import GpioDriverWrapper
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
class DriverConfig:
    """
    Complete configuration for IP core driver creation using YAML memory maps.

    Attributes:
        map_file: Path to the YAML memory map file
        bus_type: Type of bus interface ("mock", "simulation", "jtag", "pcie", "ethernet")
        bus_config: Bus-specific configuration
        driver_name: Optional name for the driver instance
    """
    map_file: str
    bus_type: str
    bus_config: BusConfig
    driver_name: str = "IP Core Driver"
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


def create_ip_core_driver(config: DriverConfig) -> IpCoreDriver:
    """
    Factory function to create an IP core driver with the specified configuration.

    This is the main factory function that users should call to create
    IP core driver instances. It handles all the complexity of creating
    the appropriate bus interface and loading the memory map from YAML.

    Args:
        config: Complete configuration for the IP core driver

    Returns:
        Configured IP core driver instance loaded from YAML

    Example:
        # Create a mock driver for testing
        config = DriverConfig(
            map_file="gpio_memory_map.yaml",
            bus_type="mock",
            bus_config=MockBusConfig(),
            driver_name="GPIO Test Driver"
        )
        driver = create_ip_core_driver(config)

        # Create a simulation driver for cocotb
        config = DriverConfig(
            map_file="gpio_memory_map.yaml",
            bus_type="simulation",
            bus_config=SimulationBusConfig(
                dut=dut,
                bus_name="s_axi",
                clock=dut.aclk
            )
        )
        driver = create_ip_core_driver(config)

        # Create a JTAG driver for hardware
        config = DriverConfig(
            map_file="gpio_memory_map.yaml",
            bus_type="jtag",
            bus_config=JtagBusConfig(jtag_session=xsdb_session)
        )
        driver = create_ip_core_driver(config)
    """
    # Create the appropriate bus interface
    bus_interface = create_bus_interface(config.bus_type, config.bus_config)

    # Load the driver from YAML memory map
    return load_from_yaml(config.map_file, bus_interface, config.driver_name)


# Convenience functions for GPIO-specific drivers (with wrapper)

def create_mock_gpio_driver(map_file: str = "gpio_memory_map.yaml",
                           driver_name: str = "Mock GPIO Driver") -> GpioDriverWrapper:
    """
    Create a mock GPIO driver for testing.

    Args:
        map_file: Path to the GPIO memory map YAML file
        driver_name: Name for the driver instance

    Returns:
        GPIO driver wrapper with mock bus interface
    """
    ip_driver = create_mock_ip_driver(map_file, driver_name)

    # Initialize mock bus with sensible default values for GPIO config
    if hasattr(ip_driver, 'config'):
        try:
            # Set default config values that make sense for a 32-pin GPIO
            # pin_count=32, has_interrupts=1, version=0x01, enable=1
            default_config = 32 | (1 << 8) | (0x01 << 16) | (1 << 31)
            ip_driver._bus.write_word(0x14, default_config)  # Config register offset
        except Exception:
            pass  # If anything fails, just continue with defaults

    return GpioDriverWrapper(ip_driver)


def create_simulation_gpio_driver(dut: Any, bus_name: str, clock: Any,
                                 map_file: str = "gpio_memory_map.yaml",
                                 driver_name: str = "Simulation GPIO Driver") -> GpioDriverWrapper:
    """
    Create a simulation GPIO driver for cocotb testbenches.

    Args:
        dut: The DUT object from cocotb
        bus_name: Name of the bus interface in the DUT
        clock: Clock signal for synchronization
        map_file: Path to the GPIO memory map YAML file
        driver_name: Name for the driver instance

    Returns:
        GPIO driver wrapper with simulation bus interface
    """
    ip_driver = create_simulation_ip_driver(dut, bus_name, clock, map_file, driver_name)
    return GpioDriverWrapper(ip_driver)


def create_jtag_gpio_driver(jtag_session: Any, chain_position: int = 0,
                           map_file: str = "gpio_memory_map.yaml",
                           driver_name: str = "JTAG GPIO Driver") -> GpioDriverWrapper:
    """
    Create a JTAG GPIO driver for hardware access.

    Args:
        jtag_session: JTAG session object
        chain_position: Position in the JTAG chain
        map_file: Path to the GPIO memory map YAML file
        driver_name: Name for the driver instance

    Returns:
        GPIO driver wrapper with JTAG bus interface
    """
    ip_driver = create_jtag_ip_driver(jtag_session, chain_position, map_file, driver_name)
    return GpioDriverWrapper(ip_driver)


def create_pcie_gpio_driver(device_path: str,
                           map_file: str = "gpio_memory_map.yaml",
                           driver_name: str = "PCIe GPIO Driver") -> GpioDriverWrapper:
    """
    Create a PCIe GPIO driver for high-speed hardware access.

    Args:
        device_path: Path to the PCIe device
        map_file: Path to the GPIO memory map YAML file
        driver_name: Name for the driver instance

    Returns:
        GPIO driver wrapper with PCIe bus interface
    """
    ip_driver = create_pcie_ip_driver(device_path, map_file, driver_name)
    return GpioDriverWrapper(ip_driver)


def create_ethernet_gpio_driver(host: str, port: int, protocol: str = "tcp",
                               map_file: str = "gpio_memory_map.yaml",
                               driver_name: str = "Ethernet GPIO Driver") -> GpioDriverWrapper:
    """
    Create an Ethernet GPIO driver for remote hardware access.

    Args:
        host: Hostname or IP address
        port: Port number
        protocol: Communication protocol ("tcp" or "udp")
        map_file: Path to the GPIO memory map YAML file
        driver_name: Name for the driver instance

    Returns:
        GPIO driver wrapper with Ethernet bus interface
    """
    ip_driver = create_ethernet_ip_driver(host, port, protocol, map_file, driver_name)
    return GpioDriverWrapper(ip_driver)


# Convenience functions for raw IP core drivers (without GPIO wrapper)

def create_mock_ip_driver(map_file: str = "gpio_memory_map.yaml",
                         driver_name: str = "Mock IP Driver") -> IpCoreDriver:
    """Create a mock IP core driver for testing."""
    config = DriverConfig(
        map_file=map_file,
        bus_type="mock",
        bus_config=MockBusConfig(),
        driver_name=driver_name
    )
    return create_ip_core_driver(config)


def create_simulation_ip_driver(dut: Any, bus_name: str, clock: Any,
                               map_file: str = "gpio_memory_map.yaml",
                               driver_name: str = "Simulation IP Driver") -> IpCoreDriver:
    """Create a simulation IP core driver for cocotb testbenches."""
    config = DriverConfig(
        map_file=map_file,
        bus_type="simulation",
        bus_config=SimulationBusConfig(dut=dut, bus_name=bus_name, clock=clock),
        driver_name=driver_name
    )
    return create_ip_core_driver(config)


def create_jtag_ip_driver(jtag_session: Any, chain_position: int = 0,
                         map_file: str = "gpio_memory_map.yaml",
                         driver_name: str = "JTAG IP Driver") -> IpCoreDriver:
    """Create a JTAG IP core driver for hardware access."""
    config = DriverConfig(
        map_file=map_file,
        bus_type="jtag",
        bus_config=JtagBusConfig(jtag_session=jtag_session, chain_position=chain_position),
        driver_name=driver_name
    )
    return create_ip_core_driver(config)


def create_pcie_ip_driver(device_path: str,
                         map_file: str = "gpio_memory_map.yaml",
                         driver_name: str = "PCIe IP Driver") -> IpCoreDriver:
    """Create a PCIe IP core driver for high-speed hardware access."""
    config = DriverConfig(
        map_file=map_file,
        bus_type="pcie",
        bus_config=PCIeBusConfig(device_path=device_path),
        driver_name=driver_name
    )
    return create_ip_core_driver(config)


def create_ethernet_ip_driver(host: str, port: int, protocol: str = "tcp",
                             map_file: str = "gpio_memory_map.yaml",
                             driver_name: str = "Ethernet IP Driver") -> IpCoreDriver:
    """Create an Ethernet IP core driver for remote hardware access."""
    config = DriverConfig(
        map_file=map_file,
        bus_type="ethernet",
        bus_config=EthernetBusConfig(host=host, port=port, protocol=protocol),
        driver_name=driver_name
    )
    return create_ip_core_driver(config)