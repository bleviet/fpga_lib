"""
Test cases for the VHDL parser module.
"""
import os
import difflib
import pytest
from pyparsing import Word, alphas, alphanums

from fpga_lib.parser.hdl.vhdl_parser import VHDLParser
from fpga_lib.generator.hdl.vhdl_generator import VHDLGenerator
from fpga_lib.core.ip_core import IPCore
from fpga_lib.core.port import Direction


class TestVHDLParser:
    """Test suite for VHDL parser functionality."""

    def test_parse_entity_simple(self):
        """Test parsing a simple VHDL entity."""
        parser = VHDLParser()
        vhdl_code = """
        library IEEE;
        use IEEE.std_logic_1164.all;

        entity counter is
            port (
                clk     : in std_logic;
                rst     : in std_logic;
                enable  : in std_logic;
                count   : out std_logic_vector(7 downto 0)
            );
        end entity counter;
        """

        result = parser.parse_text(vhdl_code)

        # Verify entity was parsed
        assert result["entity"] is not None
        assert isinstance(result["entity"], IPCore)
        assert result["entity"].name == "counter"

        # Verify ports
        interface = result["entity"].interfaces[0]
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
        assert count_port.direction == Direction.OUT

    def test_parse_entity_and_architecture(self):
        """Test parsing both entity and architecture."""
        parser = VHDLParser()
        vhdl_code = """
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

        result = parser.parse_text(vhdl_code)

        # Verify entity
        assert result["entity"] is not None
        assert result["entity"].name == "counter"

        # Verify architecture
        assert result["architecture"] is not None
        assert result["architecture"]["name"] == "behavioral"
        assert result["architecture"]["entity"] == "counter"

    def test_roundtrip_entity(self):
        """Test roundtrip: parse a VHDL entity and regenerate it."""
        parser = VHDLParser()
        generator = VHDLGenerator()

        # Original VHDL code (simplified for comparison)
        original_vhdl = """
entity counter is
    port (
        clk     : in std_logic;
        rst     : in std_logic;
        enable  : in std_logic;
        count   : out std_logic_vector(7 downto 0)
    );
end entity counter;
        """.strip()

        # Parse the VHDL code
        result = parser.parse_text(original_vhdl)
        ip_core = result["entity"]

        # Regenerate VHDL code from the parsed entity
        regenerated_vhdl = generator.generate_entity(ip_core).strip()

        # Normalize whitespace for comparison
        norm_original = self._normalize_whitespace(original_vhdl)
        norm_regenerated = self._normalize_whitespace(regenerated_vhdl)

        # Compare the essential parts
        assert "entity counter is" in norm_regenerated
        assert "port (" in norm_regenerated
        assert "clk : in std_logic" in norm_regenerated
        assert "rst : in std_logic" in norm_regenerated
        assert "enable : in std_logic" in norm_regenerated
        assert "count : out std_logic_vector(7 downto 0)" in norm_regenerated
        assert "end entity counter" in norm_regenerated

    def _normalize_whitespace(self, text):
        """Normalize whitespace for comparison."""
        return ' '.join(text.replace("\n", " ").split())
