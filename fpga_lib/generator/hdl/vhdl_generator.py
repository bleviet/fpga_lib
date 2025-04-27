# fpga_lib/generator/hdl/vhdl_generator.py
from jinja2 import Environment, FileSystemLoader
from fpga_lib.core.ip_core import IPCore
from fpga_lib.core.data_types import DataType, BitType, VectorType, IntegerType
import os


class VHDLGenerator:
    """
    VHDL code generator class for generating VHDL entities and architectures.
    """
    
    def __init__(self):
        """Initialize the VHDL generator."""
        # Get the directory of the current file
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")
        # Initialize the Jinja2 environment with the template directory
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
    
    def generate_entity(self, ip_core: IPCore) -> str:
        """
        Generate VHDL entity declaration for the given IP core.
        
        Args:
            ip_core: IPCore object to generate VHDL for
            
        Returns:
            String containing the VHDL entity declaration
        """
        # Check if the IPCore has interfaces and get the default interface
        ports = []
        if hasattr(ip_core, 'interfaces') and ip_core.interfaces:
            # Use the first interface by default
            interface = ip_core.interfaces[0]
            ports = interface.ports
        elif hasattr(ip_core, 'ports'):
            # Legacy support for IPCore objects with direct ports
            ports = ip_core.ports
        else:
            # No ports found
            ports = []
            
        # Process ports to extract the correct type information
        processed_ports = [
            {
                "name": port.name.lower(),
                "direction": port.direction.value.lower() if hasattr(port.direction, "value") else str(port.direction).lower(),
                "type": self._get_port_type_string(port),
                "width": port.width
            }
            for port in ports
        ]
        
        # Correctly set has_std_logic_vector based on vector types
        has_std_logic_vector = any(
            isinstance(port.type, VectorType) if hasattr(port, 'type') else False
            for port in ports
        )
        
        entity_template = self.env.get_template("entity.vhdl.j2")
        entity_data = {
            "entity_name": ip_core.name.lower(),
            "ports": processed_ports,
            "has_std_logic_vector": has_std_logic_vector
        }
        
        return entity_template.render(**entity_data)
    
    def generate_architecture(self, ip_core: IPCore, arch_name: str = None) -> str:
        """
        Generate VHDL architecture for the given IP core.
        
        Args:
            ip_core: IPCore object to generate VHDL for
            arch_name: Optional architecture name (defaults to ip_core.name_arch)
            
        Returns:
            String containing the VHDL architecture
        """
        if not arch_name:
            arch_name = f"{ip_core.name.lower()}_arch"
            
        architecture_template = self.env.get_template("architecture.vhdl.j2")
        architecture_data = {
            "architecture_name": arch_name,
            "entity_name": ip_core.name.lower()
        }
        
        return architecture_template.render(**architecture_data)
    
    def generate_vhdl(self, ip_core: IPCore) -> str:
        """
        Generate complete VHDL code (entity and architecture) for the given IP core.
        
        Args:
            ip_core: IPCore object to generate VHDL for
            
        Returns:
            String containing the complete VHDL code
        """
        entity_code = self.generate_entity(ip_core)
        architecture_code = self.generate_architecture(ip_core)
        
        return f"{entity_code.strip()}\n\n{architecture_code.strip()}"
    
    def _get_port_type_string(self, port) -> str:
        """
        Get the VHDL type string for a port.
        
        Args:
            port: Port object
            
        Returns:
            String representation of the port type for VHDL
        """
        if hasattr(port, 'type'):
            port_type = port.type
            
            if hasattr(port_type, "to_vhdl"):
                return port_type.to_vhdl()
            elif isinstance(port_type, VectorType):
                return f"std_logic_vector({port.width - 1} downto 0)"
            elif isinstance(port_type, BitType):
                return "std_logic"
            elif hasattr(port_type, 'base_type') and hasattr(port_type.base_type, 'name'):
                # Handle case when type is DataType with base_type
                base_type_name = port_type.base_type.name.lower()
                if base_type_name == 'std_logic_vector':
                    range_constraint = port_type.range_constraint
                    return f"std_logic_vector({range_constraint})"
                else:
                    return base_type_name
            elif isinstance(port_type, str):
                return port_type.lower()
                
        # Default case for unknown types
        return "std_logic" if port.width == 1 else f"std_logic_vector({port.width - 1} downto 0)"


# Keep the original function for backward compatibility
def generate_vhdl(ip_core: IPCore) -> str:
    """
    Generates VHDL code for a given IPCore object using Jinja2 templates,
    including support for bus interfaces.

    Args:
        ip_core (IPCore): The IP core for which to generate VHDL.

    Returns:
        str: The generated VHDL code.
    """
    generator = VHDLGenerator()
    return generator.generate_vhdl(ip_core)


if __name__ == '__main__':
    # Example usage
    from fpga_lib.core.ip_core import RAM, FIFO

    ram_instance = RAM(depth=1024, width=32)
    vhdl_code_ram = generate_vhdl(ram_instance)
    print("VHDL for RAM with AXI Lite:\n", vhdl_code_ram)

    fifo_instance = FIFO(depth=64, width=16)
    vhdl_code_fifo = generate_vhdl(fifo_instance)
    print("\nVHDL for FIFO with AXI Stream:\n", vhdl_code_fifo)