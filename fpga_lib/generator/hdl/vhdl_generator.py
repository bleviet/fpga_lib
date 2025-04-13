# fpga_lib/generator/hdl/vhdl_generator.py
from jinja2 import Environment, FileSystemLoader
from fpga_lib.core.ip_core import IPCore
from fpga_lib.core.data_types import DataType, BitType, VectorType, IntegerType
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

    # We can now directly use the ip_core.ports list, as it contains both user-defined
    # ports and interface signals.
    entity_ports = ip_core.ports

    # Process ports to extract the correct type information based on whether the type
    # is a string or a DataType object
    processed_ports = []
    
    for port in entity_ports:
        port_data = {
            "name": port['name'].lower(),
            "direction": port['direction'].lower(),
            "width": port.get('width', 1)
        }
        
        # Handle different types of port['type'] (string or DataType)
        if isinstance(port['type'], str):
            port_data["type"] = port['type'].lower()
        else:  # DataType object
            # Handle VectorType specifically
            if isinstance(port['type'], VectorType):
                port_data["type"] = "std_logic_vector"
                port_data["width"] = port['type'].width
            # Handle BitType specifically
            elif isinstance(port['type'], BitType):
                port_data["type"] = "std_logic"
            else:
                port_data["type"] = port['type'].name.lower()
                
        processed_ports.append(port_data)

    # Correctly set has_std_logic_vector based on vector types
    has_std_logic_vector = any(port["type"] == "std_logic_vector" for port in processed_ports)

    entity_template = env.get_template("entity.vhdl.j2")
    entity_data = {
        "entity_name": ip_core.name.lower(),
        "ports": processed_ports,
        "has_std_logic_vector": has_std_logic_vector
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