# tests/generator/hdl/test_vhdl_generator.py
import unittest
from fpga_lib.core.ip_core import IPCore
from fpga_lib.generator.hdl.vhdl_generator import generate_vhdl
from fpga_lib.core.data_types import BitType, VectorType

class TestVHDLGenerator(unittest.TestCase):
    def test_generate_simple_entity(self):
        # Test with string data types
        simple_core = IPCore(name="simple_ip")
        simple_core.add_port("clk", "in", "std_logic")
        simple_core.add_port("rst", "in", "std_logic")

        expected_vhdl = """
library ieee;
use ieee.std_logic_1164.all;

entity simple_ip is
    port (
        clk : in std_logic;
        rst : in std_logic
    );
end entity simple_ip;

architecture simple_ip_arch of simple_ip is
begin
    -- Your architecture code goes here
end architecture simple_ip_arch;
        """.strip()

        generated_vhdl = generate_vhdl(simple_core)
        self.assertEqual(generated_vhdl, expected_vhdl)
        
    def test_generate_entity_with_datatype_objects(self):
        # Test with DataType objects
        complex_core = IPCore(name="complex_ip")
        complex_core.add_port("clk", "in", BitType())
        complex_core.add_port("data", "out", VectorType(width=8))

        expected_vhdl = """
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity complex_ip is
    port (
        clk : in std_logic;
        data : out std_logic_vector(7 downto 0)
    );
end entity complex_ip;

architecture complex_ip_arch of complex_ip is
begin
    -- Your architecture code goes here
end architecture complex_ip_arch;
        """.strip()

        generated_vhdl = generate_vhdl(complex_core)
        print("Generated VHDL:")
        print(generated_vhdl)
        for port in complex_core.ports:
            print(f"Port: {port.name}, Width: {port.width}, Type: {port.type}")
        self.assertEqual(generated_vhdl, expected_vhdl)

if __name__ == '__main__':
    unittest.main()