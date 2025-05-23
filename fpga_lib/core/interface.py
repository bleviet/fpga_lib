# fpga_lib/core/interface.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Literal, Optional
from enum import Enum
from fpga_lib.core.data_types import DataType, BitType, VectorType, IntegerType
from fpga_lib.core.port import PortDirection, Port


@dataclass
class Interface:
    """
    Base class for all bus interfaces.
    """

    name: str
    interface_type: str
    ports: List[Port] = field(default_factory=list)

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
    prot_supported: List[str] = field(
        default_factory=lambda: ["PRIVILEGED", "SECURE", "NONSECURE"]
    )
    cache_supported: bool = False

    def __post_init__(self) -> None:
        # Override interface_type after calling super()
        self.interface_type = "axi"
        self.ports.extend([
            Port(name=f"{self.name}_aclk", direction=PortDirection.IN, type=BitType(), width=1),
            Port(name=f"{self.name}_aresetn", direction=PortDirection.IN, type=BitType(), width=1),
        ])

@dataclass
class AXILiteInterface(AXIBaseInterface):
    """
    AXI Lite interface.
    """

    interface_type: str = "axi_lite"
    burst_types: List[str] = field(default_factory=lambda: [])
    interface_mode: Literal["master", "slave"] = "slave"  # Default to slave

    def __post_init__(self) -> None:
        # Directly set the interface_type
        self.interface_type = "axi_lite"

        # Define AXI Lite signals with direction specified for slave mode
        axi_lite_signals = [
            Port(name=f"{self.name}_awaddr", direction=PortDirection.IN, type=VectorType(width=self.address_width), width=self.address_width),
            Port(name=f"{self.name}_awvalid", direction=PortDirection.IN, type=BitType(), width=1),
            Port(name=f"{self.name}_awready", direction=PortDirection.OUT, type=BitType(), width=1),
            Port(name=f"{self.name}_wdata", direction=PortDirection.IN, type=VectorType(width=self.data_width), width=self.data_width),
            Port(name=f"{self.name}_wstrb", direction=PortDirection.IN, type=VectorType(width=self.data_width // 8), width=self.data_width // 8),
            Port(name=f"{self.name}_wvalid", direction=PortDirection.IN, type=BitType(), width=1),
            Port(name=f"{self.name}_wready", direction=PortDirection.OUT, type=BitType(), width=1),
            Port(name=f"{self.name}_bresp", direction=PortDirection.OUT, type=VectorType(width=2), width=2),
            Port(name=f"{self.name}_bvalid", direction=PortDirection.OUT, type=BitType(), width=1),
            Port(name=f"{self.name}_bready", direction=PortDirection.IN, type=BitType(), width=1),
            Port(name=f"{self.name}_araddr", direction=PortDirection.IN, type=VectorType(width=self.address_width), width=self.address_width),
            Port(name=f"{self.name}_arvalid", direction=PortDirection.IN, type=BitType(), width=1),
            Port(name=f"{self.name}_arready", direction=PortDirection.OUT, type=BitType(), width=1),
            Port(name=f"{self.name}_rdata", direction=PortDirection.OUT, type=VectorType(width=self.data_width), width=self.data_width),
            Port(name=f"{self.name}_rresp", direction=PortDirection.OUT, type=VectorType(width=2), width=2),
            Port(name=f"{self.name}_rvalid", direction=PortDirection.OUT, type=BitType(), width=1),
            Port(name=f"{self.name}_rready", direction=PortDirection.IN, type=BitType(), width=1),
        ]
        self.ports.extend(axi_lite_signals)

        # Invert directions if interface_mode is master
        if self.interface_mode == "master":
            for port in self.ports:
                port.invert_direction()


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
    interface_mode: Literal["master", "slave"] = "slave"  # Default to slave

    def __post_init__(self) -> None:
        # Directly set the interface_type
        self.interface_type = "axi_stream"

        # Define AXI Stream signals with direction specified for slave mode
        axi_stream_signals = [
            Port(name=f"{self.name}_tdata", direction=PortDirection.IN, type=VectorType(width=self.data_width), width=self.data_width),
            Port(name=f"{self.name}_tvalid", direction=PortDirection.IN, type=BitType(), width=1),
            Port(name=f"{self.name}_tready", direction=PortDirection.OUT, type=BitType(), width=1),
            Port(name=f"{self.name}_tlast", direction=PortDirection.IN, type=BitType(), width=1),
            Port(name=f"{self.name}_tuser", direction=PortDirection.IN, type=VectorType(width=self.user_width), width=self.user_width),
            Port(name=f"{self.name}_tstrb", direction=PortDirection.IN, type=VectorType(width=self.data_width // 8), width=self.data_width // 8),
            Port(name=f"{self.name}_tkeep", direction=PortDirection.IN, type=VectorType(width=self.data_width // 8), width=self.data_width // 8),
            Port(name=f"{self.name}_tid", direction=PortDirection.IN, type=VectorType(width=self.tid_width), width=self.tid_width),
            Port(name=f"{self.name}_tdest", direction=PortDirection.IN, type=VectorType(width=self.tdest_width), width=self.tdest_width),
        ]
        self.ports.extend(axi_stream_signals)

        # Invert directions if interface_mode is master
        if self.interface_mode == "master":
            for port in self.ports:
                port.invert_direction()
