"""
VHDL Parser module using pyparsing to parse VHDL entities and architectures.
"""

from typing import Dict, List, Optional, Tuple, Any
import re
from pyparsing import (
    Word,
    alphas,
    alphanums,
    Keyword,
    Forward,
    Group,
    Optional as Opt,
    QuotedString,
    Suppress,
    ZeroOrMore,
    delimitedList,
    oneOf,
    White,
    Literal,
    SkipTo,
    LineEnd,
    StringEnd,
    ParserElement,
    CharsNotIn,
    CaselessKeyword,
    Regex,
    cppStyleComment,
    restOfLine,
)

from fpga_lib.model import IpCore, Port, PortDirection
from fpga_lib.core.data_types import DataType, VHDLBaseType

# Enable packrat parsing for better performance
ParserElement.set_default_whitespace_chars(" \t\n\r")
ParserElement.enable_packrat()


class VHDLParser:
    """Parser for VHDL files to extract entity and architecture information."""

    def __init__(self):
        """Initialize the VHDL parser with grammar definitions."""
        # Set up comment handling - VHDL comments start with '--' and continue to end of line
        self.comment = Literal("--") + restOfLine
        self.ignored_text = self.comment

        # VHDL keywords (case insensitive)
        self.keywords = {
            "entity": CaselessKeyword("entity"),
            "is": CaselessKeyword("is"),
            "port": CaselessKeyword("port"),
            "generic": CaselessKeyword("generic"),
            "end": CaselessKeyword("end"),
            "architecture": CaselessKeyword("architecture"),
            "of": CaselessKeyword("of"),
            "begin": CaselessKeyword("begin"),
            "in": CaselessKeyword("in"),
            "out": CaselessKeyword("out"),
            "inout": CaselessKeyword("inout"),
            "buffer": CaselessKeyword("buffer"),
            "linkage": CaselessKeyword("linkage"),
            "package": CaselessKeyword("package"),
        }

        # Basic building blocks
        self.identifier = Word(alphas + "_", alphanums + "_")
        self.direction = oneOf("in out inout buffer linkage", caseless=True)

        # Enhanced type handling
        self.simple_type_name = Word(alphas + "_", alphanums + "_.")

        # Better range handling for complex expressions like "31 downto 0"
        self.range_expr = Word(alphanums + "_-+:() ")
        self.range_type = Group(
            self.simple_type_name + Suppress("(") + self.range_expr + Suppress(")")
        )
        self.data_type = self.range_type | self.simple_type_name

        # Default value for generics - captures everything after ":=" until semicolon or closing paren
        self.default_value = Suppress(":=") + CharsNotIn(";)")

        # Enhanced port declaration parser
        # This now properly handles ports with or without a trailing semicolon
        self.port_decl = Group(
            self.identifier.set_results_name("port_name")
            + Suppress(":")
            + self.direction.set_results_name("direction")
            + self.data_type.set_results_name("type")
            + Opt(Suppress(";"))  # Semicolon is optional to handle the last port
        ).set_results_name("port_decl")

        # Generic declaration parser (similar to port but without direction, with optional default value)
        self.generic_decl = Group(
            self.identifier.set_results_name("generic_name")
            + Suppress(":")
            + self.data_type.set_results_name("type")
            + Opt(self.default_value.set_results_name("default_value"))
            + Opt(Suppress(";"))  # Semicolon is optional to handle the last generic
        ).set_results_name("generic_decl")

        # Port list that captures all ports, including the last one
        self.port_list = Group(
            Suppress("(") + delimitedList(self.port_decl, ";") + Suppress(")")
        ).set_results_name("port_list")

        # Generic list that captures all generics
        self.generic_list = Group(
            Suppress("(") + delimitedList(self.generic_decl, ";") + Suppress(")")
        ).set_results_name("generic_list")

        # Entity declaration parser with optional generics
        self.entity_decl = (
            self.keywords["entity"]
            + self.identifier.set_results_name("entity_name")
            + self.keywords["is"]
            + Opt(self.keywords["generic"] + self.generic_list + Suppress(";"))
            + self.keywords["port"]
            + self.port_list
            + Suppress(";")
            + self.keywords["end"]
            + Opt(self.keywords["entity"])
            + Opt(self.identifier)
            + Suppress(";")
        ).set_results_name("entity_decl")

        # Architecture declaration parser
        self.architecture_decl = (
            self.keywords["architecture"]
            + self.identifier.set_results_name("arch_name")
            + self.keywords["of"]
            + self.identifier.set_results_name("arch_entity")
            + self.keywords["is"]
            + SkipTo(self.keywords["begin"])
            + self.keywords["begin"]
            + SkipTo(self.keywords["end"])
            + self.keywords["end"]
            + Opt(self.keywords["architecture"])
            + Opt(self.identifier)
            + Suppress(";")
        ).set_results_name("architecture_decl")

        # Package declaration parser
        self.package_decl = (
            self.keywords["package"]
            + self.identifier.set_results_name("package_name")
            + self.keywords["is"]
            + SkipTo(self.keywords["end"])
            + self.keywords["end"]
            + Opt(self.keywords["package"])
            + Opt(self.identifier)
            + Suppress(";")
        ).set_results_name("package_decl")

        # Set parse actions to transform the parsed data
        self.port_list.set_parse_action(self._process_port_list)

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a VHDL file and extract entity and architecture information.

        Args:
            file_path: Path to the VHDL file

        Returns:
            Dictionary containing parsed entity and architecture information
        """
        with open(file_path, "r") as f:
            content = f.read()
        return self.parse_text(content)

    def parse_text(self, vhdl_text: str) -> Dict[str, Any]:
        """
        Parse VHDL text and extract entity and architecture information using pyparsing.

        Args:
            vhdl_text: VHDL code to parse

        Returns:
            Dictionary containing parsed entity and architecture information
        """
        result = {"entity": None, "architecture": None, "package": None}

        # Remove comments to simplify parsing
        vhdl_text_clean = self._remove_comments(vhdl_text)

        # Try to parse the entity using pyparsing
        try:
            entity_match = self.entity_decl.search_string(vhdl_text_clean)
            if entity_match and len(entity_match) > 0:
                entity_data = entity_match[0]
                entity_name = entity_data.get("entity_name")
                port_list = entity_data.get("port_list", [])
                generic_list = entity_data.get("generic_list", [])

                # Create ports from port_list
                ports = []
                for port_data in port_list:
                    port = self._create_port_from_data(port_data)
                    if port:
                        ports.append(port)

                # Create interface and IPCore
                if ports:
                    interface = Interface(
                        name=entity_name, interface_type="vhdl_default", ports=ports
                    )
                    ip_core = IPCore(name=entity_name, interfaces=[interface])
                else:
                    ip_core = IPCore(name=entity_name)

                # Add generics as parameters to the IPCore
                for generic_data in generic_list:
                    parameter = self._create_parameter_from_data(generic_data)
                    if parameter:
                        ip_core.parameters[parameter.name] = parameter

                result["entity"] = ip_core
        except Exception as e:
            print(f"Error parsing entity with pyparsing: {e}")
            # Fall back to regex-based parsing if pyparsing fails
            return self._parse_with_regex(vhdl_text_clean)

        # If pyparsing didn't find an entity, try regex-based parsing as fallback
        if result["entity"] is None:
            return self._parse_with_regex(vhdl_text_clean)

        # Parse architecture using pyparsing
        try:
            arch_match = self.architecture_decl.search_string(vhdl_text_clean)
            if arch_match and len(arch_match) > 0:
                arch_data = arch_match[0]
                result["architecture"] = {
                    "name": arch_data.get("arch_name"),
                    "entity": arch_data.get("arch_entity"),
                }
        except Exception as e:
            print(f"Error parsing architecture with pyparsing: {e}")
            # Fall back to regex for architecture
            arch_match = re.search(
                r"architecture\s+(\w+)\s+of\s+(\w+)\s+is",
                vhdl_text_clean,
                re.IGNORECASE | re.DOTALL,
            )
            if arch_match:
                result["architecture"] = {
                    "name": arch_match.group(1),
                    "entity": arch_match.group(2),
                }

        # Parse package using pyparsing
        try:
            package_match = self.package_decl.search_string(vhdl_text_clean)
            if package_match and len(package_match) > 0:
                package_data = package_match[0]
                result["package"] = {"name": package_data.get("package_name")}
        except Exception as e:
            print(f"Error parsing package with pyparsing: {e}")
            # Fall back to regex for package
            package_match = re.search(
                r"package\s+(\w+)\s+is", vhdl_text_clean, re.IGNORECASE | re.DOTALL
            )
            if package_match:
                result["package"] = {"name": package_match.group(1).strip()}

        return result

    def _create_port_from_data(self, port_data: dict) -> Port:
        """
        Create a Port object from parsed port data.

        Args:
            port_data: Dictionary containing port data

        Returns:
            Port object
        """
        try:
            port_name = port_data.get("port_name")
            direction_str = port_data.get("direction", "in").lower()
            type_info = port_data.get("type")

            # Map direction string to Direction enum
            direction_map = {
                "in": Direction.IN,
                "out": Direction.OUT,
                "inout": Direction.INOUT,
                "buffer": Direction.BUFFER,
                "linkage": Direction.LINKAGE,
            }
            direction = direction_map.get(direction_str, Direction.IN)

            # Create original type string for later reference
            original_type_str = ""
            data_type = None

            # Handle type (simple or range)
            if isinstance(type_info, str):
                # Simple type (e.g., std_logic)
                original_type_str = type_info
                data_type = DataType(VHDLBaseType.from_string(type_info))
            elif isinstance(type_info, list):
                # Range type (e.g., std_logic_vector(7 downto 0))
                base_type_str = type_info[0]
                range_str = type_info[1]
                original_type_str = f"{base_type_str}({range_str})"
                base_type = VHDLBaseType.from_string(base_type_str)
                data_type = DataType(base_type, range_constraint=range_str)

                # Explicitly set the width for vector types based on range
                try:
                    downto_match = re.search(r"(\d+)\s+downto\s+(\d+)", range_str)
                    if downto_match:
                        high = int(downto_match.group(1))
                        low = int(downto_match.group(2))
                        width = high - low + 1
                        data_type.width = width
                except Exception as e:
                    print(f"Error calculating width from range: {e}")

            # Create port with the type information
            port = Port(port_name, direction, type=data_type)
            # Store original type string as an attribute
            setattr(port, "original_type", original_type_str)

            return port
        except Exception as e:
            print(f"Error creating port from data: {e}")
            return None

    def _create_parameter_from_data(self, generic_data: dict):
        """
        Create a Parameter object from parsed generic data.

        Args:
            generic_data: Dictionary containing generic data

        Returns:
            Parameter object
        """
        try:
            from fpga_lib.model import Parameter

            generic_name = generic_data.get("generic_name")
            type_info = generic_data.get("type")
            default_value = generic_data.get("default_value")

            # Create original type string for later reference
            original_type_str = ""

            # Handle type (simple or range)
            if isinstance(type_info, str):
                # Simple type (e.g., natural, integer)
                original_type_str = type_info
            elif isinstance(type_info, list):
                # Range type (e.g., std_ulogic_vector(31 downto 0))
                base_type_str = type_info[0]
                range_str = type_info[1]
                original_type_str = f"{base_type_str}({range_str})"

            # Create parameter with the type information
            # Use the default value if available, otherwise None
            parameter_value = default_value.strip() if default_value else None
            parameter = Parameter(
                name=generic_name, value=parameter_value, type=original_type_str
            )

            return parameter
        except Exception as e:
            print(f"Error creating parameter from data: {e}")
            return None

    def _process_port_list(self, s, loc, tokens):
        """Parse action to process port list and extract all ports."""
        # Process the port list, ensuring all ports are captured
        return tokens

    def _remove_comments(self, text):
        """Remove comments from VHDL text for easier parsing."""
        # Remove single line comments
        result = re.sub(r"--.*$", "", text, flags=re.MULTILINE)
        return result

    def _parse_with_regex(self, vhdl_text_clean):
        """Fallback regex-based parsing for when pyparsing fails."""
        result = {"entity": None, "architecture": None, "package": None}

        # Get entity name
        entity_name_match = re.search(
            r"entity\s+(\w+)\s+is", vhdl_text_clean, re.IGNORECASE | re.DOTALL
        )
        expected_entity_name = None
        if entity_name_match:
            expected_entity_name = entity_name_match.group(1).strip()

        # Extract ports from entity
        if expected_entity_name:
            try:
                # Find the complete entity definition including generics and ports
                # Use a more robust pattern that captures the entire entity
                entity_pattern = rf"entity\s+{re.escape(expected_entity_name)}\s+is\s+(.*?)\s*end\s+(?:entity\s+)?{re.escape(expected_entity_name)}?"
                entity_match = re.search(
                    entity_pattern, vhdl_text_clean, re.IGNORECASE | re.DOTALL
                )

                if entity_match:
                    entity_body = entity_match.group(1)

                    # Extract generic section if present - look for generic ( ... );
                    generics = []
                    generic_start = entity_body.find("generic")
                    if generic_start != -1:
                        # Find the opening parenthesis after 'generic'
                        generic_paren_start = entity_body.find("(", generic_start)
                        if generic_paren_start != -1:
                            # Find the matching closing parenthesis by counting parentheses
                            paren_count = 0
                            generic_paren_end = -1

                            for i in range(generic_paren_start, len(entity_body)):
                                if entity_body[i] == "(":
                                    paren_count += 1
                                elif entity_body[i] == ")":
                                    paren_count -= 1
                                    if paren_count == 0:
                                        generic_paren_end = i
                                        break

                            if generic_paren_end != -1:
                                generics_text = entity_body[
                                    generic_paren_start + 1 : generic_paren_end
                                ]

                                # Parse generics with similar approach as ports
                                generic_entries = []

                                # Split on semicolons first, then parse each generic individually
                                generic_parts = re.split(r"\s*;\s*", generics_text)

                                for generic_part in generic_parts:
                                    generic_part = generic_part.strip()
                                    if not generic_part:
                                        continue

                                    # Remove comments from generic declaration
                                    generic_part = re.sub(
                                        r"--.*$", "", generic_part, flags=re.MULTILINE
                                    ).strip()
                                    if not generic_part:
                                        continue

                                    # Match: generic_name : type_with_possible_parentheses [optional_default_value]
                                    generic_match = re.match(
                                        r"(\w+)\s*:\s*([^:=]+)(?:\s*:=\s*(.+))?",
                                        generic_part,
                                        re.IGNORECASE | re.DOTALL,
                                    )
                                    if generic_match:
                                        generic_name = generic_match.group(1)
                                        type_str = generic_match.group(2).strip()
                                        default_value = (
                                            generic_match.group(3).strip()
                                            if generic_match.group(3)
                                            else None
                                        )
                                        generic_entries.append(
                                            (generic_name, type_str, default_value)
                                        )

                                generics = generic_entries

                    # Extract port section - look for port ( ... );
                    # Use a more sophisticated approach to find the complete port section
                    port_start = entity_body.find("port")
                    if port_start != -1:
                        # Find the opening parenthesis after 'port'
                        paren_start = entity_body.find("(", port_start)
                        if paren_start != -1:
                            # Find the matching closing parenthesis by counting parentheses
                            paren_count = 0
                            pos = paren_start
                            paren_end = -1

                            for i in range(paren_start, len(entity_body)):
                                if entity_body[i] == "(":
                                    paren_count += 1
                                elif entity_body[i] == ")":
                                    paren_count -= 1
                                    if paren_count == 0:
                                        paren_end = i
                                        break

                            if paren_end != -1:
                                ports_text = entity_body[paren_start + 1 : paren_end]
                            if paren_end != -1:
                                ports_text = entity_body[paren_start + 1 : paren_end]

                                # Parse ports with improved pattern that handles the last port and complex types
                                # Split by semicolons first, then parse each port individually
                                # This handles vector types with parentheses properly
                                port_entries = []

                                # First, split on semicolons to get individual port declarations
                                port_parts = re.split(r"\s*;\s*", ports_text)

                                for port_part in port_parts:
                                    port_part = port_part.strip()
                                    if not port_part:
                                        continue

                                    # Remove comments from port declaration
                                    port_part = re.sub(
                                        r"--.*$", "", port_part, flags=re.MULTILINE
                                    ).strip()
                                    if not port_part:
                                        continue

                                    # Match: port_name : direction type_with_possible_parentheses
                                    port_match = re.match(
                                        r"(\w+)\s*:\s*(in|out|inout|buffer|linkage)\s+(.+)",
                                        port_part,
                                        re.IGNORECASE | re.DOTALL,
                                    )
                                    if port_match:
                                        port_entries.append(
                                            (
                                                port_match.group(1),
                                                port_match.group(2),
                                                port_match.group(3).strip(),
                                            )
                                        )

                                port_matches = port_entries

                    ports = []
                    for port_match in port_matches:
                        port_name = port_match[0].strip()
                        direction_str = port_match[1].strip().lower()
                        type_str = port_match[2].strip()

                        direction_map = {
                            "in": Direction.IN,
                            "out": Direction.OUT,
                            "inout": Direction.INOUT,
                            "buffer": Direction.BUFFER,
                            "linkage": Direction.LINKAGE,
                        }
                        direction = direction_map.get(direction_str, Direction.IN)

                        # Store original type
                        original_type_str = type_str

                        # Parse type with improved regex for vector types
                        # This handles std_logic_vector(7 downto 0) format correctly
                        range_match = re.search(r"([\w\.\_]+)\s*\((.*?)\)", type_str)
                        if range_match:
                            base_type_str = range_match.group(1)
                            range_str = range_match.group(2)
                            base_type = VHDLBaseType.from_string(base_type_str)
                            data_type = DataType(base_type, range_constraint=range_str)
                            # Ensure range constraints are properly stored
                            if hasattr(data_type, "width"):
                                try:
                                    # Try to extract numeric width from range constraints like "7 downto 0"
                                    downto_match = re.search(
                                        r"(\d+)\s+downto\s+(\d+)", range_str
                                    )
                                    if downto_match:
                                        high = int(downto_match.group(1))
                                        low = int(downto_match.group(2))
                                        data_type.width = high - low + 1
                                except:
                                    # Default if parsing fails
                                    data_type.width = 8
                        else:
                            data_type = DataType(VHDLBaseType.from_string(type_str))

                        port = Port(port_name, direction, type=data_type)
                        setattr(port, "original_type", original_type_str)
                        ports.append(port)

                    if ports:
                        interface = Interface(
                            name=expected_entity_name,
                            interface_type="vhdl_default",
                            ports=ports,
                        )
                        ip_core = IPCore(
                            name=expected_entity_name, interfaces=[interface]
                        )
                    else:
                        ip_core = IPCore(name=expected_entity_name)

                    # Add generics as parameters to the IPCore
                    for generic_data in generics:
                        from fpga_lib.model import Parameter

                        generic_name = generic_data[0].strip()
                        type_str = generic_data[1].strip()
                        default_value = (
                            generic_data[2]
                            if len(generic_data) > 2 and generic_data[2]
                            else None
                        )

                        # Create parameter for the generic
                        parameter = Parameter(
                            name=generic_name, value=default_value, type=type_str
                        )
                        ip_core.parameters[parameter.name] = parameter

                    result["entity"] = ip_core
            except Exception as e:
                print(f"Error in regex fallback parsing: {e}")

        # Parse architecture
        try:
            arch_match = re.search(
                r"architecture\s+(\w+)\s+of\s+(\w+)\s+is",
                vhdl_text_clean,
                re.IGNORECASE | re.DOTALL,
            )
            if arch_match:
                result["architecture"] = {
                    "name": arch_match.group(1),
                    "entity": arch_match.group(2),
                }
        except Exception as e:
            print(f"Error parsing architecture with regex: {e}")

        # Parse package
        try:
            package_match = re.search(
                r"package\s+(\w+)\s+is", vhdl_text_clean, re.IGNORECASE | re.DOTALL
            )
            if package_match:
                result["package"] = {"name": package_match.group(1).strip()}
        except Exception as e:
            print(f"Error parsing package with regex: {e}")

        return result
