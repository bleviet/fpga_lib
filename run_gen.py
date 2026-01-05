
import sys
import yaml
import os
from fpga_lib.model.core import IpCore
from fpga_lib.generator.hdl.vhdl_generator import VHDLGenerator

from fpga_lib.parser.yaml.ip_core_parser import YamlIpCoreParser

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_gen.py <ip_core.yaml>")
        sys.exit(1)

    yaml_path = sys.argv[1]
    
    print(f"Loading IP Core from {yaml_path}...")
    
    # Use IpCoreParser to handle imports and normalization
    parser = YamlIpCoreParser()
    try:
        ip_core = parser.parse_file(yaml_path)
    except Exception as e:
        print(f"Error parsing IP Core: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    print(f"Generating for {ip_core.vlnv.name}...")
    
    gen = VHDLGenerator()
    
    # Generate generated HDL
    # Note: 'generate_all' returns dict of {filename: content}
    hdl_files = gen.generate_all(ip_core, bus_type='axil', include_regfile=True)
    
    # Generate Vendor integration
    vendor_files = gen.generate_vendor_files(ip_core, vendor='both', bus_type='axil')
    
    # Generate Testbench (includes memmap.yml now!)
    tb_files = gen.generate_testbench(ip_core, bus_type='axil')
    
    # Output dirs
    base_dir = os.path.dirname(yaml_path)
    rtl_dir = os.path.join(base_dir, 'rtl')
    tb_dir = os.path.join(base_dir, 'tb')
    intel_dir = os.path.join(base_dir, 'intel')
    xilinx_dir = os.path.join(base_dir, 'xilinx')
    
    os.makedirs(rtl_dir, exist_ok=True)
    os.makedirs(tb_dir, exist_ok=True)
    os.makedirs(intel_dir, exist_ok=True)
    os.makedirs(xilinx_dir, exist_ok=True)
    
    # Write HDL
    for fname, content in hdl_files.items():
        with open(os.path.join(rtl_dir, fname), 'w') as f:
            f.write(content)
            print(f"Wrote {fname}")
            
    # Write Vendor
    for fname, content in vendor_files.items():
        if fname.endswith('.tcl'):
            path = os.path.join(intel_dir, fname)
        elif fname.endswith('.xml'):
            path = os.path.join(xilinx_dir, fname)
        else:
            path = os.path.join(base_dir, fname)
        
        with open(path, 'w') as f:
            f.write(content)
            print(f"Wrote {fname}")

    # Write TB
    for fname, content in tb_files.items():
        with open(os.path.join(tb_dir, fname), 'w') as f:
            f.write(content)
            print(f"Wrote {fname}")

    print("Generation Complete.")

if __name__ == "__main__":
    main()
