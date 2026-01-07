"""
IP YAML Generator module.

Generates IP core YAML files (.ip.yml) from VHDL source files with automatic
bus interface detection, clock/reset classification, and structured output.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

import yaml

from fpga_lib.parser.hdl.vhdl_parser import VHDLParser
from fpga_lib.parser.hdl.bus_detector import BusInterfaceDetector
from fpga_lib.model.core import IpCore
from fpga_lib.model.base import VLNV
from fpga_lib.model.port import Port, PortDirection
from fpga_lib.model.bus import BusInterface
from fpga_lib.model.clock_reset import Clock, Reset


class IpYamlGenerator:
    """
    Generates IP YAML files from VHDL source files.

    Parses VHDL entities to extract ports, generics, and automatically
    detects bus interfaces like AXI-Lite, AXI-Stream, and Avalon-MM.
    """

    def __init__(self, detect_bus: bool = True):
        """
        Initialize the generator.

        Args:
            detect_bus: Enable automatic bus interface detection
        """
        self.parser = VHDLParser()
        self.detect_bus = detect_bus
        self.bus_detector = BusInterfaceDetector() if detect_bus else None

    def generate(
        self,
        vhdl_path: Path,
        vendor: str = "user",
        library: str = "ip",
        version: str = "1.0",
        memmap_path: Optional[Path] = None,
    ) -> str:
        """
        Generate IP YAML content from a VHDL file.

        Args:
            vhdl_path: Path to VHDL source file
            vendor: VLNV vendor name
            library: VLNV library name
            version: VLNV version
            memmap_path: Optional path to memory map file to reference

        Returns:
            YAML string content
        """
        # Parse VHDL file
        result = self.parser.parse_file(str(vhdl_path))

        if result["entity"] is None:
            raise ValueError(f"No entity found in {vhdl_path}")

        ip_core = result["entity"]

        # Update VLNV with user-provided values
        ip_core.vlnv = VLNV(
            vendor=vendor,
            library=library,
            name=ip_core.vlnv.name,
            version=version
        )

        # Detect bus interfaces
        bus_interfaces = []
        user_ports = list(ip_core.ports)  # Copy original ports
        clocks = []
        resets = []

        if self.detect_bus and self.bus_detector:
            bus_interfaces = self.bus_detector.detect(ip_core.ports)
            clocks, resets = self.bus_detector.classify_clocks_resets(ip_core.ports)

            # Filter out bus and clock/reset ports from user ports
            bus_port_names = self._get_bus_port_names(bus_interfaces, ip_core.ports)
            clock_reset_names = {c.name for c in clocks} | {r.name for r in resets}
            excluded_names = bus_port_names | clock_reset_names

            user_ports = [p for p in ip_core.ports if p.name not in excluded_names]

        # Build YAML structure
        yaml_data = self._build_yaml_structure(
            ip_core=ip_core,
            user_ports=user_ports,
            clocks=clocks,
            resets=resets,
            bus_interfaces=bus_interfaces,
            memmap_path=memmap_path,
            vhdl_path=vhdl_path,
        )

        return yaml.dump(yaml_data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def _get_bus_port_names(
        self, bus_interfaces: List[BusInterface], ports: List[Port]
    ) -> set:
        """Get names of ports that belong to detected bus interfaces."""
        bus_port_names = set()
        for bus in bus_interfaces:
            prefix = bus.physical_prefix.lower()
            for port in ports:
                if port.name.lower().startswith(prefix):
                    bus_port_names.add(port.name)
        return bus_port_names

    def _build_yaml_structure(
        self,
        ip_core: IpCore,
        user_ports: List[Port],
        clocks: List[Clock],
        resets: List[Reset],
        bus_interfaces: List[BusInterface],
        memmap_path: Optional[Path],
        vhdl_path: Path,
    ) -> Dict[str, Any]:
        """Build the YAML dictionary structure."""
        data = {
            "apiVersion": "ipcore/v1.0",
            "vlnv": {
                "vendor": ip_core.vlnv.vendor,
                "library": ip_core.vlnv.library,
                "name": ip_core.vlnv.name,
                "version": ip_core.vlnv.version,
            },
            "description": ip_core.description or f"Generated from {vhdl_path.name}",
        }

        # Clocks
        if clocks:
            data["clocks"] = [
                {"name": c.name, "description": c.description or ""}
                for c in clocks
            ]

        # Resets
        if resets:
            data["resets"] = [
                {
                    "name": r.name,
                    "polarity": r.polarity.value,
                    "description": r.description or ""
                }
                for r in resets
            ]

        # User ports (not part of bus interfaces)
        if user_ports:
            data["ports"] = [
                self._port_to_dict(p) for p in user_ports
            ]

        # Bus interfaces
        if bus_interfaces:
            data["busInterfaces"] = [
                self._bus_interface_to_dict(b) for b in bus_interfaces
            ]

        # Parameters (from generics)
        if ip_core.parameters:
            data["parameters"] = [
                {
                    "name": p.name,
                    "value": p.value,
                    "description": p.description or ""
                }
                for p in ip_core.parameters
            ]

        # Memory maps reference
        if memmap_path:
            relative_path = memmap_path.name
            data["memoryMaps"] = {"import": relative_path}

        # File sets with the source VHDL file
        data["fileSets"] = {
            "rtl": {
                "files": [str(vhdl_path.name)]
            }
        }

        return data

    def _port_to_dict(self, port: Port) -> Dict[str, Any]:
        """Convert Port to dictionary."""
        d = {
            "name": port.name,
            "direction": port.direction.value,
        }
        if port.width > 1:
            d["width"] = port.width
        if port.type:
            d["type"] = port.type
        if port.description:
            d["description"] = port.description
        return d

    def _bus_interface_to_dict(self, bus: BusInterface) -> Dict[str, Any]:
        """Convert BusInterface to dictionary."""
        return {
            "name": bus.name,
            "type": bus.type,
            "mode": bus.mode.value,
            "physicalPrefix": bus.physical_prefix,
            "description": bus.description or "",
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate IP core YAML from VHDL source file",
        prog="ip_yaml_generator"
    )
    parser.add_argument(
        "vhdl_file",
        type=Path,
        help="Path to VHDL source file"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output .ip.yml path (default: {entity_name}.ip.yml)"
    )
    parser.add_argument(
        "--vendor",
        type=str,
        default="user",
        help="VLNV vendor name (default: user)"
    )
    parser.add_argument(
        "--library",
        type=str,
        default="ip",
        help="VLNV library name (default: ip)"
    )
    parser.add_argument(
        "--version",
        type=str,
        default="1.0",
        help="VLNV version (default: 1.0)"
    )
    parser.add_argument(
        "--no-detect-bus",
        action="store_true",
        help="Disable automatic bus interface detection"
    )
    parser.add_argument(
        "--memmap",
        type=Path,
        default=None,
        help="Path to memory map file to reference"
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing output file"
    )

    args = parser.parse_args()

    # Validate input file
    if not args.vhdl_file.exists():
        print(f"Error: VHDL file not found: {args.vhdl_file}", file=sys.stderr)
        sys.exit(1)

    # Generate
    generator = IpYamlGenerator(detect_bus=not args.no_detect_bus)

    try:
        yaml_content = generator.generate(
            vhdl_path=args.vhdl_file,
            vendor=args.vendor,
            library=args.library,
            version=args.version,
            memmap_path=args.memmap,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Extract entity name from content
        lines = yaml_content.split('\n')
        entity_name = None
        for line in lines:
            if 'name:' in line and entity_name is None:
                entity_name = line.split(':')[-1].strip()
                break
        output_path = args.vhdl_file.parent / f"{entity_name or 'output'}.ip.yml"

    # Check if output exists
    if output_path.exists() and not args.force:
        print(f"Error: Output file exists: {output_path}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        sys.exit(1)

    # Write output
    with open(output_path, 'w') as f:
        f.write(yaml_content)

    print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
