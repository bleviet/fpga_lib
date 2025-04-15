# fpga_lib/core/ip_core.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Union, Optional
from .interface import Interface, AXILiteInterface, AXIStreamInterface
from .data_types import DataType, VectorType
from fpga_lib.core.port import Port, PortDirection

class PortDefault:
    """Optional default value for a port."""
    def __init__(self, value: Any = None):
        self.value = value

@dataclass
class Parameter:
    name: str
    value: Any
    type: Optional[str] = None

@dataclass
class IPCore:
    """
    Base class for IP cores.
    """
    vendor: str = ""
    library: str = ""
    name: str = "generic_ip_core"  # Default IP core name
    version: str = "1.0"
    description: str = ""
    ports: List[Port] = field(default_factory=list)
    parameters: Dict[str, Parameter] = field(default_factory=dict)
    interfaces: List[Interface] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        pass

    def add_port(self, name: str, direction: str, data_type: Union[str, DataType], width: int = 1, default: Any = None):
        """
        Adds a port to the IP core. Supports all VHDL directions and default values.
        Args:
            name (str): The name of the port
            direction (str): The direction of the port ("in", "out", "inout", "buffer")
            data_type (Union[str, DataType]): The data type of the port
            width (int, optional): The bit width of the port. Defaults to 1.
            default (Any, optional): The default value for the port.
        Raises:
            ValueError: If the port direction is invalid or the port name already exists
        """
        valid_directions = [d.value for d in PortDirection] + ["inout", "buffer"]
        if direction.lower() not in valid_directions:
            self.errors.append(f"Invalid port direction: {direction}. Must be one of {valid_directions}.")
            raise ValueError(f"Invalid port direction: {direction}. Must be one of {valid_directions}.")
        # Normalize port name for duplicate check
        norm_name = name.lower()
        if any(port.name.lower() == norm_name for port in self.ports):
            self.errors.append(f"Duplicate port name: {name}")
            raise ValueError(f"Duplicate port name: {name}")
        if isinstance(data_type, VectorType):
            width = data_type.width
        port = Port(name=name, direction=PortDirection(direction.lower()) if direction.lower() in [d.value for d in PortDirection] else direction.lower(), type=data_type, width=width if width else 1)
        port.default = PortDefault(default) if default is not None else None
        self.ports.append(port)

    def add_parameter(self, name: str, value: Any, data_type: str = None):
        """
        Adds a parameter to the IP core using a dataclass for type safety.
        Args:
            name (str): The name of the parameter
            value (Any): The value of the parameter
            data_type (str, optional): The data type of the parameter. Defaults to None.
        Raises:
            ValueError: If the parameter name already exists
        """
        norm_name = name.lower()
        if norm_name in (k.lower() for k in self.parameters):
            self.errors.append(f"Parameter {name} already exists")
            raise ValueError(f"Parameter {name} already exists")
        self.parameters[name] = Parameter(name=name, value=value, type=data_type)

    def add_interface(self, interface: Interface):
        """
        Adds an interface to the IP core and merges its signals with the IP core's ports.
        Args:
            interface (Interface): The interface to add
        Raises:
            ValueError: If there are duplicate port names
        """
        for signal in interface.ports:
            norm_name = signal["name"].lower()
            if any(port.name.lower() == norm_name for port in self.ports):
                self.errors.append(f"Duplicate port name: {signal['name']}")
                raise ValueError(f"Duplicate port name: {signal['name']}")
            self.ports.append(Port(name=signal["name"], direction=PortDirection(signal["direction"].lower()) if signal["direction"].lower() in [d.value for d in PortDirection] else signal["direction"].lower(), type=signal["type"], width=signal["width"]))
        self.interfaces.append(interface)

    def remove_port(self, name: str) -> bool:
        """
        Removes a port from the IP core by name (case-insensitive).
        Args:
            name (str): The name of the port to remove
        Returns:
            bool: True if the port was removed, False if it wasn't found
        """
        norm_name = name.lower()
        for i, port in enumerate(self.ports):
            if port.name.lower() == norm_name:
                self.ports.pop(i)
                return True
        return False

    def modify_port(self, name: str, direction: str = None, data_type: Union[str, DataType] = None, width: int = None, default: Any = None) -> bool:
        """
        Modifies an existing port in the IP core.
        Args:
            name (str): The name of the port to modify
            direction (str, optional): The new direction of the port
            data_type (Union[str, DataType], optional): The new data type of the port
            width (int, optional): The new bit width of the port
            default (Any, optional): The new default value
        Returns:
            bool: True if the port was modified, False if it wasn't found
        Raises:
            ValueError: If the port direction is invalid
        """
        norm_name = name.lower()
        for port in self.ports:
            if port.name.lower() == norm_name:
                if direction is not None:
                    valid_directions = [d.value for d in PortDirection] + ["inout", "buffer"]
                    if direction.lower() not in valid_directions:
                        self.errors.append(f"Invalid port direction: {direction}. Must be one of {valid_directions}.")
                        raise ValueError(f"Invalid port direction: {direction}. Must be one of {valid_directions}.")
                    port.direction = PortDirection(direction.lower()) if direction.lower() in [d.value for d in PortDirection] else direction.lower()
                if data_type is not None:
                    port.type = data_type
                if width is not None:
                    port.width = width
                if default is not None:
                    port.default = PortDefault(default)
                return True
        return False

    def get_port(self, name: str) -> Optional[Port]:
        """
        Gets a port from the IP core by name (case-insensitive).
        Args:
            name (str): The name of the port to get
        Returns:
            Port: The port object, or None if not found
        """
        norm_name = name.lower()
        for port in self.ports:
            if port.name.lower() == norm_name:
                return port
        return None

    def remove_interface(self, interface: Interface) -> bool:
        """
        Removes an interface and its ports from the IP core.
        Args:
            interface (Interface): The interface to remove
        Returns:
            bool: True if the interface was removed, False otherwise
        """
        if interface in self.interfaces:
            # Remove ports associated with this interface
            interface_port_names = {signal["name"].lower() for signal in interface.ports}
            self.ports = [port for port in self.ports if port.name.lower() not in interface_port_names]
            self.interfaces.remove(interface)
            return True
        return False

    def to_dict(self) -> dict:
        """
        Serializes the IP core to a dictionary.
        Returns:
            dict: The serialized IP core
        """
        return {
            "vendor": self.vendor,
            "library": self.library,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "ports": [port.__dict__ for port in self.ports],
            "parameters": {k: v.__dict__ for k, v in self.parameters.items()},
            "interfaces": [str(interface) for interface in self.interfaces],
            "errors": self.errors
        }

