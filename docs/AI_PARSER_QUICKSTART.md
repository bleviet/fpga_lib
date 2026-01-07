# AI-Enhanced VHDL Parser - Quick Start

## What Was Created

A new AI-enhanced VHDL parser that combines deterministic pyparsing with optional LLM intelligence.

### Files Created

```
ipcore_lib/
├── parser/hdl/
│   ├── vhdl_ai_parser.py           # Main AI parser (780+ lines)
│   └── README_AI_PARSER.md         # Comprehensive documentation
├── tests/
│   └── test_vhdl_ai_parser.py      # Unit tests
├── examples/
│   ├── ai_parser_demo.py           # Interactive demo script
│   └── test_vhdl/
│       └── axi_example_peripheral.vhd  # Example VHDL with AXI
└── docs/
    └── PARSER_COMPARISON.md        # Old vs New comparison
```

---

## Quick Test (Without AI)

```bash
cd /home/balevision/workspace/bleviet/ipcore_lib

# Test with the example AXI peripheral
python examples/ai_parser_demo.py examples/test_vhdl/axi_example_peripheral.vhd
```

**Expected Output:**
- Entity name: `axi_example_peripheral`
- ~20 ports parsed (AXI signals + clocks)
- 4 generics/parameters
- No bus interfaces (AI disabled)

---

## Quick Test (With AI - Requires Ollama)

```bash
# Ensure Ollama is running
ollama pull llama3.3:latest

# Run with AI enhancement
python examples/ai_parser_demo.py \
    examples/test_vhdl/axi_example_peripheral.vhd \
    --enable-ai \
    --verbose
```

**Expected Output:**
- All ports parsed (same as above)
- **Bus interfaces detected**: AI identifies AXI4-Lite slave
- **AI-generated description**: Contextual description of the IP core
- Processing time: ~2-5 seconds (LLM call)

---

## Basic Usage (Python)

### Without AI
```python
from ipcore_lib.parser.hdl.vhdl_ai_parser import VHDLAiParser

parser = VHDLAiParser()
ip_core = parser.parse_file("design.vhd")

print(f"Entity: {ip_core.vlnv.name}")
print(f"Ports: {len(ip_core.ports)}")
print(f"Parameters: {len(ip_core.parameters)}")
```

### With AI Enhancement
```python
from ipcore_lib.parser.hdl.vhdl_ai_parser import VHDLAiParser, ParserConfig

config = ParserConfig(enable_llm=True)  # Enable AI
parser = VHDLAiParser(config=config)
ip_core = parser.parse_file("axi_peripheral.vhd")

# AI automatically detects bus interfaces!
for bus_if in ip_core.bus_interfaces:
    print(f"Found {bus_if.type} {bus_if.mode}: {bus_if.name}")
```

---

## Key Features

### ✅ Phase 1: Deterministic Parsing (Always Works)
- Entity name extraction
- Port parsing (name, direction, type, width)
- Generic/parameter extraction
- Comment extraction
- Robust error handling

### 🤖 Phase 2: AI Enhancement (Optional)
- **Bus interface detection**: AXI, Avalon, Wishbone, etc.
- **Documentation generation**: Auto-generated descriptions
- **Signal grouping**: Groups related signals into buses
- **Comment analysis**: Extracts semantic meaning

---

## Architecture Highlights

### Hybrid Intelligence Pattern
```
VHDL Text
    ↓
Phase 1: pyparsing (deterministic, reliable)
    ↓
Phase 2: LLM (optional, intelligent)
    ↓
Pydantic IpCore Model (validated)
```

### Design Principles
1. **Reliability First**: Phase 1 always works
2. **Intelligence Second**: Phase 2 enhances but doesn't break
3. **Graceful Degradation**: Works without AI, better with AI
4. **Local-First**: Ollama runs locally (privacy)
5. **Clean Models**: Pydantic validation throughout

---

## Integration with llm_core

The parser reuses the `llm_core` provider pattern from `llm-playground`:

