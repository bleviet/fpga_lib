# tests/generator/hdl/test_vhdl_generator.py
import unittest
from fpga_lib.core.ip_core import IPCore
from fpga_lib.generator.hdl.vhdl_generator import generate_vhdl

class TestVHDLGenerator(unittest.TestCase):
    def test_generate_simple_entity(self):
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

if __name__ == '__main__':
    unittest.main()