# fpga_lib/core/interface.py
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Interface:
    """
    Base class for all bus interfaces.
    """
    name: str
    interface_type: str
    signals: List[Dict[str, Any]] = field(default_factory=list)  # Add signals attribute

    def __init__(self, name: str, interface_type: str):
        self.name = name
        self.interface_type = interface_type
        self.signals = []  # Initialize signals here

@dataclass
class AXIBaseInterface(Interface):
    """
    Base class for AXI interfaces.
    """
    interface_type: str = "axi"
    address_width: int = 32
    data_width: int = 32
    id_width: int = 1
    user_width: int = 0
    burst_types: List[str] = field(default_factory=lambda: ["FIXED", "INCR"])
    prot_supported: List[str] = field(default_factory=lambda: ["PRIVILEGED", "SECURE", "NONSECURE"])
    cache_supported: List[str] = field(default_factory=lambda: ["BUFFERABLE", "CACHEABLE"])
    qos_supported: bool = False

    def __init__(self, name: str, address_width: int = 32, data_width: int = 32, id_width: int = 1, user_width: int = 0,
                 burst_types: List[str] = field(default_factory=lambda: ["FIXED", "INCR"]),
                 prot_supported: List[str] = field(default_factory=lambda: ["PRIVILEGED", "SECURE", "NONSECURE"]),
                 cache_supported: List[str] = field(default_factory=lambda: ["BUFFERABLE", "CACHEABLE"]),
                 qos_supported: bool = False):
        super().__init__(name, "axi")
        self.address_width = address_width
        self.data_width = data_width
        self.id_width = id_width
        self.user_width = user_width
        self.burst_types = burst_types
        self.prot_supported = prot_supported
        self.cache_supported = cache_supported
        self.qos_supported = qos_supported
        self.signals = []  # Initialize signals here
        self.signals.extend([
            {"name": f"{name}_aclk", "direction": "in", "type": "std_logic"},
            {"name": f"{name}_aresetn", "direction": "in", "type": "std_logic"},
        ])

@dataclass
class AXILiteInterface(AXIBaseInterface):
    """
    AXI Lite interface.
    """
    interface_type: str = "axi_lite"
    burst_types: List[str] = field(default_factory=lambda: [])

    def __init__(self, name: str, address_width: int = 32, data_width: int = 32, id_width: int = 1, user_width: int = 0,
                 burst_types: List[str] = field(default_factory=lambda: []),
                 prot_supported: List[str] = field(default_factory=lambda: ["PRIVILEGED", "SECURE", "NONSECURE"]),
                 cache_supported: List[str] = field(default_factory=lambda: ["BUFFERABLE", "CACHEABLE"]),
                 qos_supported: bool = False):
        super().__init__(name, address_width, data_width, id_width, user_width, burst_types, prot_supported, cache_supported, qos_supported)
        self.signals = [] # Initialize signals here
        self.signals.extend([
            {"name": f"{name}_awaddr", "direction": "in", "type": "std_logic_vector", "width": address_width},
            {"name": f"{name}_awvalid", "direction": "in", "type": "std_logic"},
            {"name": f"{name}_awready", "direction": "out", "type": "std_logic"},
            {"name": f"{name}_wdata", "direction": "in", "type": "std_logic_vector", "width": data_width},
            {"name": f"{name}_wstrb", "direction": "in", "type": "std_logic_vector", "width": data_width // 8},
            {"name": f"{name}_wvalid", "direction": "in", "type": "std_logic"},
            {"name": f"{name}_wready", "direction": "out", "type": "std_logic"},
            {"name": f"{name}_bresp", "direction": "out", "type": "std_logic_vector", "width": 2},
            {"name": f"{name}_bvalid", "direction": "out", "type": "std_logic"},
            {"name": f"{name}_bready", "direction": "in", "type": "std_logic"},
            {"name": f"{name}_araddr", "direction": "in", "type": "std_logic_vector", "width": address_width},
            {"name": f"{name}_arvalid", "direction": "in", "type": "std_logic"},
            {"name": f"{name}_arready", "direction": "out", "type": "std_logic"},
            {"name": f"{name}_rdata", "direction": "out", "type": "std_logic_vector", "width": data_width},
            {"name": f"{name}_rresp", "direction": "out", "type": "std_logic_vector", "width": 2},
            {"name": f"{name}_rvalid", "direction": "out", "type": "std_logic"},
            {"name": f"{name}_rready", "direction": "in", "type": "std_logic"},
        ])

@dataclass
class AXIStreamInterface(AXIBaseInterface):
    """
    AXI Stream interface.
    """
    interface_type: str = "axi_stream"
    data_width: int = 8
    user_width: int = 1
    tdest_width: int = 1
    tid_width: int = 1
    tkeep_enable: bool = False
    tlast_enable: bool = False
    tstrb_enable: bool = False
    tuser_enable: bool = False

    def __init__(self, name: str, address_width: int = 32, data_width: int = 8, id_width: int = 1, user_width: int = 1,
                 burst_types: List[str] = field(default_factory=lambda: ["FIXED", "INCR"]),
                 prot_supported: List[str] = field(default_factory=lambda: ["PRIVILEGED", "SECURE", "NONSECURE"]),
                 cache_supported: List[str] = field(default_factory=lambda: ["BUFFERABLE", "CACHEABLE"]),
                 qos_supported: bool = False,
                 tdest_width: int = 1, tid_width: int = 1, tkeep_enable: bool = False,
                 tlast_enable: bool = False, tstrb_enable: bool = False, tuser_enable: bool = False):
        super().__init__(name, address_width, data_width, id_width, user_width, burst_types, prot_supported, cache_supported, qos_supported)
        self.data_width = data_width
        self.user_width = user_width
        self.tdest_width = tdest_width
        self.tid_width = tid_width
        self.tkeep_enable = tkeep_enable
        self.tlast_enable = tlast_enable
        self.tstrb_enable = tstrb_enable
        self.tuser_enable = tuser_enable
        self.signals = []  # Initialize signals here
        self.signals.extend([
            {"name": f"{name}_tdata", "direction": "in", "type": "std_logic_vector", "width": data_width},
            {"name": f"{name}_tvalid", "direction": "in", "type": "std_logic"},
            {"name": f"{name}_tready", "direction": "out", "type": "std_logic"},
            {"name": f"{name}_tlast", "direction": "in", "type": "std_logic"},
            {"name": f"{name}_tuser", "direction": "in", "type": "std_logic_vector", "width": user_width},
            {"name": f"{name}_tstrb", "direction": "in", "type": "std_logic_vector", "width": data_width // 8},
            {"name": f"{name}_tkeep", "direction": "in", "type": "std_logic_vector", "width": data_width // 8},
            {"name": f"{name}_tid", "direction": "in", "type": "std_logic_vector", "width": tid_width},
            {"name": f"{name}_tdest", "direction": "in", "type": "std_logic_vector", "width": tdest_width},
        ])