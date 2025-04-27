# tests/core/test_ip_core.py
import unittest
from fpga_lib.core.ip_core import IPCore, RAM, FIFO, Parameter
from fpga_lib.core.port import Port, PortDirection
from fpga_lib.core.interface import Interface

class TestIPCore(unittest.TestCase):
    def test_ipcore_creation(self):
        ip_core = IPCore(name="generic_ip")
        self.assertEqual(ip_core.vendor, "")
        self.assertEqual(ip_core.library, "")
        self.assertEqual(ip_core.name, "generic_ip")
        self.assertEqual(ip_core.version, "1.0")
        self.assertEqual(ip_core.description, "")
        self.assertEqual(ip_core.ports, [])
        self.assertEqual(ip_core.parameters, {})

    def test_ipcore_add_port(self):
        ip_core = IPCore(name="test_core")
        ip_core.add_port("clk", "in", "std_logic")
        self.assertEqual(len(ip_core.ports), 1)
        self.assertEqual(ip_core.ports[0], Port(name="clk", direction=PortDirection.IN, type="std_logic", width=1))

        ip_core.add_port("data_in", "in", "std_logic_vector", width=8)
        self.assertEqual(len(ip_core.ports), 2)
        self.assertEqual(ip_core.ports[1], Port(name="data_in", direction=PortDirection.IN, type="std_logic_vector", width=8))

    def test_ipcore_add_port_all_directions(self):
        ip_core = IPCore(name="test_core")
        # Test all VHDL directions
        ip_core.add_port("a", "in", "std_logic")
        ip_core.add_port("b", "out", "std_logic")
        ip_core.add_port("c", "inout", "std_logic")
        ip_core.add_port("d", "buffer", "std_logic")
        self.assertEqual(len(ip_core.ports), 4)
        self.assertEqual(ip_core.ports[0].direction, PortDirection.IN)
        self.assertEqual(ip_core.ports[1].direction, PortDirection.OUT)
        self.assertEqual(ip_core.ports[2].direction, "inout")
        self.assertEqual(ip_core.ports[3].direction, "buffer")

    def test_ipcore_add_port_case_insensitive(self):
        ip_core = IPCore(name="test_core")
        ip_core.add_port("clk", "in", "std_logic")
        with self.assertRaises(ValueError):
            ip_core.add_port("CLK", "in", "std_logic")  # Should raise due to duplicate (case-insensitive)

    def test_ipcore_add_port_with_default(self):
        ip_core = IPCore(name="test_core")
        ip_core.add_port("rst", "in", "std_logic", default='0')
        port = ip_core.get_port("rst")
        self.assertIsNotNone(port)
        self.assertTrue(hasattr(port, 'default'))
        self.assertEqual(port.default.value, '0')

    def test_ipcore_add_parameter(self):
        ip_core = IPCore(name="test_core")
        ip_core.add_parameter("ADDR_WIDTH", 10, "integer")
        self.assertEqual(len(ip_core.parameters), 1)
        self.assertIsInstance(ip_core.parameters["ADDR_WIDTH"], Parameter)
        self.assertEqual(ip_core.parameters["ADDR_WIDTH"].value, 10)
        self.assertEqual(ip_core.parameters["ADDR_WIDTH"].type, "integer")
        ip_core.add_parameter("DATA_WIDTH", 32)
        self.assertIsInstance(ip_core.parameters["DATA_WIDTH"], Parameter)
        self.assertEqual(ip_core.parameters["DATA_WIDTH"].value, 32)
        self.assertIsNone(ip_core.parameters["DATA_WIDTH"].type)

    def test_ipcore_add_parameter_dataclass(self):
        ip_core = IPCore(name="test_core")
        ip_core.add_parameter("ADDR_WIDTH", 10, "integer")
        self.assertIn("ADDR_WIDTH", ip_core.parameters)
        param = ip_core.parameters["ADDR_WIDTH"]
        self.assertIsInstance(param, Parameter)
        self.assertEqual(param.value, 10)
        self.assertEqual(param.type, "integer")

    def test_ipcore_parameter_case_insensitive(self):
        ip_core = IPCore(name="test_core")
        ip_core.add_parameter("FOO", 1)
        with self.assertRaises(ValueError):
            ip_core.add_parameter("foo", 2)

    def test_ipcore_error_collection(self):
        ip_core = IPCore(name="test_core")
        try:
            ip_core.add_port("clk", "invalid_dir", "std_logic")
        except ValueError:
            pass
        self.assertTrue(any("Invalid port direction" in e for e in ip_core.errors))
        ip_core.add_port("clk", "in", "std_logic")
        try:
            ip_core.add_port("clk", "in", "std_logic")
        except ValueError:
            pass
        self.assertTrue(any("Duplicate port name" in e for e in ip_core.errors))

    def test_ipcore_remove_interface_and_ports(self):
        ip_core = IPCore(name="test_core")
        iface = Interface(name="bus", interface_type="custom", ports=[
            Port(name="bus_clk", direction=PortDirection.IN, type="std_logic", width=1)
        ])
        ip_core.add_interface(iface)
        self.assertTrue(any(p.name == "bus_clk" for p in ip_core.ports))
        ip_core.remove_interface(iface)
        self.assertFalse(any(p.name == "bus_clk" for p in ip_core.ports))
        self.assertNotIn(iface, ip_core.interfaces)

    def test_ipcore_to_dict(self):
        ip_core = IPCore(name="test_core")
        ip_core.add_port("clk", "in", "std_logic")
        ip_core.add_parameter("WIDTH", 8, "integer")
        d = ip_core.to_dict()
        self.assertEqual(d["name"], "test_core")
        self.assertIn("clk", [p["name"] for p in d["ports"]])
        self.assertIn("WIDTH", d["parameters"])

    def test_ipcore_modify_port(self):
        ip_core = IPCore(name="test_core")
        ip_core.add_port("data", "in", "std_logic_vector", width=8)
        ip_core.modify_port("data", direction="out", width=16, default='Z')
        port = ip_core.get_port("data")
        self.assertEqual(port.direction, PortDirection.OUT)
        self.assertEqual(port.width, 16)
        self.assertEqual(port.default.value, 'Z')

