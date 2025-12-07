# AI-Enhanced VHDL Parser

This directory contains the new AI-enhanced VHDL parser that combines deterministic parsing with optional LLM-powered intelligence.

## Architecture

The parser follows a **hybrid intelligence** approach:

```
┌────────────────────────────────────────────────────┐
│                    Input VHDL                      │
└──────────────┬─────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│  Phase 1: pyparsing (Deterministic)              │
│  • Extract entity, ports, generics               │
│  • Reliable structure extraction                 │
│  • Always succeeds (or fails clearly)            │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│  Phase 2: LLM (Intelligent - OPTIONAL)           │
│  • Analyze comments for bus interfaces           │
│  • Infer missing metadata                        │
│  • Generate documentation                        │
│  • Graceful fallback if unavailable              │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│         Pydantic IpCore Model                    │
│         (Validated Canonical Data)               │
└──────────────────────────────────────────────────┘
```

## Features

### ✅ Always Available (Phase 1)
- Entity name extraction
- Port parsing (name, direction, type, width)
- Generic/parameter extraction
- Comment extraction
- Robust error handling

### 🤖 AI-Enhanced (Phase 2 - Optional)
- **Bus Interface Detection**: Automatically identifies AXI, Avalon, Wishbone, etc.
- **Documentation Generation**: Creates descriptions from code context
- **Signal Grouping**: Groups related signals into logical interfaces
- **Comment Analysis**: Extracts semantic meaning from comments

## Usage

### Basic Usage (No AI)

```python
from fpga_lib.parser.hdl.vhdl_ai_parser import VHDLAiParser, ParserConfig

# Default configuration (AI disabled)
parser = VHDLAiParser()
ip_core = parser.parse_file("my_design.vhd")

print(f"Entity: {ip_core.vlnv.name}")
print(f"Ports: {len(ip_core.ports)}")
```

### AI-Enhanced Parsing

```python
from fpga_lib.parser.hdl.vhdl_ai_parser import VHDLAiParser, ParserConfig

# Enable AI with Ollama (local, no API key needed)
config = ParserConfig(
    enable_llm=True,
    llm_provider="ollama",
    llm_model="llama3.3:latest"
)

parser = VHDLAiParser(config=config)
ip_core = parser.parse_file("axi_peripheral.vhd")

# AI automatically detects bus interfaces!
for bus_if in ip_core.bus_interfaces:
    print(f"Found {bus_if.type} interface: {bus_if.name}")
```

### Using OpenAI or Gemini

```python
# OpenAI (requires API key in .env)
config = ParserConfig(
    enable_llm=True,
    llm_provider="openai",
    llm_model="gpt-4o-mini"
)

# Gemini (requires API key in .env)
config = ParserConfig(
    enable_llm=True,
    llm_provider="gemini",
    llm_model="gemini-2.0-flash"
)
```

## Demo Script

Run the included demo script:

```bash
# Without AI (traditional parsing)
python examples/ai_parser_demo.py examples/test_vhdl/axi_example_peripheral.vhd

# With AI enhancement (Ollama local)
python examples/ai_parser_demo.py examples/test_vhdl/axi_example_peripheral.vhd --enable-ai

# With AI enhancement (OpenAI)
python examples/ai_parser_demo.py examples/test_vhdl/axi_example_peripheral.vhd \
    --enable-ai --provider openai --model gpt-4o-mini

# Verbose output
python examples/ai_parser_demo.py examples/test_vhdl/axi_example_peripheral.vhd \
    --enable-ai --verbose
```

## Configuration Options

### ParserConfig

```python
class ParserConfig(BaseModel):
    # AI Settings
    enable_llm: bool = False              # Enable AI enhancements
    llm_provider: str = "ollama"          # Provider: ollama, openai, gemini
    llm_model: str = "llama3.3:latest"    # Model name
    
    # Default VLNV components
    default_vendor: str = "unknown.vendor"
    default_library: str = "work"
    default_version: str = "1.0.0"
    default_api_version: str = "fpga-lib/v1.0"
    
    # Parser behavior
    strict_mode: bool = False              # Fail on errors vs graceful degradation
    extract_comments: bool = True          # Extract comments for AI analysis
```

## Output: Pydantic IpCore Model

The parser returns a fully validated `IpCore` model from `fpga_lib.model.core`:

```python
ip_core = parser.parse_file("design.vhd")

# Access metadata
print(ip_core.vlnv.full_name)          # "vendor:library:name:version"
print(ip_core.description)             # AI-generated description

# Access ports
for port in ip_core.ports:
    print(f"{port.name}: {port.direction.value} [{port.width} bits]")

# Access parameters/generics
for param in ip_core.parameters:
    print(f"{param.name} = {param.value} ({param.data_type})")

# Access bus interfaces (AI-detected)
for bus_if in ip_core.bus_interfaces:
    print(f"{bus_if.name}: {bus_if.type} {bus_if.mode}")

# Export to JSON
json_str = ip_core.model_dump_json(indent=2)

# Validate and modify
ip_core.description = "Updated description"
# Pydantic automatically validates!
```

## AI Bus Interface Detection

The AI analyzer can detect these bus types:

| Bus Type | Signals Detected |
|----------|-----------------|
| **AXI4_LITE** | awaddr, awvalid, wdata, bresp, araddr, rdata, etc. |
| **AXI_STREAM** | tdata, tvalid, tready, tlast, tkeep, tstrb |
| **AVALON_MM** | address, writedata, readdata, write, read, waitrequest |
| **WISHBONE** | adr, dat, we, cyc, stb, ack |

