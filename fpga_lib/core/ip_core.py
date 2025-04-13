# fpga_lib/core/ip_core.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Union
from .interface import Interface, AXILiteInterface, AXIStreamInterface
from .data_types import DataType
from fpga_lib.utils.port_utils import PortDirection

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
    ports: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    interfaces: List[Interface] = field(default_factory=list)

    def __post_init__(self):
        pass

    def add_port(self, name: str, direction: str, data_type: Union[str, DataType], width: int = 1):
        """
        Adds a port to the IP core.
        
        Args:
            name (str): The name of the port
            direction (str): The direction of the port ("in" or "out")
            data_type (Union[str, DataType]): The data type of the port
            width (int, optional): The bit width of the port. Defaults to 1.
            
        Raises:
            ValueError: If the port direction is invalid or the port name already exists
        """
        # Validate direction
        if direction.lower() not in [PortDirection.IN.lower(), PortDirection.OUT.lower()]:
            raise ValueError(f"Invalid port direction: {direction}. Must be 'in' or 'out'.")
            
        # Check for duplicate port names
        if any(port["name"] == name for port in self.ports):
            raise ValueError(f"Duplicate port name: {name}")
            
        self.ports.append({"name": name, "direction": direction, "type": data_type, "width": width})

    def add_parameter(self, name: str, value: Any, data_type: str = None):
        """
        Adds a parameter to the IP core.
        
        Args:
            name (str): The name of the parameter
            value (Any): The value of the parameter
            data_type (str, optional): The data type of the parameter. Defaults to None.
            
        Raises:
            ValueError: If the parameter name already exists
        """
        if name in self.parameters:
            raise ValueError(f"Parameter {name} already exists")
            
        self.parameters[name] = {"value": value, "type": data_type}

    def add_interface(self, interface: Interface):
        """
        Adds an interface to the IP core and merges its signals with the IP core's ports.
        
        Args:
            interface (Interface): The interface to add
            
        Raises:
            ValueError: If there are duplicate port names
        """
        for signal in interface.ports:
            # Check for duplicate port names and handle them
            if any(port["name"] == signal["name"] for port in self.ports):
                raise ValueError(f"Duplicate port name: {signal['name']}")
            self.ports.append(signal)
        self.interfaces.append(interface)
        
    def remove_port(self, name: str) -> bool:
        """
        Removes a port from the IP core.
        
        Args:
            name (str): The name of the port to remove
            
        Returns:
            bool: True if the port was removed, False if it wasn't found
        """
        for i, port in enumerate(self.ports):
            if port["name"] == name:
                self.ports.pop(i)
                return True
        return False
        
    def modify_port(self, name: str, direction: str = None, data_type: Union[str, DataType] = None, width: int = None) -> bool:
        """
        Modifies an existing port in the IP core.
        
        Args:
            name (str): The name of the port to modify
            direction (str, optional): The new direction of the port
            data_type (Union[str, DataType], optional): The new data type of the port
            width (int, optional): The new bit width of the port
            
        Returns:
            bool: True if the port was modified, False if it wasn't found
            
        Raises:
            ValueError: If the port direction is invalid
        """
        for port in self.ports:
            if port["name"] == name:
                if direction is not None:
                    if direction.lower() not in [PortDirection.IN.lower(), PortDirection.OUT.lower()]:
                        raise ValueError(f"Invalid port direction: {direction}. Must be 'in' or 'out'.")
                    port["direction"] = direction
                if data_type is not None:
                    port["type"] = data_type
                if width is not None:
                    port["width"] = width
                return True
        return False

    def get_port(self, name: str) -> Dict[str, Any]:
        """
        Gets a port from the IP core by name.
        
        Args:
            name (str): The name of the port to get
            
        Returns:
            Dict[str, Any]: The port dictionary, or None if not found
        """
        for port in self.ports:
            if port["name"] == name:
                return port
        return None

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
        if not any(port['name'] == 'clk' for port in self.ports):
            self.add_port("clk", "in", "std_logic")
        if not any(port['name'] == 'addr' for port in self.ports):
            self.add_port("addr", "in", "std_logic", width=address_width)
        if not any(port['name'] == 'din' for port in self.ports):
            self.add_port("din", "in", "std_logic_vector", width=self.width)
        if not any(port['name'] == 'dout' for port in self.ports):
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
        if not any(port['name'] == 'clk' for port in self.ports):
            self.add_port("clk", "in", "std_logic")
        if not any(port['name'] == 'wr_en' for port in self.ports):
            self.add_port("wr_en", "in", "std_logic")
        if not any(port['name'] == 'rd_en' for port in self.ports):
            self.add_port("rd_en", "in", "std_logic")
        if not any(port['name'] == 'din' for port in self.ports):
            self.add_port("din", "in", "std_logic_vector", width=self.width)
        if not any(port['name'] == 'dout' for port in self.ports):
            self.add_port("dout", "out", "std_logic_vector", width=self.width)
        if not any(port['name'] == 'full' for port in self.ports):
            self.add_port("full", "out", "std_logic")
        if not any(port['name'] == 'empty' for port in self.ports):
            self.add_port("empty", "out", "std_logic")
        self.add_interface(AXIStreamInterface(name="s_axis"))
        self.add_interface(AXIStreamInterface(name="m_axis"))