class TestRAM(unittest.TestCase):
    def test_ram_creation(self):
        ram = RAM(depth=1024, width=32)
        self.assertEqual(ram.vendor, "my_company")
        self.assertEqual(ram.library, "memory_blocks")
        self.assertEqual(ram.name, "single_port_ram")
        self.assertEqual(ram.version, "2.0")
        self.assertEqual(ram.depth, 1024)
        self.assertEqual(ram.width, 32)
        self.assertTrue(any(port.name == 'clk' for port in ram.ports))
        self.assertTrue(any(port.name == 'addr' and port.width == 10 for port in ram.ports))
        self.assertTrue(any(port.name == 'din' and port.width == 32 for port in ram.ports))
        self.assertTrue(any(port.name == 'dout' and port.width == 32 for port in ram.ports))

class TestFIFO(unittest.TestCase):
    def test_fifo_creation(self):
        fifo = FIFO(depth=64, width=16, almost_full_threshold=50)
        self.assertEqual(fifo.vendor, "my_company")
        self.assertEqual(fifo.library, "fifo_blocks")
        self.assertEqual(fifo.name, "standard_fifo")
        self.assertEqual(fifo.version, "1.1")
        self.assertEqual(fifo.depth, 64)
        self.assertEqual(fifo.width, 16)
        self.assertEqual(fifo.almost_full_threshold, 50)
        self.assertTrue(any(port.name == 'clk' for port in fifo.ports))
        self.assertTrue(any(port.name == 'wr_en' for port in fifo.ports))
        self.assertTrue(any(port.name == 'rd_en' for port in fifo.ports))
        self.assertTrue(any(port.name == 'din' and port.width == 16 for port in fifo.ports))
        self.assertTrue(any(port.name == 'dout' and port.width == 16 for port in fifo.ports))
        self.assertTrue(any(port.name == 'full' for port in fifo.ports))
        self.assertTrue(any(port.name == 'empty' for port in fifo.ports))

if __name__ == '__main__':
    unittest.main()