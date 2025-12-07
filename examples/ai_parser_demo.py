#!/usr/bin/env python3
"""
Demo: AI-Powered VHDL Parser

This script demonstrates the VHDLAiParser that uses LLM to parse VHDL code,
providing intelligent parsing with automatic bus interface detection.

Usage:
    # Parse with Ollama (local, default)
    python ai_parser_demo.py examples/test_vhdl/axi_example_peripheral.vhd

    # Parse with OpenAI
    python ai_parser_demo.py examples/test_vhdl/axi_example_peripheral.vhd --provider openai

    # Parse with Gemini
    python ai_parser_demo.py examples/test_vhdl/axi_example_peripheral.vhd --provider gemini
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fpga_lib.parser.hdl.vhdl_ai_parser import VHDLAiParser, ParserConfig
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

console = Console()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI-Powered VHDL Parser Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "vhdl_file",
        type=Path,
        help="VHDL file to parse"
    )
    parser.add_argument(
        "--provider",
        choices=["ollama", "openai", "gemini"],
        default="ollama",
        help="LLM provider to use (default: ollama for local)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="LLM model name (default: provider-specific - gemma3:12b for ollama, gpt-4o-mini for openai, gemini-2.0-flash-exp for gemini)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: fail on parsing errors"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    return parser.parse_args()


def display_ip_core(ip_core):
    """Display parsed IP core information with rich formatting."""

    # Header
    console.print(Panel(
        f"[bold cyan]{ip_core.vlnv.name}[/bold cyan]\n"
        f"[dim]{ip_core.vlnv.full_name}[/dim]\n\n"
        f"{ip_core.description}",
        title="[bold]IP Core",
        border_style="cyan"
    ))

    # Parameters/Generics
    if ip_core.parameters:
        param_table = Table(title="Parameters/Generics", show_header=True)
        param_table.add_column("Name", style="yellow")
        param_table.add_column("Type", style="cyan")
        param_table.add_column("Default", style="green")

        for param in ip_core.parameters:
            param_table.add_row(
                param.name,
                param.data_type,
                str(param.value) if param.value else "-"
            )

        console.print(param_table)
        console.print()

    # Ports
    if ip_core.ports:
        port_table = Table(title="Ports", show_header=True)
        port_table.add_column("Name", style="yellow")
        port_table.add_column("Direction", style="magenta")
        port_table.add_column("Width", style="cyan")
        port_table.add_column("Physical", style="dim")

        for port in ip_core.ports:
            width_str = str(port.width) if port.width > 1 else "1"
            port_table.add_row(
                port.name,
                port.direction.value,
                width_str,
                port.physical_port
            )

        console.print(port_table)
        console.print()

    # Bus Interfaces (AI-detected)
    if ip_core.bus_interfaces:
        bus_table = Table(title="Bus Interfaces (AI-Detected)", show_header=True)
        bus_table.add_column("Name", style="yellow")
        bus_table.add_column("Type", style="cyan")
        bus_table.add_column("Mode", style="magenta")
        bus_table.add_column("Prefix", style="green")

        for bus_if in ip_core.bus_interfaces:
            bus_table.add_row(
                bus_if.name,
                bus_if.type,
                bus_if.mode,
                bus_if.physical_prefix
            )

        console.print(bus_table)
        console.print()

    # Summary
    summary = f"""
**Summary:**
- Ports: {len(ip_core.ports)}
- Parameters: {len(ip_core.parameters)}
- Bus Interfaces: {len(ip_core.bus_interfaces)}
"""
    console.print(Panel(Markdown(summary), title="Statistics", border_style="green"))


def main():
    """Main demo function."""
    args = parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Verify file exists
    if not args.vhdl_file.exists():
        console.print(f"[bold red]Error:[/bold red] File not found: {args.vhdl_file}")
        sys.exit(1)

    # Set provider-specific default models if not specified
    if args.model is None:
        if args.provider == "ollama":
            args.model = "gemma3:12b"
        elif args.provider == "openai":
            args.model = "gpt-5-nano"
        elif args.provider == "gemini":
            args.model = "gemini-2.5-flash-lite"

    # Show configuration
    config_info = f"""
**Parser Configuration:**
- LLM Provider: {args.provider}
- Model: {args.model}
- Strict Mode: {'Yes' if args.strict else 'No'}
"""
    console.print(Panel(Markdown(config_info), title="Configuration", border_style="blue"))
    console.print()

    # Create parser configuration
    config = ParserConfig(
        llm_provider=args.provider,
        llm_model=args.model,
        strict_mode=args.strict
    )

    # Parse VHDL file
    console.print(f"[bold]Parsing:[/bold] {args.vhdl_file}")
    console.print()

    try:
        parser = VHDLAiParser(config=config)

        # Check if provider is available before parsing
        if not parser.llm_parser.is_available():
            error_msg = f"[bold red]Error:[/bold red] LLM provider '{args.provider}' is not available.\n"

            if args.provider == "openai":
                error_msg += "\n[yellow]OpenAI requires an API key. Please:[/yellow]\n"
                error_msg += "1. Set OPENAI_API_KEY environment variable, or\n"
                error_msg += "2. Create a .env file with: OPENAI_API_KEY=your-key-here\n"
                error_msg += "\nGet your API key from: https://platform.openai.com/api-keys"
            elif args.provider == "gemini":
                error_msg += "\n[yellow]Gemini requires an API key. Please:[/yellow]\n"
                error_msg += "1. Set GEMINI_API_KEY environment variable, or\n"
                error_msg += "2. Create a .env file with: GEMINI_API_KEY=your-key-here\n"
                error_msg += "\nGet your API key from: https://aistudio.google.com/app/apikey"
            elif args.provider == "ollama":
                error_msg += "\n[yellow]Ollama requires a local server. Please:[/yellow]\n"
                error_msg += "1. Install Ollama from: https://ollama.ai\n"
                error_msg += "2. Start the server: ollama serve\n"
                error_msg += f"3. Pull the model: ollama pull {args.model}"

            console.print(error_msg)
            sys.exit(1)

        with console.status("[bold green]Parsing VHDL..."):
            ip_core = parser.parse_file(args.vhdl_file)

        # Display results
        display_ip_core(ip_core)

        # Show JSON output option
        console.print()
        console.print("[dim]Tip: You can export to JSON using ip_core.model_dump_json()[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if args.verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
