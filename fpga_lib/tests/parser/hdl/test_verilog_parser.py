"""
Tests for the Verilog Parser
"""
import os
import pytest
from typing import Dict, Any

from fpga_lib.parser.hdl.verilog_parser import VerilogParser
from fpga_lib.generator.hdl.vhdl_generator import VHDLGenerator
from fpga_lib.core.ip_core import IPCore


class TestVerilogParser:
    """Test cases for the Verilog parser."""

    def test_parse_module_ansi(self):
        """Test parsing a Verilog module with ANSI-style port declarations."""
        parser = VerilogParser()
        verilog_code = """
        // Simple counter module
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

        result = parser.parse_text(verilog_code)

        # Verify module was parsed
        assert result["module"] is not None
        assert isinstance(result["module"], IPCore)
        assert result["module"].name == "counter"

        # Verify ports
        interface = result["module"].interfaces[0]
        assert len(interface.ports) == 4

        # Verify port details
        port_names = [p.name for p in interface.ports]
        assert "clk" in port_names
        assert "rst" in port_names
        assert "enable" in port_names
        assert "count" in port_names

        # Find count port and check its type
        count_port = next(p for p in interface.ports if p.name == "count")
        assert count_port.type.base_type.name.lower() == "std_logic_vector"
        assert "7 downto 0" in count_port.type.range_constraint

    def test_parse_module_non_ansi(self):
        """Test parsing a Verilog module with non-ANSI-style port declarations."""
        parser = VerilogParser()
        verilog_code = """
        // Simple counter module with non-ANSI style ports
        module counter(clk, rst, enable, count);
            input clk;
            input rst;
            input enable;
            output [7:0] count;

            reg [7:0] count;

            always @(posedge clk or posedge rst) begin
                if (rst)
                    count <= 8'b0;
                else if (enable)
                    count <= count + 1'b1;
            end

        endmodule
        """

        result = parser.parse_text(verilog_code)

        # Verify module was parsed
        assert result["module"] is not None
        assert isinstance(result["module"], IPCore)
        assert result["module"].name == "counter"

        # Verify ports
        interface = result["module"].interfaces[0]
        assert len(interface.ports) == 4

        # Verify port details
        port_names = [p.name for p in interface.ports]
        assert "clk" in port_names
        assert "rst" in port_names
        assert "enable" in port_names
        assert "count" in port_names

    def test_verilog_to_vhdl_roundtrip(self):
        """Test roundtrip: parse Verilog module and generate VHDL entity."""
        verilog_parser = VerilogParser()
        vhdl_generator = VHDLGenerator()

        # Original Verilog code
        verilog_code = """
        module adder(
            input [7:0] a,
            input [7:0] b,
            output [8:0] sum
        );
            assign sum = a + b;
        endmodule
        """

        # Parse the Verilog code
        result = verilog_parser.parse_text(verilog_code)
        ip_core = result["module"]

        # Generate VHDL from the parsed Verilog module
        vhdl_entity = vhdl_generator.generate_entity(ip_core)

        # Check VHDL entity content
        assert "entity adder is" in vhdl_entity
        assert "port (" in vhdl_entity
        assert "a : in std_logic_vector(7 downto 0)" in vhdl_entity.replace("    ", "")
        assert "b : in std_logic_vector(7 downto 0)" in vhdl_entity.replace("    ", "")
        assert "sum : out std_logic_vector(8 downto 0)" in vhdl_entity.replace("    ", "")
        assert "end entity adder" in vhdl_entity
