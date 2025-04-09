# fpga_lib/core/ip_core.py
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class IPCore:
    vendor: str = ""           # Vendor des IP Cores
    library: str = ""          # Bibliothek, zu der der IP Core gehört
    name: str = ""
    version: str = "1.0"
    description: str = ""
    ports: List[Dict[str, Any]] = None
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.ports is None:
            self.ports = []
        if self.parameters is None:
            self.parameters = {}

    def add_port(self, name: str, direction: str, data_type: str, width: int = 1):
        self.ports.append({"name": name, "direction": direction, "type": data_type, "width": width})

    def add_parameter(self, name: str, value: Any, data_type: str = None):
        self.parameters[name] = {"value": value, "type": data_type}

@dataclass
class RAM(IPCore):
    depth: int = 0
    width: int = 0
    technology: str = "Generic"
    vendor: str = "my_company"
    library: str = "memory_blocks"
    name: str = "single_port_ram"
    version: str = "2.0"

    def __post_init__(self):
        super().__post_init__()
        # Spezifische Initialisierung für RAM, z.B. Hinzufügen von Standard-Ports
        if not any(port['name'] == 'clk' for port in self.ports):
            self.add_port("clk", "input", "logic")
        if not any(port['name'] == 'addr' for port in self.ports):
            self.add_port("addr", "input", "logic", width=(self.depth-1).bit_length() if self.depth > 1 else 1)
        if not any(port['name'] == 'din' for port in self.ports):
            self.add_port("din", "input", "logic", width=self.width)
        if not any(port['name'] == 'dout' for port in self.ports):
            self.add_port("dout", "output", "logic", width=self.width)

@dataclass
class FIFO(IPCore):
    depth: int = 0
    width: int = 0
    almost_full_threshold: int = 0
    vendor: str = "my_company"
    library: str = "fifo_blocks"
    name: str = "standard_fifo"
    version: str = "1.1"

    def __post_init__(self):
        super().__post_init__()
        # Spezifische Initialisierung für FIFO
        if not any(port['name'] == 'clk' for port in self.ports):
            self.add_port("clk", "input", "logic")
        if not any(port['name'] == 'wr_en' for port in self.ports):
            self.add_port("wr_en", "input", "logic")
        if not any(port['name'] == 'rd_en' for port in self.ports):
            self.add_port("rd_en", "input", "logic")
        if not any(port['name'] == 'din' for port in self.ports):
            self.add_port("din", "input", "logic", width=self.width)
        if not any(port['name'] == 'dout' for port in self.ports):
            self.add_port("dout", "output", "logic", width=self.width)
        if not any(port['name'] == 'full' for port in self.ports):
            self.add_port("full", "output", "logic")
        if not any(port['name'] == 'empty' for port in self.ports):
            self.add_port("empty", "output", "logic")