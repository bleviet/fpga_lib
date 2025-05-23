"""
Verilog Parser module using pyparsing to parse Verilog module declarations.
"""
from typing import Dict, List, Optional, Tuple, Any
import re
from pyparsing import (
    Word, alphas, alphanums, Keyword, Forward, Group, Optional as Opt,
    QuotedString, Suppress, ZeroOrMore, delimitedList, oneOf, White,
    Literal, SkipTo, LineEnd, StringEnd, ParserElement, nums, 
    CharsNotIn, pythonStyleComment, cppStyleComment, CaselessKeyword
)

from fpga_lib.core.data_types import DataType, VHDLBaseType
from fpga_lib.core.port import Port, Direction
from fpga_lib.core.interface import Interface
from fpga_lib.core.ip_core import IPCore

# Enable packrat parsing for better performance
ParserElement.set_default_whitespace_chars(' \t\n\r')
ParserElement.enable_packrat()

class VerilogParser:
    """Parser for Verilog files to extract module declarations."""
    
    def __init__(self):
        """Initialize the Verilog parser with grammar definitions."""
        # Verilog keywords
        self.keywords = {
            "module": CaselessKeyword("module"),
            "endmodule": CaselessKeyword("endmodule"),
            "input": CaselessKeyword("input"),
            "output": CaselessKeyword("output"),
            "inout": CaselessKeyword("inout"),
            "wire": CaselessKeyword("wire"),
            "reg": CaselessKeyword("reg"),
        }
        
        # Basic building blocks
        self.identifier = Word(alphas + "_", alphanums + "_$")
        
        # Comments
        self.line_comment = "//" + SkipTo(LineEnd())
        self.block_comment = "/*" + SkipTo("*/") + "*/"
        
        # Number definitions for vector ranges
        self.number = Word(nums)
        self.vector_range = Suppress("[") + self.number + Suppress(":") + self.number + Suppress("]")
        
        # Port types and directions
        self.direction = oneOf("input output inout", caseless=True)
        self.data_type = Opt(oneOf("wire reg logic", caseless=True))
        
        # Verilog port declaration with range
        self.port_decl_with_range = Group(
            self.direction +
            Opt(self.vector_range).set_results_name("range") + 
            self.data_type +
            self.identifier.set_results_name("name") +
            Opt(Suppress(Literal(",")) | Suppress(Literal(";")))  # Fixed: Use Literal objects
        ).set_results_name("port_decl")
        
        # Verilog port declaration without range
        self.port_decl_no_range = Group(
            self.direction +
            self.data_type +
            self.identifier.set_results_name("name") +
            Opt(Suppress(Literal(",")) | Suppress(Literal(";")))  # Fixed: Use Literal objects
        ).set_results_name("port_decl")
        
        self.port_decl = self.port_decl_with_range | self.port_decl_no_range
        
        # Port list - just names for the module declaration
        self.port_list_simple = Group(
            Suppress("(") +
            delimitedList(self.identifier) +
            Suppress(")")
        ).set_results_name("port_list")
        
        # Full port definitions
        self.full_port_list = Group(
            Suppress("(") +
            ZeroOrMore(self.port_decl) +
            Suppress(")")
        ).set_results_name("full_port_list")
        
        # Module declaration (ansi-style with inline port declarations)
        self.module_ansi_decl = (
            self.keywords["module"] +
            self.identifier.set_results_name("module_name") +
            self.full_port_list +
            Suppress(";") +
            SkipTo(self.keywords["endmodule"]) +
            self.keywords["endmodule"]
        ).set_results_name("module_ansi_decl")
        
        # Module declaration (older non-ansi style with port list followed by port definitions)
        self.module_non_ansi_decl = (
            self.keywords["module"] +
            self.identifier.set_results_name("module_name") +
            self.port_list_simple +
            Suppress(";") +
            ZeroOrMore(self.port_decl) +
            SkipTo(self.keywords["endmodule"]) +
            self.keywords["endmodule"]
        ).set_results_name("module_non_ansi_decl")
        
        # Combined module declaration (try ansi-style first, then non-ansi)
        self.module_decl = self.module_ansi_decl | self.module_non_ansi_decl
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a Verilog file and extract module information.
        
        Args:
            file_path: Path to the Verilog file
            
        Returns:
            Dictionary containing parsed module information
        """
        with open(file_path, 'r') as f:
            content = f.read()
        return self.parse_text(content)
    
    def parse_text(self, verilog_text: str) -> Dict[str, Any]:
        """
        Parse Verilog text and extract module information.
        
        Args:
            verilog_text: Verilog code to parse
            
        Returns:
            Dictionary containing parsed module information
        """
        result = {"module": None}
        
        # Check if "module" keyword exists in text
        if "module" not in verilog_text.lower():
            print("Warning: No 'module' keyword found in Verilog text")
            return result
            
        # Try regex approach first (more flexible with different formatting)
        try:
            # Extract module name - handle modules with special /* AUTOARG */ comment
            # This pattern is more robust for modules with special comments
            module_pattern = r'module\s+(\w+)\s*\((.*?)\);'
            module_match = re.search(module_pattern, verilog_text, re.IGNORECASE | re.DOTALL)
            
            if module_match:
                module_name = module_match.group(1)
                ports_text = module_match.group(2)
                
                print(f"Regex found module: {module_name}")
                print(f"Ports text: {ports_text}")
                
                # Special handling for AUTOARG comments - common in mor1kx files
                if "/*AUTOARG*/" in ports_text:
                    # This is a special case - find all port names and infer directions
                    # Look for the AUTOARG comment section that lists ports
                    autoarg_pattern = r'/\*AUTOARG\*/\s*(.*?)(?:\/\/|$)'
                    autoarg_match = re.search(autoarg_pattern, verilog_text, re.IGNORECASE | re.DOTALL)
                    
                    if autoarg_match:
                        # Get the AUTOARG section text
                        autoarg_text = autoarg_match.group(1)
                        
                        # Find outputs section
                        outputs_pattern = r'\/\/\s*outputs\s*(.*?)(?:\/\/|$)'
                        outputs_match = re.search(outputs_pattern, autoarg_text, re.IGNORECASE | re.DOTALL)
                        
                        # Find inputs section
                        inputs_pattern = r'\/\/\s*inputs\s*(.*?)(?:$)'
                        inputs_match = re.search(inputs_pattern, autoarg_text, re.IGNORECASE | re.DOTALL)
                        
                        ports = []
                        
                        # Process output ports
                        if outputs_match:
                            outputs_text = outputs_match.group(1)
                            output_ports = re.findall(r'(\w+)(?:,|\s*$)', outputs_text)
                            
                            for port_name in output_ports:
                                port_name = port_name.strip()
                                if port_name:  # Skip empty entries
                                    port = self._create_port(port_name, "output", None, None)
                                    ports.append(port)
                        
                        # Process input ports
                        if inputs_match:
                            inputs_text = inputs_match.group(1)
                            input_ports = re.findall(r'(\w+)(?:,|\s*$)', inputs_text)
                            
                            for port_name in input_ports:
                                port_name = port_name.strip()
                                if port_name:  # Skip empty entries
                                    port = self._create_port(port_name, "input", None, None)
                                    ports.append(port)
                        
                        if ports:
                            # Create interface with all ports from AUTOARG
                            interface = Interface(name=module_name, interface_type="verilog_default", ports=ports)
                            result["module"] = IPCore(name=module_name, interfaces=[interface])
                            return result  # Return early since we've handled the special case
                
                # If not AUTOARG or AUTOARG handling failed, continue with standard parsing
                # Parse ANSI-style port declarations with a more flexible regex pattern
                # This handles: input/output/inout, with optional reg/wire/logic, optional bit range, and name
                ansi_port_pattern = r'(input|output|inout)\s+(reg|wire|logic)?\s*(?:\[(\d+)\s*:\s*(\d+)\])?\s*(\w+)'
                ansi_ports = re.findall(ansi_port_pattern, ports_text, re.IGNORECASE)
                
                # If no ANSI-style ports found, look for non-ANSI style
                ports = []
                
                if ansi_ports:
                    print(f"Found {len(ansi_ports)} ANSI-style ports")
                    # Process ANSI-style ports
                    for port_match in ansi_ports:
                        direction_str = port_match[0].lower()
                        port_type = port_match[1].lower() if port_match[1] else None
                        msb_str = port_match[2]
                        lsb_str = port_match[3]
                        port_name = port_match[4]
                        
                        # Parse MSB and LSB if present
                        msb = int(msb_str) if msb_str else None
                        lsb = int(lsb_str) if lsb_str else None
                        
                        print(f"Found port: {port_name}, direction: {direction_str}, type: {port_type}, range: {msb}:{lsb}")
                        
                        # Create port
                        port = self._create_port(port_name, direction_str, msb, lsb)
                        ports.append(port)
                    
                    # Try to find any output ports that might have been missed by the first regex
                    # This handles the specific case of "output reg [7:0] count" style ports
                    output_reg_pattern = r'output\s+reg\s*\[(\d+)\s*:\s*(\d+)\]\s*(\w+)'
                    output_reg_ports = re.findall(output_reg_pattern, ports_text, re.IGNORECASE)
                    
                    for port_match in output_reg_ports:
                        msb = int(port_match[0])
                        lsb = int(port_match[1])
                        port_name = port_match[2]
                        
                        # Check if this port was already added
                        if not any(p.name == port_name for p in ports):
                            print(f"Found additional output reg port: {port_name}, range: {msb}:{lsb}")
                            port = self._create_port(port_name, "output", msb, lsb)
                            ports.append(port)
                    
                    # One more try with a more specific pattern for outputs with ranges
                    output_vector_pattern = r'output\s*\[(\d+)\s*:\s*(\d+)\]\s*(\w+)'
                    output_vector_ports = re.findall(output_vector_pattern, ports_text, re.IGNORECASE)
                    
                    for port_match in output_vector_ports:
                        msb = int(port_match[0])
                        lsb = int(port_match[1])
                        port_name = port_match[2]
                        
                        # Check if this port was already added
                        if not any(p.name == port_name for p in ports):
                            print(f"Found additional output vector port: {port_name}, range: {msb}:{lsb}")
                            port = self._create_port(port_name, "output", msb, lsb)
                            ports.append(port)
                            
                else:
                    # If the port list is just a list of names without directions
                    # Check if it's just a comma-separated list of identifiers without direction keywords
                    is_simple_list = not any(kw in ports_text.lower() for kw in ['input', 'output', 'inout'])
                    
                    if is_simple_list:
                        # Try to extract port names from the list
                        port_names = [p.strip() for p in re.split(r',\s*', ports_text) if p.strip()]
                        
                        # Look for port declarations elsewhere in the file
                        # First extract all input/output/inout declarations in the module body
                        port_decls = re.findall(
                            r'(input|output|inout)\s+(reg|wire|logic)?\s*(?:\[(\d+)\s*:\s*(\d+)\])?\s*(\w+)\s*;', 
                            verilog_text, 
                            re.IGNORECASE
                        )
                        
                        port_dict = {}
                        for decl in port_decls:
                            direction = decl[0].lower()
                            has_range = decl[2] != '' and decl[3] != ''
                            msb = int(decl[2]) if has_range else None
                            lsb = int(decl[3]) if has_range else None
                            name = decl[4]
                            
                            port_dict[name] = (direction, msb, lsb)
                        
                        for port_name in port_names:
                            if port_name in port_dict:
                                direction, msb, lsb = port_dict[port_name]
                                ports.append(self._create_port(port_name, direction, msb, lsb))
                            else:
                                # Default to input if direction is not specified
                                ports.append(self._create_port(port_name, "input", None, None))
                    else:
                        # Try a more general approach to find all ports
                        # This is a more comprehensive regex that handles more variations
                        comprehensive_pattern = r'(input|output|inout)(?:\s+(reg|wire|logic))?(?:\s*\[(\d+)\s*:\s*(\d+)\])?(?:\s+(\w+))(?:,|$|;)'
                        port_matches = re.findall(comprehensive_pattern, ports_text, re.IGNORECASE)
                        
                        for port_match in port_matches:
                            direction_str = port_match[0].lower()
                            port_type = port_match[1].lower() if port_match[1] else None
                            msb_str = port_match[2]
                            lsb_str = port_match[3]
                            port_name = port_match[4]
                            
                            # Parse MSB and LSB if present
                            msb = int(msb_str) if msb_str else None
                            lsb = int(lsb_str) if lsb_str else None
                            
                            print(f"Found port: {port_name}, direction: {direction_str}, type: {port_type}, range: {msb}:{lsb}")
                            
                            # Create port
                            port = self._create_port(port_name, direction_str, msb, lsb)
                            ports.append(port)
                        
                        # If still no ports found, fall back to non-ANSI style
                        if not ports:
                            # Handle non-ANSI style (just port names in the list)
                            port_names = [name.strip() for name in ports_text.split(',')]
                            
                            # Look for port declarations in the rest of the module
                            decl_pattern = r'(input|output|inout)(?:\s+(?:reg|wire|logic))?(?:\s*\[(\d+)\s*:\s*(\d+)\])?(?:\s+(\w+))'
                            port_decls = re.findall(decl_pattern, verilog_text, re.IGNORECASE)
                            
                            # Create a dictionary of port declarations for quick lookup
                            port_dict = {}
                            for port_decl in port_decls:
                                direction_str = port_decl[0].lower()
                                has_range = port_decl[1] != '' and port_decl[2] != ''
                                msb = int(port_decl[1]) if has_range else None
                                lsb = int(port_decl[2]) if has_range else None
                                port_name = port_decl[3]
                                
                                port_dict[port_name] = (direction_str, msb, lsb)
                            
                            # Create ports based on declarations
                            for port_name in port_names:
                                port_name = port_name.strip()
                                if port_name in port_dict:
                                    direction_str, msb, lsb = port_dict[port_name]
                                    port = self._create_port(port_name, direction_str, msb, lsb)
                                else:
                                    # Default port if no declaration found
                                    port = Port(port_name, Direction.IN, type=DataType(VHDLBaseType.STD_LOGIC))
                                    
                                ports.append(port)
                
                # Create interface with all ports
                interface = Interface(name=module_name, interface_type="verilog_default", ports=ports)
                
                # Create and return IPCore with the correct module name
                result["module"] = IPCore(name=module_name, interfaces=[interface])
            else:
                # Try a more flexible pattern to match module declarations
                # Some module declarations might have comments or unusual formatting
                module_alt_pattern = r'module\s+([a-zA-Z0-9_]+)'
                module_alt_match = re.search(module_alt_pattern, verilog_text, re.IGNORECASE)
                
                if module_alt_match:
                    module_name = module_alt_match.group(1)
                    print(f"Found module name using alternative pattern: {module_name}")
                    
                    # Try to find port declarations in the module body
                    port_decls = re.findall(
                        r'(input|output|inout)\s+(reg|wire|logic)?\s*(?:\[(\d+)\s*:\s*(\d+)\])?\s*(\w+)\s*;', 
                        verilog_text, 
                        re.IGNORECASE
                    )
                    
                    ports = []
                    for decl in port_decls:
                        direction = decl[0].lower()
                        has_range = decl[2] != '' and decl[3] != ''
                        msb = int(decl[2]) if has_range else None
                        lsb = int(decl[3]) if has_range else None
                        name = decl[4]
                        
                        ports.append(self._create_port(name, direction, msb, lsb))
                    
                    if ports:
                        interface = Interface(name=module_name, interface_type="verilog_default", ports=ports)
                        result["module"] = IPCore(name=module_name, interfaces=[interface])
                
        except Exception as e:
            print(f"Error in regex parsing: {e}")
        
        # If regex approach didn't work, try the pyparsing approach
        if result["module"] is None:
            try:
                print("Trying pyparsing approach for module")
                module_match = self.module_decl.search_string(verilog_text)
                print(f"Module pyparsing match: {module_match}")
                if module_match and len(module_match) > 0:
                    module_data = module_match[0]
                    result["module"] = self._create_ip_core(module_data)
            except Exception as e:
                print(f"Error parsing module with pyparsing: {e}")
        
        return result
    
    def _create_port(self, name: str, direction_str: str, msb: Optional[int], lsb: Optional[int]) -> Port:
        """
        Create a port from extracted values.
        
        Args:
            name: Port name
            direction_str: Direction string ('input', 'output', 'inout')
            msb: Most significant bit (if vector)
            lsb: Least significant bit (if vector)
            
        Returns:
            Port object
        """
        # Map direction string to Direction enum
        direction_map = {
            "input": Direction.IN,
            "output": Direction.OUT,
            "inout": Direction.INOUT
        }
        direction = direction_map.get(direction_str.lower(), Direction.IN)
        
        # Create data type based on range
        if msb is not None and lsb is not None:
            width = abs(msb - lsb) + 1
            if width == 1:
                data_type = DataType(VHDLBaseType.STD_LOGIC)
            else:
                data_type = DataType(VHDLBaseType.STD_LOGIC_VECTOR, f"{msb} downto {lsb}")
        else:
            data_type = DataType(VHDLBaseType.STD_LOGIC)
            
        return Port(name, direction, type=data_type)
    
    def _create_ip_core(self, module_data) -> IPCore:
        """
        Create an IPCore object from parsed module data.
        
        Args:
            module_data: Parsed module data from pyparsing
            
        Returns:
            IPCore object representing the parsed module
        """
        # Extract the module name
        module_name = ""
        if "module_name" in module_data:
            module_name = module_data["module_name"]
        
        ports = []
        
        # Handle ANSI style module
        if "full_port_list" in module_data:
            for port_decl in module_data["full_port_list"]:
                ports.append(self._create_port_from_decl(port_decl))
        # Handle non-ANSI style module
        elif "port_list" in module_data:
            # Non-ANSI style is more complex as we need to link port names with their declarations
            port_names = module_data["port_list"]
            # Find port declarations in the rest of the module body
            port_decls = [item for item in module_data if isinstance(item, list) and len(item) >= 3]
            
            # Match port declarations with names
            for port_name in port_names:
                for port_decl in port_decls:
                    if "name" in port_decl and port_decl["name"] == port_name:
                        ports.append(self._create_port_from_decl(port_decl))
                        break
                else:
                    # If we can't find the declaration, create a default one
                    default_port = Port(port_name, Direction.IN, type=DataType(VHDLBaseType.STD_LOGIC))
                    ports.append(default_port)
        
        # Create interface with all ports
        # Use "verilog_default" as the interface_type
        interface = Interface(name=module_name, interface_type="verilog_default", ports=ports)
        
        # Create and return IPCore with the correct module name
        ip_core = IPCore(name=module_name, interfaces=[interface])
        return ip_core
    
    def _create_port_from_decl(self, port_decl) -> Port:
        """
        Create a Port object from parsed port declaration.
        
        Args:
            port_decl: Parsed port declaration from pyparsing
            
        Returns:
            Port object representing the port
        """
        name = port_decl["name"]
        
        # Get direction
        direction_str = port_decl[0].lower()
        direction_map = {
            "input": Direction.IN,
            "output": Direction.OUT,
            "inout": Direction.INOUT
        }
        direction = direction_map.get(direction_str, Direction.IN)
        
        # Determine data type based on range if present
        if "range" in port_decl and port_decl["range"]:
            # Vector type with range
            msb = int(port_decl["range"][0])
            lsb = int(port_decl["range"][1])
            width = abs(msb - lsb) + 1
            if width == 1:
                data_type = DataType(VHDLBaseType.STD_LOGIC)
            else:
                data_type = DataType(VHDLBaseType.STD_LOGIC_VECTOR, f"{msb} downto {lsb}")
        else:
            # Scalar type without range
            data_type = DataType(VHDLBaseType.STD_LOGIC)
        
        # Create port - using 'type' parameter instead of 'data_type'
        return Port(name, direction, type=data_type)