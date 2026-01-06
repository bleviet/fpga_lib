"""
Generate VHDL files from IP Core YAML specification.

Usage:
    python scripts/generate_vhdl.py <ip_core.yaml> [output_dir]
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fpga_lib.generator.hdl.vhdl_generator import VHDLGenerator
from fpga_lib.parser.yaml.ip_core_parser import YamlIpCoreParser


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_vhdl.py <ip_core.yaml> [output_dir]")
        sys.exit(1)

    yaml_path = sys.argv[1]

    # Optional: specify output directory, defaults to same directory as YAML
    if len(sys.argv) > 2:
        output_base = sys.argv[2]
    else:
        output_base = os.path.dirname(yaml_path)

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

    # Generate all files with structured layout (rtl/, tb/, intel/, xilinx/)
    all_files = gen.generate_all(
        ip_core,
        bus_type='axil',
        structured=True,
        vendor='both',
        include_testbench=True,
        include_regs=True
    )

    # Write files
    for filepath, content in all_files.items():
        full_path = os.path.join(output_base, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"Wrote {filepath}")

    # Update IP core YAML with fileSets
    yaml_path_abs = os.path.abspath(yaml_path)
    updated = gen.update_ipcore_filesets(
        yaml_path_abs,
        all_files,
        include_regs=True,
        vendor='both',
        include_testbench=True
    )

    if updated:
        print(f"\n✓ Updated {yaml_path} with fileSets")
    else:
        print(f"\n✓ FileSets in {yaml_path} are already up to date")

    print(f"\nGeneration Complete. Files written to: {output_base}")
    print(f"Total files: {len(all_files)}")
    print("\nDirectory structure:")
    print("  rtl/        - VHDL source files")
    print("  tb/         - Cocotb testbench files")
    print("  intel/      - Intel Platform Designer integration")
    print("  xilinx/     - Xilinx Vivado IP-XACT integration")

    print("Generation Complete.")

if __name__ == "__main__":
    main()