# Examples of IP cores with interfaces
@dataclass
class RAM(IPCore):
    """
    RAM IP core.
    """
    depth: int = 1024   # Default depth
    width: int = 32     # Default width
    technology: str = "Generic"
    vendor: str = "my_company"
    library: str = "memory_blocks"
    name: str = "single_port_ram"
    version: str = "2.0"

    def __post_init__(self):
        super().__post_init__()
        address_width = (self.depth - 1).bit_length() if self.depth > 1 else 1
        if not any(port.name == 'clk' for port in self.ports):
            self.add_port("clk", "in", "std_logic")
        if not any(port.name == 'addr' for port in self.ports):
            self.add_port("addr", "in", "std_logic", width=address_width)
        if not any(port.name == 'din' for port in self.ports):
            self.add_port("din", "in", "std_logic_vector", width=self.width)
        if not any(port.name == 'dout' for port in self.ports):
            self.add_port("dout", "out", "std_logic_vector", width=self.width)
        self.add_interface(AXILiteInterface(name="s_axi"))

@dataclass
class FIFO(IPCore):
    """
    FIFO IP core.
    """
    depth: int = 64     # Default depth
    width: int = 8      # Default width
    almost_full_threshold: int = 0
    vendor: str = "my_company"
    library: str = "fifo_blocks"
    name: str = "standard_fifo"
    version: str = "1.1"

    def __post_init__(self):
        super().__post_init__()
        if not any(port.name == 'clk' for port in self.ports):
            self.add_port("clk", "in", "std_logic")
        if not any(port.name == 'wr_en' for port in self.ports):
            self.add_port("wr_en", "in", "std_logic")
        if not any(port.name == 'rd_en' for port in self.ports):
            self.add_port("rd_en", "in", "std_logic")
        if not any(port.name == 'din' for port in self.ports):
            self.add_port("din", "in", "std_logic_vector", width=self.width)
        if not any(port.name == 'dout' for port in self.ports):
            self.add_port("dout", "out", "std_logic_vector", width=self.width)
        if not any(port.name == 'full' for port in self.ports):
            self.add_port("full", "out", "std_logic")
        if not any(port.name == 'empty' for port in self.ports):
            self.add_port("empty", "out", "std_logic")
        self.add_interface(AXIStreamInterface(name="s_axis"))
        self.add_interface(AXIStreamInterface(name="m_axis"))