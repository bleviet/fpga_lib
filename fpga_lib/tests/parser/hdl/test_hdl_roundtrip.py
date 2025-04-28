"""
Test module for complete HDL roundtrip testing (parse -> generate -> compare).
This allows testing the full workflow with real HDL files.
"""
import os
import tempfile
import pytest
import difflib
from typing import Dict, Any, Tuple

from fpga_lib.parser.hdl.vhdl_parser import VHDLParser
from fpga_lib.parser.hdl.verilog_parser import VerilogParser
from fpga_lib.generator.hdl.vhdl_generator import VHDLGenerator
from fpga_lib.core.ip_core import IPCore


class TestHDLRoundtrip:
    """Test cases for HDL roundtrip: parse -> generate -> compare."""

    def setup_method(self):
        """Set up test environment."""
        self.vhdl_parser = VHDLParser()
        self.verilog_parser = VerilogParser()
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

        # Create Verilog file
        verilog_content = """
// 8-bit counter module
module counter(
    input clk,
    input rst,
    input enable,
    output reg [7:0] count
);

    always @(posedge clk or posedge rst) begin
        if (rst)
            count <= 8'b0;
        else if (enable)
            count <= count + 1'b1;
    end

endmodule
        """
        verilog_path = os.path.join(self.temp_dir.name, "counter.v")
        with open(verilog_path, 'w') as f:
            f.write(verilog_content)
        test_files["verilog"] = verilog_path

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

    def test_verilog_to_vhdl_conversion(self):
        """Test Verilog to VHDL conversion: parse Verilog -> generate VHDL."""
        # Parse the Verilog file
        result = self.verilog_parser.parse_file(self.test_files["verilog"])
        ip_core = result["module"]

        assert ip_core is not None
        assert ip_core.name == "counter"

        # Generate VHDL from the IPCore
        generated_vhdl = self.vhdl_generator.generate_entity(ip_core)

        # Create a test output file with the generated VHDL
        output_path = os.path.join(self.temp_dir.name, "verilog_to_vhdl.vhd")
        with open(output_path, 'w') as f:
            f.write(generated_vhdl)

        # Essential content checks
        assert "entity counter is" in generated_vhdl
        assert "port (" in generated_vhdl
        assert "clk : in std_logic" in generated_vhdl.replace("    ", "")
        assert "rst : in std_logic" in generated_vhdl.replace("    ", "")
        assert "enable : in std_logic" in generated_vhdl.replace("    ", "")
        assert "count : out std_logic_vector(7 downto 0)" in generated_vhdl.replace("    ", "")
        assert "end entity counter" in generated_vhdl
