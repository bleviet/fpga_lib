#!/usr/bin/env python3
"""
ipcore - IP Core scaffolding and generation tool.

Usage:
    python scripts/ipcore.py generate my_core.ip.yml --output ./generated
    python scripts/ipcore.py generate my_core.ip.yml --json --progress  # VS Code mode

Subcommands:
    generate    Generate VHDL/testbench from IP core YAML
    validate    Validate IP core YAML (future)
    new         Create new IP core from template (future)
"""
import sys
import os
import json
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fpga_lib.generator.hdl.vhdl_generator import VHDLGenerator
from fpga_lib.parser.yaml.ip_core_parser import YamlIpCoreParser

# Map YAML bus types to generator templates
BUS_TYPE_MAP = {
    'AXI4L': 'axil',
    'AXI4LITE': 'axil',
    'AXILITE': 'axil',
    'AVALONMM': 'avmm',
    'AVMM': 'avmm',
}


def get_bus_type(ip_core) -> str:
    """Extract bus type from IP core's bus interfaces."""
    for bus in ip_core.bus_interfaces:
        if bus.mode == 'slave' and bus.memory_map_ref:
            bus_type = bus.type.value if hasattr(bus.type, 'value') else str(bus.type)
            return BUS_TYPE_MAP.get(bus_type.upper(), 'axil')
    return 'axil'


def log(msg: str, use_progress: bool, use_json: bool):
    """Output progress message if enabled."""
    if use_progress and use_json:
        print(f"PROGRESS: {msg}", flush=True)
    elif use_progress:
        print(msg)


def cmd_generate(args):
    """Generate VHDL files from IP core YAML."""
    output_base = args.output or os.path.dirname(args.input)

    try:
        log("Parsing IP core YAML...", args.progress, args.json)
        ip_core = YamlIpCoreParser().parse_file(args.input)

        bus_type = get_bus_type(ip_core)
        log(f"Detected bus type: {bus_type}", args.progress, args.json)

        log("Generating VHDL files...", args.progress, args.json)
        gen = VHDLGenerator()
        all_files = gen.generate_all(
            ip_core,
            bus_type=bus_type,
            structured=True,
            vendor=args.vendor,
            include_testbench=args.testbench,
            include_regs=args.regs
        )

        log(f"Writing {len(all_files)} files...", args.progress, args.json)
        written = {}
        for filepath, content in all_files.items():
            full_path = os.path.join(output_base, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            Path(full_path).write_text(content)
            written[filepath] = full_path
            log(f"  Written: {filepath}", args.progress, args.json)

        # Update IP core YAML with fileSets
        if args.update_yaml:
            gen.update_ipcore_filesets(
                os.path.abspath(args.input),
                all_files,
                include_regs=args.regs,
                vendor=args.vendor,
                include_testbench=args.testbench
            )

        log("Generation complete!", args.progress, args.json)

        if args.json:
            # JSON output for VS Code integration
            print(json.dumps({
                'success': True,
                'files': written,
                'count': len(written),
                'busType': bus_type
            }))
        else:
            # Human-readable output
            print(f"\n✓ Generated {len(all_files)} files to: {output_base}")
            print("\nDirectory structure:")
            print("  rtl/        - VHDL source files")
            print("  tb/         - Cocotb testbench files")
            print("  intel/      - Intel Platform Designer integration")
            print("  xilinx/     - Xilinx Vivado IP-XACT integration")

    except Exception as e:
        if args.json:
            print(json.dumps({'success': False, 'error': str(e)}))
        else:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog='ipcore',
        description='IP Core scaffolding and generation tool'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # generate subcommand
    gen_parser = subparsers.add_parser('generate', help='Generate VHDL from IP core YAML')
    gen_parser.add_argument('input', help='IP core YAML file')
    gen_parser.add_argument('--output', '-o', help='Output directory (default: same as input)')
    gen_parser.add_argument('--vendor', default='both',
                            choices=['none', 'intel', 'xilinx', 'both'],
                            help='Vendor integration files to generate')
    gen_parser.add_argument('--testbench', action='store_true', default=True,
                            help='Generate cocotb testbench (default: True)')
    gen_parser.add_argument('--no-testbench', dest='testbench', action='store_false')
    gen_parser.add_argument('--regs', action='store_true', default=True,
                            help='Include standalone register bank')
    gen_parser.add_argument('--no-regs', dest='regs', action='store_false')
    gen_parser.add_argument('--update-yaml', action='store_true', default=True,
                            help='Update IP core YAML with fileSets')
    gen_parser.add_argument('--no-update-yaml', dest='update_yaml', action='store_false')
    gen_parser.add_argument('--json', action='store_true',
                            help='JSON output (for VS Code integration)')
    gen_parser.add_argument('--progress', action='store_true',
                            help='Enable progress output')
    gen_parser.set_defaults(func=cmd_generate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