The analyzer looks for:
1. **Signal naming patterns**: Prefixes like `s_axi_`, `m_axis_`, `avmm_`
2. **Comments**: Text like "AXI4-Lite slave interface"
3. **Port groupings**: Related signals appearing together

## Requirements

### Core Requirements
- Python 3.8+
- pyparsing
- pydantic
- rich (for demo script)

### AI Enhancement Requirements (Optional)
- llm_core (from llm-playground repository)
- For Ollama: Local Ollama installation
- For OpenAI: API key in `.env`
- For Gemini: API key in `.env`

## Installation

1. **Install core dependencies:**
   ```bash
   pip install pyparsing pydantic rich
   ```

2. **For AI features (optional):**
   ```bash
   # Add llm_core to Python path or install locally
   cd ../llm-playground/llm_core
   pip install -e .
   
   # For local AI (recommended):
   # Install Ollama from https://ollama.ai
   ollama pull llama3.3:latest
   
   # For cloud AI:
   # Create .env file with API keys
   echo "OPENAI_API_KEY=your-key" >> .env
   echo "GOOGLE_API_KEY=your-key" >> .env
   ```

## Examples

### Example 1: Simple Parsing

```python
from fpga_lib.parser.hdl.vhdl_ai_parser import VHDLAiParser

parser = VHDLAiParser()

vhdl_code = """
entity my_counter is
    generic (
        WIDTH : integer := 32
    );
    port (
        clk : in std_logic;
        reset : in std_logic;
        enable : in std_logic;
        count : out std_logic_vector(WIDTH-1 downto 0)
    );
end entity my_counter;
"""

ip_core = parser.parse_text(vhdl_code)
print(f"Parsed: {ip_core.vlnv.name}")
print(f"Ports: {[p.name for p in ip_core.ports]}")
print(f"Generics: {[p.name for p in ip_core.parameters]}")
```

### Example 2: AI-Enhanced Parsing

```python
from fpga_lib.parser.hdl.vhdl_ai_parser import VHDLAiParser, ParserConfig
from pathlib import Path

config = ParserConfig(enable_llm=True)
parser = VHDLAiParser(config=config)

# Parse AXI peripheral
ip_core = parser.parse_file(Path("examples/test_vhdl/axi_example_peripheral.vhd"))

# AI automatically detects AXI interface!
if ip_core.bus_interfaces:
    bus_if = ip_core.bus_interfaces[0]
    print(f"Detected: {bus_if.type} {bus_if.mode} interface")
    print(f"Name: {bus_if.name}")
    print(f"Prefix: {bus_if.physical_prefix}")
```

### Example 3: Error Handling

```python
from fpga_lib.parser.hdl.vhdl_ai_parser import VHDLAiParser, ParserConfig

# Strict mode: fails on errors
config = ParserConfig(strict_mode=True)
parser = VHDLAiParser(config=config)

try:
    ip_core = parser.parse_file("broken.vhd")
except ValueError as e:
    print(f"Parse error: {e}")

# Graceful mode: returns minimal valid core
config = ParserConfig(strict_mode=False)
parser = VHDLAiParser(config=config)
ip_core = parser.parse_file("broken.vhd")  # Won't raise exception
```

## Benefits Over Old Parser

| Feature | Old Parser | AI Parser |
|---------|-----------|-----------|
| **Data Model** | Custom classes | Pydantic models (validated) |
| **Bus Detection** | Manual annotation | Automatic (AI) |
| **Documentation** | Manual | Auto-generated (AI) |
| **Validation** | Basic | Comprehensive (Pydantic) |
| **Export** | Custom | JSON via Pydantic |
| **Type Safety** | Runtime errors | Compile-time hints |
| **Extensibility** | Tightly coupled | Clean interfaces |

## Design Philosophy

1. **Reliability First**: Phase 1 (pyparsing) always works
2. **Intelligence Second**: Phase 2 (LLM) enhances but doesn't break
3. **Graceful Degradation**: Works without AI, better with AI
4. **Local-First Privacy**: Ollama runs locally, no data leaves your machine
5. **Educational**: Demonstrates practical AI integration patterns

## Troubleshooting

### AI Not Working?

```python
from fpga_lib.parser.hdl.vhdl_ai_parser import VhdlAiAnalyzer

analyzer = VhdlAiAnalyzer(provider_name="ollama")
if analyzer.is_available():
    print("✅ AI available")
else:
    print("❌ AI not available")
    print("Check: 1) llm_core installed, 2) Ollama running, 3) API keys set")
```

### Parsing Fails?

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

parser = VHDLAiParser()
ip_core = parser.parse_file("design.vhd")  # Will show detailed logs
```

### Bus Interfaces Not Detected?

Ensure your VHDL has:
1. Clear naming conventions (`s_axi_*`, `m_axis_*`)
2. Comments describing interfaces
3. Standard signal names

## Future Enhancements

- [ ] Support for multiple entities per file
- [ ] Architecture body parsing
- [ ] Package parsing
- [ ] VHDL-2008 features
- [ ] Code quality suggestions from AI
- [ ] Test bench generation
- [ ] IP-XACT export

## Related Files

- `vhdl_ai_parser.py` - Main parser implementation
- `../../model/` - Pydantic data models
- `../../../llm-playground/llm_core/` - LLM provider abstraction
- `../../examples/ai_parser_demo.py` - Demo script
- `../../examples/test_vhdl/` - Test VHDL files

## Contributing

When adding features:
1. Maintain Phase 1 (pyparsing) reliability
2. Make Phase 2 (LLM) optional
3. Add tests for both modes
4. Update this README

## License

See project root LICENSE file.
