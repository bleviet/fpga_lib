"""
Test module for complete HDL roundtrip testing (parse -> generate -> compare).
This allows testing the full workflow with real HDL files.
"""
import os
import tempfile
import pytest
import difflib
import glob
import re
from typing import Dict, Any, Tuple

from fpga_lib.parser.hdl.vhdl_parser import VHDLParser
from fpga_lib.generator.hdl.vhdl_generator import VHDLGenerator
from fpga_lib.core.ip_core import IPCore


class TestHDLRoundtrip:
    """Test cases for HDL roundtrip: parse -> generate -> compare."""
    
    def setup_method(self):
        """Set up test environment."""
        self.vhdl_parser = VHDLParser()
        self.vhdl_generator = VHDLGenerator()
        
        # Create test files for parsing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_files = self._create_test_files()
    
    def teardown_method(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def _create_test_files(self) -> Dict[str, str]:
        """Create test HDL files for parsing and return paths."""
        test_files = {}
        
        # Create VHDL file
        vhdl_content = """
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity counter is
    port (
        clk     : in std_logic;
        rst     : in std_logic;
        enable  : in std_logic;
        count   : out std_logic_vector(7 downto 0)
    );
end entity counter;

architecture behavioral of counter is
    signal count_internal : unsigned(7 downto 0);
begin
    process(clk, rst)
    begin
        if rst = '1' then
            count_internal <= (others => '0');
        elsif rising_edge(clk) then
            if enable = '1' then
                count_internal <= count_internal + 1;
            end if;
        end if;
    end process;
    
    count <= std_logic_vector(count_internal);
end architecture behavioral;
        """
        vhdl_path = os.path.join(self.temp_dir.name, "counter.vhd")
        with open(vhdl_path, 'w') as f:
            f.write(vhdl_content)
        test_files["vhdl"] = vhdl_path
        
        return test_files
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text for comparison."""
        return " ".join(text.replace(";", "; ").split())
    
    def test_vhdl_roundtrip(self):
        """Test VHDL roundtrip: parse file -> generate VHDL -> compare essentials."""
        # Parse the VHDL file
        result = self.vhdl_parser.parse_file(self.test_files["vhdl"])
        ip_core = result["entity"]
        
        assert ip_core is not None
        assert ip_core.name == "counter"
        
        # Generate VHDL from the IPCore
        generated_vhdl = self.vhdl_generator.generate_entity(ip_core)
        
        # Read original entity part only from the test file
        with open(self.test_files["vhdl"], 'r') as f:
            original_content = f.read()
        
        # Extract entity part for comparison (simplified for test)
        entity_start = original_content.find("entity")
        entity_end = original_content.find("end entity")
        original_entity = original_content[entity_start:entity_end + len("end entity counter;")]
        
        # Compare essential parts of the entity declarations
        norm_original = self._normalize_whitespace(original_entity)
        norm_generated = self._normalize_whitespace(generated_vhdl)
        
        # Create a test output file with both versions for inspection if needed
        output_path = os.path.join(self.temp_dir.name, "vhdl_roundtrip_comparison.txt")
        with open(output_path, 'w') as f:
            f.write("=== ORIGINAL ===\n")
            f.write(original_entity)
            f.write("\n\n=== GENERATED ===\n")
            f.write(generated_vhdl)
            f.write("\n\n=== DIFF ===\n")
            for line in difflib.unified_diff(
                original_entity.splitlines(), 
                generated_vhdl.splitlines(),
                fromfile='original',
                tofile='generated',
                lineterm=''
            ):
                f.write(line + "\n")
        
        # Essential content checks
        assert "entity counter is" in norm_generated
        assert "port (" in norm_generated
        assert "clk : in std_logic" in norm_generated
        assert "rst : in std_logic" in norm_generated
        assert "enable : in std_logic" in norm_generated
        assert "count : out std_logic_vector(7 downto 0)" in norm_generated
        assert "end entity counter" in norm_generated
    
    @pytest.mark.parametrize("vhdl_file", glob.glob(os.path.join(os.path.dirname(__file__), "../resources/vhdl/neorv32_core/*.vhd")))
    def test_neorv32_vhdl_files(self, vhdl_file):
        """Test parsing and validating all VHDL files in the neorv32_core directory."""
        # Get just the file name for reporting
        file_basename = os.path.basename(vhdl_file)
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), "../resources/vhdl/output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Read the original file content
        with open(vhdl_file, 'r') as f:
            original_content = f.read().lower()
        
        # Check if file contains entity declaration using regex
        entity_in_file = re.search(r'entity\s+(\w+)\s+is', original_content, re.IGNORECASE | re.DOTALL)
        expected_entity_name = None
        if entity_in_file:
            expected_entity_name = entity_in_file.group(1).strip().lower()
            print(f"Expected entity name in {file_basename}: {expected_entity_name}")
            
        # Parse the VHDL file
        try:
            result = self.vhdl_parser.parse_file(vhdl_file)
            
            # Create a detailed report for all files
            report_file = os.path.join(output_dir, f"report_{file_basename}.txt")
            with open(report_file, 'w') as f:
                f.write(f"File: {file_basename}\n")
                f.write(f"Original file: {vhdl_file}\n\n")
                
                # If we found an entity name in the file but parser didn't detect it
                if expected_entity_name and (not result["entity"] or result["entity"].name.lower() != expected_entity_name):
                    f.write(f"⚠️ PARSER ERROR: File contains entity '{expected_entity_name}' but parser ")
                    if not result["entity"]:
                        f.write("didn't detect any entity.\n")
                    else:
                        f.write(f"detected entity '{result['entity'].name}'.\n")
                    pytest.fail(f"Parser didn't correctly detect entity '{expected_entity_name}' in {file_basename}")
                
                # Check if we have an entity or a package
                if "entity" in result and result["entity"] is not None:
                    ip_core = result["entity"]
                    f.write(f"Entity: {ip_core.name}\n")
                    
                    # Document all ports with their types
                    if ip_core.interfaces and ip_core.interfaces[0].ports:
                        interface = ip_core.interfaces[0]
                        f.write(f"Ports ({len(interface.ports)}):\n")
                        for port in interface.ports:
                            port_type_str = self._get_port_type_description(port)
                            f.write(f"  - {port.name} : {port.direction} {port_type_str}\n")
                    else:
                        f.write("No ports found in entity\n")
                    
                    # Generate VHDL from the IPCore
                    try:
                        generated_vhdl = self.vhdl_generator.generate_entity(ip_core)
                        f.write("\nGenerated VHDL:\n")
                        f.write(generated_vhdl)
                        
                        # Write the generated VHDL to a separate output file
                        output_file = os.path.join(output_dir, f"generated_{file_basename}")
                        with open(output_file, 'w') as vhdl_out:
                            vhdl_out.write(generated_vhdl)
                            
                        # Basic validation of generated content
                        assert f"entity {ip_core.name.lower()}" in generated_vhdl.lower(), f"Missing entity declaration in generated VHDL for {file_basename}"
                        assert f"end entity {ip_core.name.lower()}" in generated_vhdl.lower(), f"Missing end entity in generated VHDL for {file_basename}"
                        
                        # Type validation - check if all original port types are properly represented
                        # in the generated VHDL
                        for port in interface.ports:
                            port_name = port.name.lower()
                            
                            # Check direction
                            direction_str = port.direction.value.lower() if hasattr(port.direction, "value") else str(port.direction).lower()
                            assert f"{port_name} : {direction_str}" in generated_vhdl.lower(), \
                                f"Port {port_name} direction {direction_str} not found in generated VHDL"
                            
                            # Check type - this is a basic check that could be improved
                            port_type_str = self._get_port_type_description(port).lower()
                            # Remove whitespace for comparison
                            clean_vhdl = ''.join(generated_vhdl.lower().split())
                            clean_port = f"{port_name}:{direction_str}{port_type_str.replace(' ', '')}"
                            
                            assert clean_port in clean_vhdl.replace(' ', ''), \
                                f"Port {port_name} with type {port_type_str} not correctly represented in generated VHDL"
                        
                        f.write("\nValidation: ✅ PASS\n")
                        print(f"✅ Successfully parsed and generated VHDL for entity {ip_core.name} from {file_basename}")
                        print(f"   Output written to {output_file}")
                        
                    except Exception as e:
                        f.write(f"\n❌ Error generating VHDL: {str(e)}\n")
                        pytest.fail(f"Error generating VHDL for {file_basename}: {str(e)}")
                    
                elif "package" in result and result["package"] is not None:
                    # For package files, just validate that we parsed something
                    package_name = result["package"].get("name")
                    assert package_name, f"Failed to parse package name from {file_basename}"
                    f.write(f"Package: {package_name}\n")
                    f.write("Parsed successfully\n")
                    print(f"✅ Successfully parsed package {package_name} from {file_basename}")
                
                elif expected_entity_name:
                    # We should have detected an entity but didn't
                    f.write(f"❌ PARSER ERROR: Failed to detect entity {expected_entity_name}\n")
                    pytest.fail(f"Parser failed to detect entity {expected_entity_name} in {file_basename}")
                    
                else:
                    # Some files might not have entities or packages
                    f.write("No entity or package found\n")
                    print(f"⚠️ File {file_basename} parsed but no entity or package found")
                
        except Exception as e:
            # For errors, write an error report
            error_report = os.path.join(output_dir, f"error_report_{file_basename}.txt")
            with open(error_report, 'w') as f:
                f.write(f"Error parsing {file_basename}: {str(e)}\n")
            
            pytest.fail(f"Error parsing {file_basename}: {str(e)}")
    
    def _get_port_type_description(self, port):
        """Get a detailed description of the port type for testing and documentation."""
        if not hasattr(port, 'type'):
            return f"Unknown type (width={port.width})"
            
        port_type = port.type
        
        # If the port has an original_type attribute, use it (preserves std_ulogic vs std_logic)
        if hasattr(port, 'original_type') and port.original_type:
            return port.original_type
            
        if hasattr(port_type, "to_vhdl"):
            return port_type.to_vhdl()
        elif hasattr(port_type, 'base_type') and hasattr(port_type.base_type, 'name'):
            base_type_name = port_type.base_type.name.lower()
            if hasattr(port_type, 'range_constraint') and port_type.range_constraint:
                return f"{base_type_name}({port_type.range_constraint})"
            else:
                return base_type_name
        elif isinstance(port_type, str):
            return port_type.lower()
            
        # Default case - use what's in the generated VHDL
        return f"std_logic" if port.width == 1 else f"std_logic_vector({port.width - 1} downto 0)"