```python
from llm_core.providers import OllamaProvider, OpenAIProvider

# Same pattern as summarize_webpage!
provider = OllamaProvider(model_name="llama3.3:latest")
client = provider.get_client()
response = provider.summarize(client, content, system_prompt, user_prompt)
```

**Benefits:**
- Proven abstraction (already works in `summarize_webpage`)
- Multiple provider support (Ollama, OpenAI, Gemini)
- Easy to test and extend

---

## What Makes This Different?

### vs Old Parser (`vhdl_parser.py`)
| Feature | Old | New AI |
|---------|-----|--------|
| Data model | Custom classes | Pydantic models |
| Bus detection | ❌ None | ✅ AI-powered |
| Validation | Manual | Automatic |
| JSON export | Manual | Built-in |
| Type hints | Partial | Complete |

### vs Manual Annotation
- **Old way**: Write YAML/XML to define bus interfaces
- **New way**: AI detects from code + comments automatically

---

## Dependencies

### Core (Required)
```bash
pip install pyparsing pydantic rich
```

### AI Enhancement (Optional)
```bash
# Option 1: Local (recommended)
# Install Ollama from https://ollama.ai
ollama pull llama3.3:latest

# Option 2: Cloud
# Add to .env:
echo "OPENAI_API_KEY=your-key" >> .env
```

### llm_core Integration
```bash
# Add llm_core to path (temporary)
export PYTHONPATH="/home/balevision/workspace/bleviet/llm-playground/llm_core:$PYTHONPATH"

# Or install locally (permanent)
cd /home/balevision/workspace/bleviet/llm-playground/llm_core
pip install -e .
```

---

## Testing

```bash
# Run unit tests
cd /home/balevision/workspace/bleviet/ipcore_lib
python -m pytest ipcore_lib/tests/test_vhdl_ai_parser.py -v

# Run with AI integration tests (requires Ollama)
python -m pytest ipcore_lib/tests/test_vhdl_ai_parser.py -v -m integration
```

---

## Next Steps

### Immediate (Ready to Use)
1. ✅ Test with demo script
2. ✅ Parse existing VHDL files
3. ✅ Compare old vs new parser

### Short-term (Enhancement)
1. Adjust LLM prompts for better bus detection
2. Add more test cases
3. Integrate with existing tools

### Long-term (New Features)
1. Architecture body parsing
2. Multiple entities per file
3. Test bench generation
4. Code quality suggestions
5. IP-XACT export

---

## Troubleshooting

### AI Not Working?
```python
from ipcore_lib.parser.hdl.vhdl_ai_parser import VhdlAiAnalyzer

analyzer = VhdlAiAnalyzer(provider_name="ollama")
if analyzer.is_available():
    print("✅ AI available")
else:
    print("❌ Check: 1) llm_core installed, 2) Ollama running")
```

### Import Errors?
```bash
# Ensure ipcore_lib is in path
export PYTHONPATH="/home/balevision/workspace/bleviet/ipcore_lib:$PYTHONPATH"

# Ensure llm_core is in path
export PYTHONPATH="/home/balevision/workspace/bleviet/llm-playground/llm_core:$PYTHONPATH"
```

### Parser Fails?
```bash
# Enable verbose logging
python examples/ai_parser_demo.py yourfile.vhd --verbose
```

---

## Documentation

- **Full Documentation**: `ipcore_lib/parser/hdl/README_AI_PARSER.md`
- **Comparison**: `docs/PARSER_COMPARISON.md`
- **Implementation Plan**: `docs/plan.md` (updated with LLM integration)

---

## Summary

**Created:**
- ✅ AI-enhanced VHDL parser (780+ lines)
- ✅ Pydantic model integration
- ✅ LLM-powered bus detection
- ✅ Comprehensive tests
- ✅ Interactive demo
- ✅ Full documentation

**Key Innovation:**
Hybrid intelligence that combines deterministic parsing reliability with AI-powered semantic understanding, following proven patterns from `llm_core`.

**Philosophy:**
Works without AI (reliable), better with AI (intelligent), local-first (privacy), easy to extend (clean interfaces).
