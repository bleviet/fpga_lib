# fpga_lib/core/ip_core.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Union
from .interface import Interface, AXILiteInterface, AXIStreamInterface

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

    def add_port(self, name: str, direction: str, data_type: str, width: int = 1):
        """
        Adds a port to the IP core.
        """
        self.ports.append({"name": name, "direction": direction, "type": data_type, "width": width})

    def add_parameter(self, name: str, value: Any, data_type: str = None):
        """
        Adds a parameter to the IP core.
        """
        self.parameters[name] = {"value": value, "type": data_type}

    def add_interface(self, interface: Interface):
        """
        Adds an interface to the IP core and merges its signals with the IP core's ports.
        """
        # interface._create_default_signals()  # Ensure default signals are created - REMOVE THIS LINE
        for signal in interface.signals:
            # Check for duplicate port names and handle them (e.g., raise an error or rename the signal)
            if any(port["name"] == signal["name"] for port in self.ports):
                raise ValueError(f"Duplicate port name: {signal['name']}")  # Raise an error for now
            self.ports.append(signal)
        self.interfaces.append(interface)

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