# fpga_lib/generator/hdl/vhdl_generator.py
from jinja2 import Environment, FileSystemLoader
from fpga_lib.core.ip_core import IPCore
import os

def generate_vhdl(ip_core: IPCore) -> str:
    """
    Generates VHDL code for a given IPCore object using Jinja2 templates.

    Args:
        ip_core (IPCore): The IP core for which to generate VHDL.

    Returns:
        str: The generated VHDL code.
    """
    # Get the directory of the current file
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    # Initialize the Jinja2 environment with the template directory
    env = Environment(loader=FileSystemLoader(template_dir))

    # Prepare data for the entity template
    entity_template = env.get_template("entity.vhdl.j2")
    entity_data = {
        "entity_name": ip_core.name.lower(),  # Convert entity name to lowercase
        "ports": [{"name": port['name'].lower(), "direction": port['direction'].lower(), "type": port['type'].lower(), "width": port.get('width', 1)} for port in ip_core.ports], # Convert port attributes to lowercase
        "has_std_logic_vector": any(port['type'].lower() == 'std_logic_vector' for port in ip_core.ports)
    }
    entity_code = entity_template.render(**entity_data)

    # Prepare data for the architecture template
    architecture_template = env.get_template("architecture.vhdl.j2")
    architecture_data = {
        "architecture_name": f"{ip_core.name.lower()}_arch", # Convert architecture name to lowercase
        "entity_name": ip_core.name.lower()                   # Convert entity name to lowercase
    }
    architecture_code = architecture_template.render(**architecture_data)

    return f"{entity_code.strip()}\n\n{architecture_code.strip()}"

if __name__ == '__main__':
    # Example usage
    from fpga_lib.core.ip_core import RAM

    ram_instance = RAM(name="My_RAM", depth=1024, width=32)
    ram_instance.add_port("CLK", "IN", "STD_LOGIC")
    ram_instance.add_port("ADDR", "IN", "STD_LOGIC_VECTOR", width=10)
    ram_instance.add_port("Din", "IN", "STD_LOGIC_VECTOR", width=32)
    ram_instance.add_port("Dout", "OUT", "STD_LOGIC_VECTOR", width=32)
    vhdl_code = generate_vhdl(ram_instance)
    print(vhdl_code)