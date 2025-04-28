"""
VHDL Parser module using pyparsing to parse VHDL entities and architectures.
"""
from typing import Dict, List, Optional, Tuple, Any
import re
from pyparsing import (
    Word, alphas, alphanums, Keyword, Forward, Group, Optional as Opt,
    QuotedString, Suppress, ZeroOrMore, delimitedList, oneOf, White,
    Literal, SkipTo, LineEnd, StringEnd, ParserElement, CharsNotIn,
    CaselessKeyword
)

from fpga_lib.core.data_types import DataType, VHDLBaseType
from fpga_lib.core.port import Port, Direction
from fpga_lib.core.interface import Interface
from fpga_lib.core.ip_core import IPCore

# Enable packrat parsing for better performance
ParserElement.set_default_whitespace_chars(' \t\n\r')
ParserElement.enable_packrat()

class VHDLParser:
    """Parser for VHDL files to extract entity and architecture information."""

    def __init__(self):
        """Initialize the VHDL parser with grammar definitions."""
        # VHDL keywords
        self.keywords = {
            "entity": CaselessKeyword("entity"),
            "is": CaselessKeyword("is"),
            "port": CaselessKeyword("port"),
            "end": CaselessKeyword("end"),
            "architecture": CaselessKeyword("architecture"),
            "of": CaselessKeyword("of"),
            "begin": CaselessKeyword("begin"),
            "in": CaselessKeyword("in"),
            "out": CaselessKeyword("out"),
            "inout": CaselessKeyword("inout"),
            "buffer": CaselessKeyword("buffer"),
            "linkage": CaselessKeyword("linkage"),
        }

        # Basic building blocks
        self.identifier = Word(alphas + "_", alphanums + "_")
        self.comment = "--" + SkipTo(LineEnd())
        self.direction = oneOf("in out inout buffer linkage", caseless=True)

        # Types
        self.simple_type = self.identifier.copy()
        self.range_type = Group(self.simple_type + "(" + Word(alphanums + "_-+:() ") + ")")
        self.data_type = self.range_type | self.simple_type

        # Port declaration
        self.port_decl = Group(
            self.identifier + ":" +
            self.direction +
            self.data_type +
            Opt(Literal(";") | Literal(","))  # Fixed: Use Literal for alternation with |
        ).set_results_name("port_decl")

        # Port list
        self.port_list = Group(
            Suppress("(") +
            delimitedList(self.port_decl, ";") +
            Suppress(")")
        ).set_results_name("port_list")

        # Entity declaration with string capture for debug
        self.entity_decl = (
            self.keywords["entity"] +
            self.identifier.set_results_name("entity_name") +
            self.keywords["is"] +
            self.keywords["port"] +
            self.port_list +
            Suppress(";") +
            self.keywords["end"] +
            Opt(self.keywords["entity"]) +
            Opt(self.identifier) +
            Suppress(";")
        ).set_results_name("entity_decl")

        # Architecture declaration (simplified, just detecting the structure)
        self.architecture_decl = (
            self.keywords["architecture"] +
            self.identifier.set_results_name("arch_name") +
            self.keywords["of"] +
            self.identifier.set_results_name("arch_entity") +
            self.keywords["is"] +
            SkipTo(self.keywords["begin"]) +
            self.keywords["begin"] +
            SkipTo(self.keywords["end"]) +
            self.keywords["end"] +
            Opt(self.keywords["architecture"]) +
            Opt(self.identifier) +
            Suppress(";")
        ).set_results_name("architecture_decl")

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a VHDL file and extract entity and architecture information.

        Args:
            file_path: Path to the VHDL file

        Returns:
            Dictionary containing parsed entity and architecture information
        """
        with open(file_path, 'r') as f:
            content = f.read()
        return self.parse_text(content)

    def parse_text(self, vhdl_text: str) -> Dict[str, Any]:
        """
        Parse VHDL text and extract entity and architecture information.

        Args:
            vhdl_text: VHDL code to parse

        Returns:
            Dictionary containing parsed entity and architecture information
        """
        result = {"entity": None, "architecture": None}

        # Use regular expression as a fallback for entity parsing
        # This is more flexible for different formatting styles
        if "entity" not in vhdl_text.lower():
            print("Warning: No 'entity' keyword found in VHDL text")
            return result

        try:
            # Basic regex for entity extraction as fallback
            entity_pattern = r'entity\s+(\w+)\s+is\s+port\s*\((.*?)\)\s*;\s*end\s+(entity\s+)?\1\s*;'
            entity_match = re.search(entity_pattern, vhdl_text, re.IGNORECASE | re.DOTALL)

            if entity_match:
                entity_name = entity_match.group(1)
                ports_text = entity_match.group(2)

                print(f"Regex found entity: {entity_name}")
                print(f"Ports text: {ports_text}")

                # Parse ports using regex
                port_pattern = r'(\w+)\s*:\s*(in|out|inout|buffer|linkage)\s+([\w\s\(\)]+)'
                port_matches = re.findall(port_pattern, ports_text, re.IGNORECASE)

                ports = []
                for port_match in port_matches:
                    port_name = port_match[0].strip()
                    direction_str = port_match[1].strip().lower()
                    type_str = port_match[2].strip()

                    print(f"Found port: {port_name}, direction: {direction_str}, type: {type_str}")

                    # Map direction string to Direction enum
                    direction_map = {
                        "in": Direction.IN,
                        "out": Direction.OUT,
                        "inout": Direction.INOUT,
                        "buffer": Direction.BUFFER,
                        "linkage": Direction.LINKAGE
                    }
                    direction = direction_map.get(direction_str, Direction.IN)

                    # Parse type and range if present
                    range_match = re.search(r'(\w+)\s*\((.*?)\)', type_str)
                    if range_match:
                        base_type_str = range_match.group(1)
                        range_str = range_match.group(2)
                        base_type = VHDLBaseType.from_string(base_type_str)
                        data_type = DataType(base_type, range_constraint=range_str)
                    else:
                        data_type = DataType(VHDLBaseType.from_string(type_str))

                    # Create port
                    port = Port(port_name, direction, type=data_type)
                    ports.append(port)

                # Create interface with all ports
                interface = Interface(name=entity_name, interface_type="vhdl_default", ports=ports)

                # Create and return IPCore with the correct entity name
                result["entity"] = IPCore(name=entity_name, interfaces=[interface])

            # Try to parse architecture using regex as well
            arch_pattern = r'architecture\s+(\w+)\s+of\s+(\w+)\s+is'
            arch_match = re.search(arch_pattern, vhdl_text, re.IGNORECASE)
            if arch_match:
                result["architecture"] = {
                    "name": arch_match.group(1),
                    "entity": arch_match.group(2)
                }

        except Exception as e:
            print(f"Error in regex parsing: {e}")

        # If regex approach didn't work, try the pyparsing approach
        if result["entity"] is None:
            try:
                print("Trying pyparsing approach for entity")
                entity_match = self.entity_decl.search_string(vhdl_text)
                print(f"Entity pyparsing match: {entity_match}")
                if entity_match and len(entity_match) > 0:
                    entity_data = entity_match[0]
                    result["entity"] = self._create_ip_core(entity_data)
            except Exception as e:
                print(f"Error parsing entity with pyparsing: {e}")

        if result["architecture"] is None:
            try:
                arch_match = self.architecture_decl.search_string(vhdl_text)
                if arch_match and len(arch_match) > 0:
                    arch_data = arch_match[0]
                    result["architecture"] = {
                        "name": arch_data["arch_name"],
                        "entity": arch_data["arch_entity"]
                    }
            except Exception as e:
                print(f"Error parsing architecture: {e}")

        return result

    def _create_ip_core(self, entity_data) -> IPCore:
        """
        Create an IPCore object from parsed entity data.

        Args:
            entity_data: Parsed entity data from pyparsing

        Returns:
            IPCore object representing the parsed entity
        """
        entity_name = entity_data["entity_name"]
        ports = []

        for port_decl in entity_data["port_list"]:
            name = port_decl[0]
            direction_str = port_decl[2].lower()
            type_info = port_decl[3]

            # Map direction string to Direction enum
            direction_map = {
                "in": Direction.IN,
                "out": Direction.OUT,
                "inout": Direction.INOUT,
                "buffer": Direction.BUFFER,
                "linkage": Direction.LINKAGE
            }
            direction = direction_map.get(direction_str, Direction.IN)

            # Handle type (can be simple or range type)
            if isinstance(type_info, str):
                # Simple type
                data_type = DataType(VHDLBaseType.from_string(type_info))
            else:
                # Range type
                base_type_str = type_info[0]
                range_str = type_info[1]
                base_type = VHDLBaseType.from_string(base_type_str)
                data_type = DataType(base_type, range_constraint=range_str)

            # Create port - using 'type' parameter instead of 'data_type'
            port = Port(name, direction, type=data_type)
            ports.append(port)

        # Create interface with all ports
        interface = Interface(name=entity_name, interface_type="vhdl_default", ports=ports)

        # Create and return IPCore with the correct entity name
        return IPCore(name=entity_name, interfaces=[interface])
