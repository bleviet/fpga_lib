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

@dataclass
class AXILiteInterface(AXIBaseInterface):
    """
    AXI Lite interface.
    """
    interface_type: str = "axi_lite"
    burst_types: List[str] = field(default_factory=lambda: [])

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

@dataclass
class AvalonBaseInterface(Interface):
    """
    Base class for Avalon interfaces.
    """
    interface_type: str = "avalon"
    address_width: int = 32
    data_width: int = 32

@dataclass
class AvalonMMInterface(AvalonBaseInterface):
    """
    Avalon Memory-Mapped interface.
    """
    interface_type: str = "avalon_mm"
    read_wait_time: int = 1
    write_wait_time: int = 1
    burst_count_width: int = 1
    constant_burst_behavior: bool = False

@dataclass
class AvalonSTInterface(AvalonBaseInterface):
    """
    Avalon Streaming interface.
    """
    interface_type: str = "avalon_st"
    data_width: int = 8
    ready_latency: int = 0
    valid_latency: int = 0
    startofpacket_enable: bool = False
    endofpacket_enable: bool = False
    channel_enable: bool = False
    error_enable: bool = False