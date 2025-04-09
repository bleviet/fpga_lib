# fpga_lib/generator/hdl/vhdl_generator.py
from jinja2 import Environment, FileSystemLoader
from fpga_lib.core.ip_core import IPCore
from fpga_lib.core.interface import AXILiteInterface, AXIStreamInterface, AvalonMMInterface, AvalonSTInterface
import os

def generate_vhdl(ip_core: IPCore) -> str:
    """
    Generates VHDL code for a given IPCore object using Jinja2 templates,
    including support for bus interfaces.

    Args:
        ip_core (IPCore): The IP core for which to generate VHDL.

    Returns:
        str: The generated VHDL code.
    """
    # Get the directory of the current file
    template_dir = os.path.join(os.path.dirname(__file__), "templates")

    # Initialize the Jinja2 environment with the template directory
    env = Environment(loader=FileSystemLoader(template_dir))

    entity_ports = list(ip_core.ports)

    # Add interface signals to the entity ports
    for interface in ip_core.interfaces:
        if isinstance(interface, AXILiteInterface):
            entity_ports.extend([
                {"name": f"{interface.name}_aclk", "direction": "in", "type": "std_logic"},
                {"name": f"{interface.name}_aresetn", "direction": "in", "type": "std_logic"},
                {"name": f"{interface.name}_awaddr", "direction": "in", "type": "std_logic_vector", "width": interface.address_width},
                {"name": f"{interface.name}_awvalid", "direction": "in", "type": "std_logic"},
                {"name": f"{interface.name}_awready", "direction": "out", "type": "std_logic"},
                {"name": f"{interface.name}_wdata", "direction": "in", "type": "std_logic_vector", "width": interface.data_width},
                {"name": f"{interface.name}_wstrb", "direction": "in", "type": "std_logic_vector", "width": interface.data_width // 8},
                {"name": f"{interface.name}_wvalid", "direction": "in", "type": "std_logic"},
                {"name": f"{interface.name}_wready", "direction": "out", "type": "std_logic"},
                {"name": f"{interface.name}_bresp", "direction": "out", "type": "std_logic_vector", "width": 2},
                {"name": f"{interface.name}_bvalid", "direction": "out", "type": "std_logic"},
                {"name": f"{interface.name}_bready", "direction": "in", "type": "std_logic"},
                {"name": f"{interface.name}_araddr", "direction": "in", "type": "std_logic_vector", "width": interface.address_width},
                {"name": f"{interface.name}_arvalid", "direction": "in", "type": "std_logic"},
                {"name": f"{interface.name}_arready", "direction": "out", "type": "std_logic"},
                {"name": f"{interface.name}_rdata", "direction": "out", "type": "std_logic_vector", "width": interface.data_width},
                {"name": f"{interface.name}_rresp", "direction": "out", "type": "std_logic_vector", "width": 2},
                {"name": f"{interface.name}_rvalid", "direction": "out", "type": "std_logic"},
                {"name": f"{interface.name}_rready", "direction": "in", "type": "std_logic"},
            ])
        elif isinstance(interface, AXIStreamInterface):
            entity_ports.extend([
                {"name": f"{interface.name}_aclk", "direction": "in", "type": "std_logic"},
                {"name": f"{interface.name}_aresetn", "direction": "in", "type": "std_logic"},
                {"name": f"{interface.name}_tdata", "direction": "in", "type": "std_logic_vector", "width": interface.data_width},
                {"name": f"{interface.name}_tvalid", "direction": "in", "type": "std_logic"},
                {"name": f"{interface.name}_tready", "direction": "out", "type": "std_logic"},
                {"name": f"{interface.name}_tlast", "direction": "in", "type": "std_logic"},
                {"name": f"{interface.name}_tuser", "direction": "in", "type": "std_logic_vector", "width": interface.user_width},
                {"name": f"{interface.name}_tstrb", "direction": "in", "type": "std_logic_vector", "width": interface.data_width // 8},
                {"name": f"{interface.name}_tkeep", "direction": "in", "type": "std_logic_vector", "width": interface.data_width // 8},
                {"name": f"{interface.name}_tid", "direction": "in", "type": "std_logic_vector", "width": interface.tid_width},
                {"name": f"{interface.name}_tdest", "direction": "in", "type": "std_logic_vector", "width": interface.tdest_width},
            ])
        elif isinstance(interface, AvalonMMInterface):
            # ... (Avalon MM signals)
            pass
        elif isinstance(interface, AvalonSTInterface):
            # ... (Avalon ST signals)
            pass

    entity_template = env.get_template("entity.vhdl.j2")
    entity_data = {
        "entity_name": ip_core.name.lower(),
        "ports": [{"name": port['name'].lower(), "direction": port['direction'].lower(), "type": port['type'].lower(), "width": port.get('width', 1)} for port in entity_ports],
        "has_std_logic_vector": any(port['type'].lower() == 'std_logic_vector' for port in entity_ports)
    }
    entity_code = entity_template.render(**entity_data)

    architecture_template = env.get_template("architecture.vhdl.j2")
    architecture_data = {
        "architecture_name": f"{ip_core.name.lower()}_arch",
        "entity_name": ip_core.name.lower()
    }
    architecture_code = architecture_template.render(**architecture_data)

    return f"{entity_code.strip()}\n\n{architecture_code.strip()}"

if __name__ == '__main__':
    # Example usage
    from fpga_lib.core.ip_core import RAM, FIFO

    ram_instance = RAM(depth=1024, width=32)
    vhdl_code_ram = generate_vhdl(ram_instance)
    print("VHDL for RAM with AXI Lite:\n", vhdl_code_ram)

    fifo_instance = FIFO(depth=64, width=16)
    vhdl_code_fifo = generate_vhdl(fifo_instance)
    print("\nVHDL for FIFO with AXI Stream:\n", vhdl_code_fifo)