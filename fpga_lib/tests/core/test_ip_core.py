# tests/core/test_ip_core.py
import unittest
from fpga_lib.core.ip_core import IPCore, RAM, FIFO

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
        ip_core.add_port("clk", "input", "logic")
        self.assertEqual(len(ip_core.ports), 1)
        self.assertEqual(ip_core.ports[0]["name"], "clk")
        self.assertEqual(ip_core.ports[0]["direction"], "input")
        self.assertEqual(ip_core.ports[0]["type"], "logic")
        self.assertEqual(ip_core.ports[0]["width"], 1)
        ip_core.add_port("data_in", "input", "std_logic_vector", width=8)
        self.assertEqual(len(ip_core.ports), 2)
        self.assertEqual(ip_core.ports[1]["width"], 8)

    def test_ipcore_add_parameter(self):
        ip_core = IPCore(name="test_core")
        ip_core.add_parameter("ADDR_WIDTH", 10, "integer")
        self.assertEqual(len(ip_core.parameters), 1)
        self.assertEqual(ip_core.parameters["ADDR_WIDTH"]["value"], 10)
        self.assertEqual(ip_core.parameters["ADDR_WIDTH"]["type"], "integer")
        ip_core.add_parameter("DATA_WIDTH", 32)
        self.assertEqual(ip_core.parameters["DATA_WIDTH"]["value"], 32)
        self.assertIsNone(ip_core.parameters["DATA_WIDTH"].get("type"))

class TestRAM(unittest.TestCase):
    def test_ram_creation(self):
        ram = RAM(depth=1024, width=32)
        self.assertEqual(ram.vendor, "my_company")
        self.assertEqual(ram.library, "memory_blocks")
        self.assertEqual(ram.name, "single_port_ram")
        self.assertEqual(ram.version, "2.0")
        self.assertEqual(ram.depth, 1024)
        self.assertEqual(ram.width, 32)
        self.assertTrue(any(port['name'] == 'clk' for port in ram.ports))
        self.assertTrue(any(port['name'] == 'addr' and port['width'] == 10 for port in ram.ports))
        self.assertTrue(any(port['name'] == 'din' and port['width'] == 32 for port in ram.ports))
        self.assertTrue(any(port['name'] == 'dout' and port['width'] == 32 for port in ram.ports))

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
        self.assertTrue(any(port['name'] == 'clk' for port in fifo.ports))
        self.assertTrue(any(port['name'] == 'wr_en' for port in fifo.ports))
        self.assertTrue(any(port['name'] == 'rd_en' for port in fifo.ports))
        self.assertTrue(any(port['name'] == 'din' and port['width'] == 16 for port in fifo.ports))
        self.assertTrue(any(port['name'] == 'dout' and port['width'] == 16 for port in fifo.ports))
        self.assertTrue(any(port['name'] == 'full' for port in fifo.ports))
        self.assertTrue(any(port['name'] == 'empty' for port in fifo.ports))

if __name__ == '__main__':
    unittest.main()