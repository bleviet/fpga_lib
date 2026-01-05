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
    
    def _parse_bits(self, bits: str) -> dict:
        """Parse bit string [M:N] or [N] into offset and width."""
        import re
        if not bits:
            return {'offset': 0, 'width': 1}
        
        # Handle [M:N]
        match_range = re.search(r'\[(\d+):(\d+)\]', bits)
        if match_range:
            high = int(match_range.group(1))
            low = int(match_range.group(2))
            return {'offset': low, 'width': abs(high - low) + 1}
            
        # Handle [N]
        match_single = re.search(r'\[(\d+)\]', bits)
        if match_single:
            bit = int(match_single.group(1))
            return {'offset': bit, 'width': 1}
            
        return {'offset': 0, 'width': 1}

    def _prepare_registers(self, ip_core: IpCore) -> List[Dict[str, Any]]:
        """
        Extract and prepare register information from memory maps (recursively).
        """
        registers = []
        
        def process_register(reg, base_offset, prefix):
            current_offset = base_offset + (getattr(reg, 'address_offset', None) or getattr(reg, 'offset', None) or 0)
            reg_name = reg.name if hasattr(reg, 'name') else 'REG'
            
            # Check for nested registers (array/group)
            nested_regs = getattr(reg, 'registers', [])
            if nested_regs:
                count = getattr(reg, 'count', 1) or 1
                stride = getattr(reg, 'stride', 0) or 0
                
                for i in range(count):
                    instance_offset = current_offset + (i * stride)
                    instance_prefix = f"{prefix}{reg_name}_{i}_" if count > 1 else f"{prefix}{reg_name}_"
                    
                    for child in nested_regs:
                        process_register(child, instance_offset, instance_prefix)
                return

            # Leaf register processing
            fields = []
            for field in getattr(reg, 'fields', []):
                # Handle bit parsing
                bit_offset = getattr(field, 'bit_offset', None)
                bit_width = getattr(field, 'bit_width', None)
                
                if bit_offset is None or bit_width is None:
                    bits_str = getattr(field, 'bits', '') 
                    parsed = self._parse_bits(bits_str)
                    if bit_offset is None: bit_offset = parsed['offset']
                    if bit_width is None: bit_width = parsed['width']
                
                # Access normalization
                acc = getattr(field, 'access', 'read-write')
                acc_str = acc.value if hasattr(acc, 'value') else str(acc)
                reg_acc = getattr(reg, 'access', 'read-write')
                reg_acc_str = reg_acc.value if hasattr(reg_acc, 'value') else str(reg_acc)
                
                fields.append({
                    'name': field.name,
                    'offset': bit_offset,
                    'width': bit_width,
                    'access': acc_str.lower() if acc_str else reg_acc_str.lower(),
                    'reset_value': field.reset_value if getattr(field, 'reset_value', None) is not None else 0,
                    'description': getattr(field, 'description', '')
                })

            reg_acc = getattr(reg, 'access', 'read-write')
            reg_acc_str = reg_acc.value if hasattr(reg_acc, 'value') else str(reg_acc)

            registers.append({
                'name': prefix + reg_name,
                'offset': current_offset,
                'access': reg_acc_str.lower(),
                'description': getattr(reg, 'description', ''),
                'fields': fields
            })

        for mm in ip_core.memory_maps:
            for block in mm.address_blocks:
                block_offset = getattr(block, 'base_address', 0) or getattr(block, 'offset', 0) or 0
                for reg in block.registers:
                    process_register(reg, block_offset, "")
        
        return sorted(registers, key=lambda x: x['offset'])
    
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
        registers = self._prepare_registers(ip_core)
        
        sw_access = ['read-write', 'write-only', 'rw', 'wo']
        hw_access = ['read-only', 'ro']
        
        sw_registers = [r for r in registers if r['access'] in sw_access]
        hw_registers = [r for r in registers if r['access'] in hw_access]

        return {
            'entity_name': ip_core.vlnv.name.lower(),
            'registers': registers,
            'sw_registers': sw_registers,
            'hw_registers': hw_registers,
            'generics': self._prepare_generics(ip_core),
            'user_ports': self._prepare_user_ports(ip_core),
            'bus_type': bus_type,
            'data_width': 32,
            'addr_width': 8,
            'reg_width': 4,
            'memory_maps': ip_core.memory_maps,
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
    
    def generate_intel_hw_tcl(self, ip_core: IpCore, bus_type: str = 'axil') -> str:
        """Generate Intel Platform Designer _hw.tcl component file."""
        template = self.env.get_template('intel_hw_tcl.j2')
        context = self._get_template_context(ip_core, bus_type)
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
        vendor: str = 'both',
        bus_type: str = 'axil'
    ) -> Dict[str, str]:
        """
        Generate vendor-specific integration files.
        
        Args:
            ip_core: IP core definition
            vendor: 'intel', 'xilinx', or 'both'
            bus_type: Bus interface type
            
        Returns:
            Dictionary mapping filename to content
        """
        name = ip_core.vlnv.name.lower()
        files = {}
        
        if vendor in ['intel', 'both']:
            files[f"{name}_hw.tcl"] = self.generate_intel_hw_tcl(ip_core, bus_type)
        
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

    def generate_memmap_yaml(self, ip_core: IpCore) -> str:
        """Generate memory map YAML for Python driver."""
        template = self.env.get_template('memmap.yml.j2')
        context = self._get_template_context(ip_core)
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
            f"{name}_memmap.yml": self.generate_memmap_yaml(ip_core),
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
