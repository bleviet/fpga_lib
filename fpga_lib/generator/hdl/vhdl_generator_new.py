"""
VHDL code generator using the new modular template structure.

Generates:
- Package (types, records, conversion functions)
- Top-level (instantiates core + bus wrapper)
- Core (bus-agnostic logic)
- Bus wrapper (AXI-Lite or Avalon-MM)
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import os

from jinja2 import Environment, FileSystemLoader

from fpga_lib.model.core import IpCore
from fpga_lib.model.memory import MemoryMap, Register, BitField
from fpga_lib.generator.base_generator import BaseGenerator


class VHDLGenerator(BaseGenerator):
    """
    VHDL code generator for IP cores with memory-mapped registers.
    
    Generates modular VHDL code:
    - Package with register types, enumerations, and conversion functions
    - Top-level entity that instantiates core and bus wrapper
    - Core logic module (bus-agnostic)
    - Bus wrapper (AXI-Lite or Avalon-MM)
    """
    
    SUPPORTED_BUS_TYPES = ['axil', 'avmm']
    
    def __init__(self, template_dir: Optional[str] = None):
        """Initialize VHDL generator with templates."""
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), "templates")
        super().__init__(template_dir)
    
    def _prepare_registers(self, ip_core: IpCore) -> List[Dict[str, Any]]:
        """
        Extract and prepare register information from memory maps.
        
        Args:
            ip_core: IP core with memory maps
            
        Returns:
            List of register dictionaries for templates
        """
        registers = []
        
        for mm in ip_core.memory_maps:
            # Registers are inside address_blocks
            for block in mm.address_blocks:
                for reg in block.registers:
                    reg_dict = {
                        'name': reg.name,
                        'offset': reg.address_offset,
                        'access': reg.access.value if hasattr(reg.access, 'value') else str(reg.access),
                        'description': reg.description or '',
                        'fields': []
                    }
                    
                    for field in reg.fields:
                        field_dict = {
                            'name': field.name,
                            'offset': field.bit_offset,
                            'width': field.bit_width,
                            'access': field.access.value if hasattr(field.access, 'value') else str(field.access),
                            'reset_value': field.reset_value if field.reset_value else 0,
                            'description': field.description or ''
                        }
                        reg_dict['fields'].append(field_dict)
                    
                    registers.append(reg_dict)
        
        return registers
    
    def _prepare_generics(self, ip_core: IpCore) -> List[Dict[str, Any]]:
        """Prepare generics/parameters for templates."""
        generics = []
        for param in ip_core.parameters:
            generics.append({
                'name': param.name,
                'type': param.data_type.value if hasattr(param.data_type, 'value') else str(param.data_type),
                'default_value': param.value
            })
        return generics
    
    def _prepare_user_ports(self, ip_core: IpCore) -> List[Dict[str, Any]]:
        """Prepare user-defined ports (non-bus ports)."""
        ports = []
        for port in ip_core.ports:
            direction = port.direction.value if hasattr(port.direction, 'value') else str(port.direction)
            width = port.width if hasattr(port, 'width') else 1
            
            if width == 1:
                port_type = 'std_logic'
            else:
                port_type = f'std_logic_vector({width-1} downto 0)'
            
            ports.append({
                'name': port.name.lower(),
                'direction': direction.lower(),
                'type': port_type
            })
        return ports
    
    def _get_template_context(
        self, 
        ip_core: IpCore, 
        bus_type: str = 'axil'
    ) -> Dict[str, Any]:
        """Build common template context."""
        return {
            'entity_name': ip_core.vlnv.name.lower(),
            'registers': self._prepare_registers(ip_core),
            'generics': self._prepare_generics(ip_core),
            'user_ports': self._prepare_user_ports(ip_core),
            'bus_type': bus_type,
            'data_width': 32,
            'addr_width': 8,
            'reg_width': 4,
        }
    
    def generate_package(self, ip_core: IpCore) -> str:
        """Generate VHDL package with register types and conversion functions."""
        template = self.env.get_template('package.vhdl.j2')
        context = self._get_template_context(ip_core)
        return template.render(**context)
    
    def generate_top(self, ip_core: IpCore, bus_type: str = 'axil') -> str:
        """Generate top-level entity that instantiates core and bus wrapper."""
        if bus_type not in self.SUPPORTED_BUS_TYPES:
            raise ValueError(f"Unsupported bus type: {bus_type}. Supported: {self.SUPPORTED_BUS_TYPES}")
        
        template = self.env.get_template('top.vhdl.j2')
        context = self._get_template_context(ip_core, bus_type)
        return template.render(**context)
    
    def generate_core(self, ip_core: IpCore) -> str:
        """Generate core logic module (bus-agnostic)."""
        template = self.env.get_template('core.vhdl.j2')
        context = self._get_template_context(ip_core)
        return template.render(**context)
    
    def generate_bus_wrapper(self, ip_core: IpCore, bus_type: str) -> str:
        """Generate bus interface wrapper for register access."""
        if bus_type not in self.SUPPORTED_BUS_TYPES:
            raise ValueError(f"Unsupported bus type: {bus_type}. Supported: {self.SUPPORTED_BUS_TYPES}")
        
        template = self.env.get_template(f'bus_{bus_type}.vhdl.j2')
        context = self._get_template_context(ip_core, bus_type)
        return template.render(**context)
    
    def generate_register_file(self, ip_core: IpCore) -> str:
        """Generate standalone register file (bus-agnostic)."""
        template = self.env.get_template('register_file.vhdl.j2')
        context = self._get_template_context(ip_core)
        return template.render(**context)
    
    def generate_all(
        self, 
        ip_core: IpCore, 
        bus_type: str = 'axil',
        include_regfile: bool = False
    ) -> Dict[str, str]:
        """
        Generate all VHDL files for the IP core.
        
        Args:
            ip_core: IP core definition
            bus_type: Bus interface type ('axil' or 'avmm')
            include_regfile: Include standalone register file
            
        Returns:
            Dictionary mapping filename to content
        """
        name = ip_core.vlnv.name.lower()
        
        files = {
            f"{name}_pkg.vhd": self.generate_package(ip_core),
            f"{name}.vhd": self.generate_top(ip_core, bus_type),
            f"{name}_core.vhd": self.generate_core(ip_core),
            f"{name}_{bus_type}.vhd": self.generate_bus_wrapper(ip_core, bus_type),
        }
        
        if include_regfile:
            files[f"{name}_regfile.vhd"] = self.generate_register_file(ip_core)
        
        return files
    
    def generate_intel_hw_tcl(self, ip_core: IpCore) -> str:
        """Generate Intel Platform Designer _hw.tcl component file."""
        template = self.env.get_template('intel_hw_tcl.j2')
        context = self._get_template_context(ip_core, 'avmm')
        # Add VLNV info
        context['vendor'] = ip_core.vlnv.vendor
        context['library'] = ip_core.vlnv.library
        context['version'] = ip_core.vlnv.version
        context['description'] = ip_core.description if hasattr(ip_core, 'description') else ''
        context['author'] = ip_core.vlnv.vendor
        context['display_name'] = ip_core.vlnv.name.replace('_', ' ').title()
        return template.render(**context)
    
    def generate_xilinx_component_xml(self, ip_core: IpCore) -> str:
        """Generate Xilinx Vivado IP-XACT component.xml."""
        template = self.env.get_template('xilinx_component_xml.j2')
        context = self._get_template_context(ip_core, 'axil')
        # Add VLNV info
        context['vendor'] = ip_core.vlnv.vendor
        context['library'] = ip_core.vlnv.library
        context['version'] = ip_core.vlnv.version
        context['description'] = ip_core.description if hasattr(ip_core, 'description') else ''
        context['display_name'] = ip_core.vlnv.name.replace('_', ' ').title()
        return template.render(**context)
    
    def generate_vendor_files(
        self, 
        ip_core: IpCore, 
        vendor: str = 'both'
    ) -> Dict[str, str]:
        """
        Generate vendor-specific integration files.
        
        Args:
            ip_core: IP core definition
            vendor: 'intel', 'xilinx', or 'both'
            
        Returns:
            Dictionary mapping filename to content
        """
        name = ip_core.vlnv.name.lower()
        files = {}
        
        if vendor in ['intel', 'both']:
            files[f"{name}_hw.tcl"] = self.generate_intel_hw_tcl(ip_core)
        
        if vendor in ['xilinx', 'both']:
            files["component.xml"] = self.generate_xilinx_component_xml(ip_core)
        
        return files
    
    def generate_cocotb_test(self, ip_core: IpCore, bus_type: str = 'axil') -> str:
        """Generate cocotb Python test file."""
        template = self.env.get_template('cocotb_test.py.j2')
        context = self._get_template_context(ip_core, bus_type)
        return template.render(**context)
    
    def generate_cocotb_makefile(self, ip_core: IpCore, bus_type: str = 'axil') -> str:
        """Generate Makefile for cocotb simulation."""
        template = self.env.get_template('cocotb_makefile.j2')
        context = self._get_template_context(ip_core, bus_type)
        return template.render(**context)
    
    def generate_testbench(
        self, 
        ip_core: IpCore, 
        bus_type: str = 'axil'
    ) -> Dict[str, str]:
        """
        Generate testbench files for cocotb simulation.
        
        Args:
            ip_core: IP core definition
            bus_type: Bus interface type
            
        Returns:
            Dictionary mapping filename to content
        """
        name = ip_core.vlnv.name.lower()
        return {
            f"{name}_test.py": self.generate_cocotb_test(ip_core, bus_type),
            "Makefile": self.generate_cocotb_makefile(ip_core, bus_type),
        }


# Backward compatibility: standalone function
def generate_vhdl(ip_core: IpCore, bus_type: str = 'axil') -> Dict[str, str]:
    """
    Generate VHDL files for an IP core.
    
    Args:
        ip_core: IP core definition
        bus_type: Bus interface type
        
    Returns:
        Dictionary mapping filename to content
    """
    generator = VHDLGenerator()
    return generator.generate_all(ip_core, bus_type)
