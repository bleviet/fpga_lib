# Implementation Plan for FPGA IP Core Management Application

Based on the comprehensive architecture in `docs/notes.md`, here's a phased implementation plan that builds incrementally from foundational components to the full plugin-based GUI system.

---

## LLM Integration Strategy Overview

### Why Integrate LLM?

Traditional HDL parsing faces challenges that AI naturally solves:

1. **Ambiguity Resolution**: VHDL code often lacks explicit metadata (which signals form a bus interface?)
2. **Natural Language Understanding**: Comments contain valuable semantic information
3. **Pattern Recognition**: Identifying non-standard conventions across different coding styles
4. **Semantic Search**: Finding IP cores by functionality, not just keywords
5. **Code Quality**: Suggesting improvements based on best practices

### Integration Philosophy: "Hybrid Intelligence"

**NOT**: Replace deterministic parsing with unreliable LLM
**YES**: Enhance reliable parsing with intelligent interpretation

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
│  • Suggest improvements                          │
│  • Graceful fallback if unavailable              │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│         Canonical IpCore Model                   │
└──────────────────────────────────────────────────┘
```

### Where LLM Adds Value

| Use Case | Traditional Approach | LLM Enhancement |
|----------|---------------------|-----------------|
| Bus interface detection | Manual YAML annotation | Auto-detect from signals/comments |
| Documentation | Parse explicit comments only | Generate from context + naming |
| Search | Keyword matching | Semantic similarity ("timer" = "counter") |
| Code review | Static analysis rules | Context-aware suggestions |
| Migration | Manual conversion | Intelligent upgrade recommendations |

### Design Principles

1. **Optional & Configurable**: `--enable-ai` flag, off by default
2. **Local-First**: Default to Ollama (privacy + no API costs)
3. **Graceful Degradation**: Core functionality works without LLM
4. **Reuse Proven Patterns**: Leverage `llm_core` from `summarize_webpage`
5. **Educational**: Demonstrate practical AI in domain-specific tools

### Implementation Pattern

Following the **Provider + Strategy pattern** from `llm_core`:

```python
# Configuration
class ParserConfig(BaseModel):
    enable_llm: bool = False          # Explicit opt-in
    llm_provider: str = "ollama"      # Local by default
    llm_model: str = "llama3.3:latest"

# Usage
parser = VhdlParser(config=ParserConfig(enable_llm=True))
ip_core = parser.parse("timer.vhd")  # AI-enhanced if available
```

---

## Phase 1: Core Foundation (Weeks 1-3)

### 1.1 Canonical Data Model (Week 1)
**Goal:** Establish the single source of truth

**Tasks:**
1. **Define Pydantic models** in `fpga_lib/model/`:
   ```python
   # fpga_lib/model/core.py
   class IpCore(BaseModel):
       vlnv: VLNV
       description: str
       generics: List[Generic] = []
       ports: List[Port] = []
       bus_interfaces: List[BusInterface] = []
       memory_maps: List[MemoryMap] = []
   
   # fpga_lib/model/bus.py
   class BusInterface(BaseModel):
       name: str
       bus_type: BusType  # Enum: AXI4L, AXIS, Avalon, etc.
       mode: InterfaceMode  # Enum: master, slave
       port_maps: Dict[str, str]
       memory_map: Optional[MemoryMapReference]
   
   # fpga_lib/model/memory.py
   class MemoryMap(BaseModel):
       name: str
       address_blocks: List[AddressBlock]
   
   class AddressBlock(BaseModel):
       name: str
       base_address: int
       range: int
       width: int
       registers: List[Register] = []
       register_arrays: List[RegisterArray] = []
   ```

2. **Integrate existing register models** from `fpga_lib/core/register.py`:
   - Ensure `Register` and `BitField` classes work seamlessly with new `MemoryMap` model
   - Add Pydantic `model_validate` support to existing dataclasses

3. **Create validation rules**:
   ```python
   # fpga_lib/model/validators.py
   def validate_address_alignment(register: Register) -> List[ValidationError]:
       """Registers must be aligned to their width."""
       if register.offset % (register.width // 8) != 0:
           return [ValidationError(f"Unaligned address: {register.name}")]
       return []
   
   def validate_no_overlaps(memory_map: MemoryMap) -> List[ValidationError]:
       """Detect overlapping registers."""
       # Already implemented in memory_map_core.py, integrate here
       pass
   ```

4. **Add computed properties** to models:
   ```python
   class Port(BaseModel):
       # ... existing fields ...
       
       @property
       def range_string(self) -> str:
           """Generate VHDL range string (to/downto)."""
           if self.msb is None:
               return ""
           return f"({self.msb} {self.range_direction.value} {self.lsb})"
   ```

**Deliverable:** Validated Pydantic models for the entire IP core structure

---

### 1.2 Parser Layer (Week 2)
**Goal:** Convert external formats → Canonical Model

**Tasks:**
1. **YAML Parser** (already exists, enhance):
   - Move `examples/gpio/memory_map_loader.py` → `fpga_lib/parser/yaml/memory_map_parser.py`
   - Extend to parse full IP core definitions (not just memory maps)
   - Support the enhanced YAML schema from `docs/notes.md`

2. **VHDL Parser with AI Enhancement** (enhance existing):
   - Build on existing `fpga_lib/parser/hdl/vhdl_parser.py`
   - **Phase 1 (pyparsing)**: Robust entity extraction
     - Use `pyparsing` for deterministic parsing of entity, ports, generics
     - Extract basic structure reliably
   - **Phase 2 (LLM-powered)**: Intelligent interpretation
     - Integrate `llm_core` providers for AI-powered analysis
     - Extract bus interface hints from comments/pragmas (e.g., "AXI4-Lite slave")
     - Group related signals into logical bus interfaces (e.g., signals with `axi_` prefix)
     - Handle complex expressions (`DATA_WIDTH - 1`, `2**N - 1`)
     - Infer missing metadata (address widths, protocol types)
     - Gracefully handle non-standard/vendor-specific conventions
   - **Hybrid Strategy Pattern**:
     ```python
     class VhdlParserStrategy:
         def __init__(self, llm_provider: Optional[BaseProvider] = None):
             self.pyparsing_parser = VhdlPyparsingParser()
             self.llm_provider = llm_provider  # Optional AI enhancement
         
         def parse(self, vhdl_text: str) -> IpCore:
             # Step 1: Deterministic parsing
             entity_data = self.pyparsing_parser.parse(vhdl_text)
             
             # Step 2: AI-enhanced interpretation (if LLM available)
             if self.llm_provider:
                 entity_data = self._enhance_with_llm(entity_data, vhdl_text)
             
             return self._to_canonical_model(entity_data)
         
         def _enhance_with_llm(self, entity_data, vhdl_text):
             """Use LLM to extract bus interfaces from comments/conventions."""
             prompt = f"""
             Analyze this VHDL entity and identify bus interfaces:
             
             Entity: {entity_data['name']}
             Ports: {entity_data['ports']}
             Comments: {self._extract_comments(vhdl_text)}
             
             Identify:
             1. Which ports belong to standard bus interfaces (AXI, Avalon, etc.)
             2. Bus interface type and role (master/slave)
             3. Any missing metadata from comments
             
             Return structured JSON.
             """
             # Use llm_core provider pattern
             bus_interfaces = self.llm_provider.analyze(prompt)
             entity_data['bus_interfaces'] = bus_interfaces
             return entity_data
     ```

3. **Create Parser Registry**:
   ```python
   # fpga_lib/parser/registry.py
   class ParserFactory:
       _parsers: Dict[str, Type[IIpParser]] = {}
       
       @classmethod
       def register(cls, format: str, parser_class: Type[IIpParser]):
           cls._parsers[format] = parser_class
       
       @classmethod
       def get_parser(cls, format: str) -> IIpParser:
           if format not in cls._parsers:
               raise ValueError(f"No parser for format: {format}")
           return cls._parsers[format]()
   
   # Usage:
   ParserFactory.register("yaml", YamlParser)
   ParserFactory.register("vhdl", VhdlParser)
   ParserFactory.register("ipxact", IpxactParser)  # Future
   ```

4. **Add error recovery**:
   - Partial parsing when files are incomplete
   - Clear error messages with line numbers
   - Option to parse with warnings vs strict mode

5. **LLM Integration Setup**:
   - Add `llm_core` as dependency to `fpga_lib`
   - Create configuration for LLM provider selection:
     ```python
     # fpga_lib/config.py
     class ParserConfig(BaseModel):
         enable_llm_enhancement: bool = False  # Opt-in
         llm_provider: Optional[str] = "ollama"  # Default to local
         llm_model: Optional[str] = "llama3.3:latest"
     ```
   - Fallback gracefully: If LLM unavailable, use pyparsing-only mode
   - Add CLI flag: `fpga-lib parse --enable-ai input.vhd`

**Deliverable:** Pluggable parser system (YAML/VHDL → `IpCore` model) with optional AI enhancement

---

### 1.3 Generator Layer (Week 3)
**Goal:** Convert Canonical Model → Output Formats

**Tasks:**
1. **VHDL Generator** (enhance existing):
   - Move existing generator to `fpga_lib/generator/hdl/vhdl_generator.py`
   - Use Jinja2 templates (already done)
   - Template simplification: remove logic, use `@property` from models

2. **YAML Generator**:
   ```python
   # fpga_lib/generator/yaml/yaml_generator.py
   class YamlGenerator(IIpGenerator):
       def generate(self, ip_core: IpCore, output_path: Path) -> None:
           data = ip_core.model_dump(exclude_none=True)
           yaml_str = yaml.dump(data, sort_keys=False, indent=2)
           output_path.write_text(yaml_str)
   ```

3. **Documentation Generator** (new):
   ```python
   # fpga_lib/generator/docs/markdown_generator.py
   class MarkdownGenerator(IIpGenerator):
       def generate(self, ip_core: IpCore, output_path: Path) -> None:
           template = self.env.get_template("memory_map.md.j2")
           content = template.render(ip_core=ip_core)
           output_path.write_text(content)
   ```

4. **C Header Generator** (new):
   ```python
   # fpga_lib/generator/sw/c_header_generator.py
   class CHeaderGenerator(IIpGenerator):
       def generate(self, ip_core: IpCore, output_path: Path) -> None:
           # Generate #define CTRL_REG_OFFSET 0x00
           # Generate bitfield masks
           pass
   ```

5. **Generator Registry** (mirrors parser registry):
   ```python
   # fpga_lib/generator/registry.py
   class GeneratorFactory:
       # Same pattern as ParserFactory
       pass
   ```

**Deliverable:** Pluggable generator system (`IpCore` → VHDL/YAML/Markdown/C)

---

## Phase 2: CLI Tool & Core Library (Weeks 4-5)

### 2.1 Facade Layer (Week 4)
**Goal:** Simple API that hides complexity

**Tasks:**
1. **IpCoreManager facade**:
   ```python
   # fpga_lib/manager.py
   class IpCoreManager:
       def __init__(self):
           self.parser_factory = ParserFactory()
           self.generator_factory = GeneratorFactory()
       
       def convert(self, input_path: Path, output_format: str) -> Path:
           """One-line conversion."""
           # Detect input format
           input_format = self._detect_format(input_path)
           
           # Parse → Canonical Model
           parser = self.parser_factory.get_parser(input_format)
           ip_core = parser.parse(input_path)
           
           # Validate
           errors = ip_core.validate()
           if errors:
               raise ValidationError(errors)
           
           # Generate
           output_path = input_path.with_suffix(f".{output_format}")
           generator = self.generator_factory.get_generator(output_format)
           generator.generate(ip_core, output_path)
           
           return output_path
       
       def validate(self, input_path: Path) -> List[ValidationError]:
           """Standalone validation."""
           parser = self.parser_factory.get_parser(self._detect_format(input_path))
           ip_core = parser.parse(input_path)
           return ip_core.validate()
   ```

2. **CLI tool**:
   ```python
   # fpga_lib/cli.py
   import click
   
   @click.group()
   def cli():
       """FPGA IP Core Manager CLI."""
       pass
   
   @cli.command()
   @click.argument('input_file', type=click.Path(exists=True))
   @click.option('--format', '-f', required=True, type=click.Choice(['vhdl', 'yaml', 'markdown', 'c']))
   def convert(input_file, format):
       """Convert IP core to different format."""
       manager = IpCoreManager()
       output = manager.convert(Path(input_file), format)
       click.echo(f"Generated: {output}")
   
   @cli.command()
   @click.argument('input_file', type=click.Path(exists=True))
   def validate(input_file):
       """Validate IP core definition."""
       manager = IpCoreManager()
       errors = manager.validate(Path(input_file))
       if errors:
           for error in errors:
               click.echo(f"❌ {error}", err=True)
           sys.exit(1)
       else:
           click.echo("✅ Valid")
   ```

3. **Package setup**:
   ```python
   # setup.py
   setup(
       name='fpga_lib',
       entry_points={
           'console_scripts': [
               'fpga-tool=fpga_lib.cli:cli',
           ],
       },
   )
   ```

**Deliverable:** Working CLI tool for conversions and validation

---

### 2.2 Testing & Documentation (Week 5)

**Tasks:**
1. **Comprehensive test suite**:
   ```
   tests/
       model/
           test_ip_core_validation.py
           test_register_model.py
       parser/
           test_yaml_parser.py
           test_vhdl_parser.py
       generator/
           test_vhdl_generator.py
           test_yaml_generator.py
       integration/
           test_roundtrip.py  # YAML → Model → YAML
           test_vhdl_to_yaml.py
   ```

2. **Add example IP cores**:
   ```
   examples/
       cores/
           simple_timer/
               timer.yml
               timer.vhd
               timer_regs.yml
           uart/
               uart.yml
               uart.vhd
           axi_dma/
               dma.yml
               dma.vhd
   ```

3. **API Documentation**:
   - Add docstrings to all public APIs
   - Generate Sphinx documentation
   - Create user guide with examples

**Deliverable:** Stable, tested, documented core library

---

## Phase 2.3: LLM Integration Use Cases (Week 5.5)
**Goal:** Define where AI adds value beyond basic parsing

### LLM Enhancement Scenarios

**1. Bus Interface Auto-Detection**
```python
# Input: VHDL with unclear bus grouping
# LLM analyzes:
# - Signal naming conventions (axi_*, m_axis_*)
# - Comments ("AXI4-Lite slave interface")
# - Port groupings in entity
# 
# Output: Structured bus interface metadata
{
    "name": "s_axi",
    "type": "AXI4_LITE",
    "role": "slave",
    "signals": {
        "awaddr": "s_axi_awaddr",
        "awvalid": "s_axi_awvalid",
        ...
    }
}
```

**2. Documentation Generation**
```python
# Input: Sparse comments in VHDL
# LLM generates:
# - Register descriptions based on names
# - Bitfield purposes from context
# - Usage examples
# 
# Example:
# CTRL_REG (0x00) → "Control register for enabling/disabling core"
# STATUS_REG (0x04) → "Status register with interrupt flags"
```

**3. Code Quality Analysis**
```python
# LLM reviews VHDL and suggests:
# - Missing reset conditions
# - Potential timing issues
# - Non-standard conventions
# - Improvement opportunities
```

**4. Semantic Search Enhancement**
```python
# Query: "timer with interrupt support"
# Traditional search: keyword matching
# LLM search: 
#   - Understands "timer" could be "counter" or "watchdog"
#   - Recognizes "interrupt" might be "irq" or "event"
#   - Ranks by functional similarity, not just text match
```

**5. Migration Assistant**
```python
# Input: Old VHDL coding style
# LLM suggests:
# - Modern VHDL-2008 equivalents
# - Standard bus interface conversions
# - Synthesis-friendly alternatives
```

### Implementation Pattern (mirrors summarizer.py)

```python
# fpga_lib/ai/vhdl_analyzer.py
from llm_core.providers import BaseProvider
from rich.console import Console

class VhdlAiAnalyzer:
    """AI-powered VHDL analysis using llm_core providers."""
    
    def __init__(self, provider: BaseProvider):
        self.provider = provider
        self.console = Console()
    
    def detect_bus_interfaces(self, entity_data: Dict, vhdl_text: str) -> List[BusInterface]:
        """Use LLM to identify bus interfaces from VHDL code."""
        
        if not self.provider.api_key and self.provider.name != "Ollama":
            self.console.print(f"[yellow]LLM provider not configured, skipping AI enhancement[/yellow]")
            return []
        
        system_prompt = """
        You are an expert FPGA engineer analyzing VHDL code.
        Identify standard bus interfaces (AXI, Avalon, Wishbone, etc.) from:
        1. Signal naming conventions
        2. Comments and pragmas
        3. Port groupings
        
        Return structured JSON with bus interface metadata.
        """
        
        user_prompt = f"""
        Entity: {entity_data['name']}
        Ports: {json.dumps(entity_data['ports'], indent=2)}
        
        VHDL Code:
        {vhdl_text[:2000]}  # First 2000 chars for context
        
        Identify all bus interfaces and return as JSON array:
        [
          {{
            "name": "s_axi",
            "type": "AXI4_LITE",
            "role": "slave",
            "signals": {{"awaddr": "s_axi_awaddr", ...}}
          }}
        ]
        """
        
        with self.console.status("[green]Analyzing with AI..."):
            client = self.provider.get_client()
            result = self.provider.analyze(client, user_prompt, system_prompt)
        
        return self._parse_llm_response(result)
```

### Configuration & Fallback

```python
# Example usage in VHDL parser
class VhdlParser:
    def __init__(self, config: ParserConfig):
        self.pyparsing_parser = VhdlPyparsingParser()
        
        # Optional LLM enhancement
        if config.enable_llm_enhancement:
            from llm_core.providers import OllamaProvider, OpenAIProvider
            
            if config.llm_provider == "ollama":
                llm = OllamaProvider(model_name=config.llm_model)
            elif config.llm_provider == "openai":
                llm = OpenAIProvider(model_name=config.llm_model)
            else:
                llm = None
            
            self.ai_analyzer = VhdlAiAnalyzer(llm) if llm else None
        else:
            self.ai_analyzer = None
    
    def parse(self, vhdl_text: str) -> IpCore:
        # Step 1: Deterministic parsing (always runs)
        entity_data = self.pyparsing_parser.parse(vhdl_text)
        
        # Step 2: AI enhancement (optional, graceful fallback)
        if self.ai_analyzer:
            try:
                bus_interfaces = self.ai_analyzer.detect_bus_interfaces(
                    entity_data, vhdl_text
                )
                entity_data['bus_interfaces'] = bus_interfaces
            except Exception as e:
                # Graceful degradation: log warning, continue without AI
                logger.warning(f"LLM enhancement failed: {e}, continuing with basic parsing")
        
        return self._to_canonical_model(entity_data)
```

### Benefits of This Approach

1. **Optional & Local-First**: Defaults to Ollama (no API costs, no privacy concerns)
2. **Graceful Degradation**: Works without LLM, enhanced with LLM
3. **Reuses llm_core**: Proven provider abstraction from `summarize_webpage`
4. **User Control**: CLI flag `--enable-ai` for explicit opt-in
5. **Educational**: Shows practical AI integration in domain-specific tools

**Deliverable:** AI-enhanced parser with multiple use cases, following llm_core patterns

---

## Phase 3: IP Core Library Manager (Weeks 6-8)

### 3.1 Indexing System (Week 6)
**Goal:** Fast discovery and search with parallel processing

**Tasks:**
1. **SQLite index schema**:
   ```sql
   -- fpga_lib/library/schema.sql
   CREATE TABLE ip_cores ( ... );  -- As defined in notes.md
   CREATE VIRTUAL TABLE ip_cores_fts USING fts5( ... );
   CREATE TABLE dependencies ( ... );
   CREATE TABLE bus_interfaces ( ... );
   CREATE TABLE embeddings (  -- For AI-powered semantic search
       core_id INTEGER PRIMARY KEY,
       embedding BLOB,  -- Vector embedding of description + metadata
       model_version TEXT,
       FOREIGN KEY (core_id) REFERENCES ip_cores(id)
   );
   ```

2. **Parallel indexer implementation**:
   ```python
   # fpga_lib/library/indexer.py
   from concurrent.futures import ProcessPoolExecutor, as_completed
   import multiprocessing
   
   class IpCoreIndexer:
       def __init__(self, project_root: Path, index_db: Path, max_workers: int = None):
           # As detailed in notes.md
           self.max_workers = max_workers or multiprocessing.cpu_count()
           self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
           pass
       
       def scan_project(self) -> None:
           """Parallel initial scan using multiprocessing."""
           files = list(self._discover_files())
           
           # Parse files in parallel across CPU cores
           futures = []
           for file_path in files:
               future = self.executor.submit(self._parse_file_worker, file_path)
               futures.append(future)
           
           # Collect results and index sequentially (SQLite writes)
           for future in as_completed(futures):
               try:
                   parsed_data = future.result()
                   self._index_parsed_data(parsed_data)
               except Exception as e:
                   logger.error(f"Failed to index: {e}")
       
       @staticmethod
       def _parse_file_worker(path: Path) -> dict:
           """Worker process: parse file (CPU-intensive)."""
           parser = ParserFactory.get_parser(detect_format(path))
           return parser.parse(path).model_dump()
       
       def _index_file(self, path: Path) -> None:
           """Parse and index single file."""
           pass
   ```

3. **File system watcher**:
   ```python
   # fpga_lib/library/watcher.py
   from watchdog.observers import Observer
   
   class FileSystemWatcher:
       def __init__(self, root: Path, indexer: IpCoreIndexer):
           self.observer = Observer()
           # Setup as in notes.md
   ```

4. **AI-powered query engine with LLM fallback**:
   ```python
   # fpga_lib/library/query.py
   import numpy as np
   from sentence_transformers import SentenceTransformer
   from typing import Optional
   from llm_core.providers import BaseProvider
   
   class IpCoreQuery:
       def __init__(self, db_path: Path, llm_provider: Optional[BaseProvider] = None):
           # Lightweight embedding model (runs on CPU, no GPU needed)
           self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
           self.db = sqlite3.connect(db_path)
           self.llm_provider = llm_provider  # Optional LLM for query expansion
       
       def find_by_name(self, pattern: str) -> List[IpCoreMetadata]:
           pass
       
       def find_axi_slaves(self) -> List[IpCoreMetadata]:
           pass
       
       def full_text_search(self, query: str) -> List[IpCoreMetadata]:
           """Traditional keyword-based search."""
           pass
       
       def semantic_search(self, query: str, top_k: int = 10) -> List[IpCoreMetadata]:
           """AI-powered semantic search using embeddings.
           
           Example queries:
           - "timer with interrupt support"
           - "DMA controller for video streaming"
           - "cores similar to AXI GPIO"
           """
           # Optional: Use LLM to expand/clarify query
           expanded_query = self._expand_query_with_llm(query) if self.llm_provider else query
           
           # Generate query embedding
           query_embedding = self.embedding_model.encode(expanded_query)
           
           # Compute cosine similarity with all indexed cores
           cursor = self.db.execute("SELECT core_id, embedding FROM embeddings")
           scores = []
           for core_id, embedding_blob in cursor:
               core_embedding = np.frombuffer(embedding_blob, dtype=np.float32)
               similarity = np.dot(query_embedding, core_embedding)
               scores.append((core_id, similarity))
           
           # Return top-k most similar cores
           top_cores = sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
           return [self._load_metadata(core_id) for core_id, _ in top_cores]
       
       def _expand_query_with_llm(self, query: str) -> str:
           """Use LLM to expand natural language query into technical terms.
           
           Example:
           Input: "I need something to count time"
           Output: "timer counter watchdog periodic interrupt"
           """
           prompt = f"""
           Convert this natural language query into technical FPGA/HDL terms.
           Add synonyms and related terms. Keep it concise.
           
           Query: "{query}"
           
           Return only the expanded technical query (no explanation).
           """
           
           try:
               client = self.llm_provider.get_client()
               expanded = self.llm_provider.summarize(
                   client, prompt, 
                   system_prompt="You are an FPGA engineering assistant.",
                   user_prompt_prefix=""
               )
               return expanded.strip()
           except Exception as e:
               logger.warning(f"Query expansion failed: {e}, using original query")
               return query
       
       def generate_embeddings_batch(self, cores: List[IpCore]) -> None:
           """Generate embeddings for multiple cores in parallel."""
           texts = [f"{c.description} {c.vlnv.name}" for c in cores]
           embeddings = self.embedding_model.encode(texts, batch_size=32, show_progress_bar=True)
           
           for core, embedding in zip(cores, embeddings):
               self._store_embedding(core.vlnv, embedding)
   ```

**Deliverable:** Fast parallel indexing with AI-powered semantic search backend + optional LLM query expansion

---

### 3.2 Library Manager API (Week 7)

**Tasks:**
1. **Library manager facade**:
   ```python
   # fpga_lib/library/manager.py
   class LibraryManager:
       def __init__(self, project_root: Path):
           self.indexer = IpCoreIndexer(project_root, project_root / ".fpga_lib" / "index.db")
           self.watcher = FileSystemWatcher(project_root, self.indexer)
           self.query = IpCoreQuery(self.indexer.db)
       
       def search(self, query: str) -> List[IpCoreMetadata]:
           """User-facing search."""
           return self.query.full_text_search(query)
       
       def get_dependencies(self, core: IpCore) -> List[Path]:
           """Get all cores this one depends on."""
           return self.indexer.get_dependencies(core.path)
   ```

2. **CLI integration**:
   ```bash
   # New CLI commands
   fpga-tool library init                  # Initialize index
   fpga-tool library search "timer"        # Search cores
   fpga-tool library list --bus AXI4L      # Filter by bus type
   fpga-tool library deps timer.yml        # Show dependencies
   ```

**Deliverable:** Library management accessible via CLI

---

### 3.3 Dependency Graph (Week 8)

**Tasks:**
1. **Build dependency graph**:
   ```python
   # fpga_lib/library/dependency_graph.py
   import networkx as nx
   
   class DependencyGraph:
       def __init__(self, library: LibraryManager):
           self.library = library
           self.graph = nx.DiGraph()
       
       def build(self) -> None:
           """Build graph from all indexed cores."""
           cores = self.library.indexer.get_all_cores()
           for core in cores:
               self.graph.add_node(core.path)
               deps = self.library.get_dependencies(core)
               for dep in deps:
                   self.graph.add_edge(core.path, dep)
       
       def find_cycles(self) -> List[List[Path]]:
           """Detect circular dependencies."""
           return list(nx.simple_cycles(self.graph))
       
       def topological_order(self) -> List[Path]:
           """Get build order."""
           return list(nx.topological_sort(self.graph))
   ```

2. **Export graph to DOT format** (for visualization):
   ```python
   def export_dot(self, output_path: Path) -> None:
       nx.drawing.nx_pydot.write_dot(self.graph, output_path)
   ```

**Deliverable:** Dependency analysis and build ordering

---

## Phase 4: GUI Foundation (Weeks 9-12)

### 4.1 Plugin Host Core (Weeks 9-10)
**Goal:** Minimal GUI framework that plugins extend

**Tasks:**
1. **Plugin contract**:
   ```python
   # fpga_lib/gui/plugin_api.py
   from abc import ABC, abstractmethod
   
   class IPlugin(ABC):
       @property
       @abstractmethod
       def name(self) -> str: pass
       
       @property
       @abstractmethod
       def version(self) -> str: pass
       
       @abstractmethod
       def initialize(self, context: PluginContext) -> None: pass
       
       @abstractmethod
       def activate(self) -> None: pass
       
       @abstractmethod
       def deactivate(self) -> None: pass
       
       @abstractmethod
       def cleanup(self) -> None: pass
   ```

2. **Event bus**:
   ```python
   # fpga_lib/gui/event_bus.py
   class Event(BaseModel):
       event_type: str
       timestamp: datetime = Field(default_factory=datetime.now)
       source_plugin: str
   
   class EventBus:
       def __init__(self):
           self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
       
       def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
           self._subscribers[event_type].append(handler)
       
       def publish(self, event: Event) -> None:
           for handler in self._subscribers[event.event_type]:
               handler(event)
   ```

3. **Service registry**:
   ```python
   # fpga_lib/gui/service_registry.py
   class IService(ABC): pass
   
   class ServiceRegistry:
       def __init__(self):
           self._services: Dict[Type[IService], List[IService]] = defaultdict(list)
       
       def register_service(self, interface: Type[IService], impl: IService) -> None:
           self._services[interface].append(impl)
       
       def get_service(self, interface: Type[IService]) -> Optional[IService]:
           services = self._services.get(interface, [])
           return services[0] if services else None
       
       def get_all_services(self, interface: Type[IService]) -> List[IService]:
           return self._services.get(interface, [])
   ```

4. **Plugin manager**:
   ```python
   # fpga_lib/gui/plugin_manager.py
   class PluginManager:
       def __init__(self, event_bus: EventBus, service_registry: ServiceRegistry):
           self.event_bus = event_bus
           self.service_registry = service_registry
           self.plugins: Dict[str, IPlugin] = {}
       
       def discover_plugins(self) -> None:
           """Find plugins via entry points."""
           for entry_point in importlib.metadata.entry_points(group='fpga_lib.plugins'):
               plugin_class = entry_point.load()
               plugin = plugin_class()
               self.plugins[plugin.name] = plugin
       
       def initialize_all(self) -> None:
           """Initialize all discovered plugins."""
           context = PluginContext(self.event_bus, self.service_registry)
           for plugin in self.plugins.values():
               plugin.initialize(context)
   ```

5. **Main application window**:
   ```python
   # fpga_lib/gui/main_window.py
   class MainWindow(QMainWindow):
       def __init__(self):
           super().__init__()
           self.event_bus = EventBus()
           self.service_registry = ServiceRegistry()
           self.plugin_manager = PluginManager(self.event_bus, self.service_registry)
           
           self._setup_ui()
           self.plugin_manager.discover_plugins()
           self.plugin_manager.initialize_all()
       
       def _setup_ui(self):
           # Menu bar
           # Dockable window system (QDockWidget)
           # Status bar
           pass
   ```

**Deliverable:** Empty GUI shell that can load plugins

---

### 4.2 Convert Memory Map Editor to Plugin (Weeks 11-12)

**Tasks:**
1. **Extract as standalone plugin**:
   ```
   plugins/
       memory_map_editor/
           __init__.py              # MemoryMapEditorPlugin class
           ui/
               outline.py           # Tree view (from memory_map_outline.py)
               detail_form.py       # Property editor
               bit_visualizer.py    # Bit field viz
           services/
               register_service.py  # IRegisterEditorService
   ```

2. **Plugin implementation**:
   ```python
   # plugins/memory_map_editor/__init__.py
   class MemoryMapEditorPlugin(IPlugin):
       name = "Memory Map Editor"
       version = "1.0.0"
       
       def initialize(self, context: PluginContext):
           self.context = context
           self.service = RegisterEditorService()
           context.service_registry.register_service(IRegisterEditorService, self.service)
           
           # Subscribe to events
           context.event_bus.subscribe("file_loaded", self.on_file_loaded)
       
       def activate(self):
           # Add dock widgets to main window
           self.outline_dock = self.context.create_dock_widget("Memory Map Outline", self.outline)
           self.detail_dock = self.context.create_dock_widget("Register Details", self.detail_form)
       
       def on_file_loaded(self, event: FileLoadedEvent):
           """When IP core is loaded, populate outline."""
           self.outline.set_ip_core(event.ip_core)
   ```

3. **Entry point registration**:
   ```python
   # plugins/memory_map_editor/setup.py
   setup(
       name='fpga_lib_memory_map_editor',
       entry_points={
           'fpga_lib.plugins': [
               'memory_map_editor = plugins.memory_map_editor:MemoryMapEditorPlugin'
           ]
       }
   )
   ```

4. **Migrate existing code**:
   - Move `examples/gui/memory_map_editor/gui` → `plugins/memory_map_editor/ui/`
   - Adapt to use event bus instead of direct signal connections
   - Register services instead of direct method calls

**Deliverable:** Memory map editor running as first plugin

---

## Phase 5: Additional Plugins (Weeks 13-17)

### 5.1 IP Core Explorer Plugin (Week 13)

**Tasks:**
1. **Tree view with library**:
   ```python
   # plugins/ip_core_explorer/__init__.py
   class IpCoreExplorerPlugin(IPlugin):
       def activate(self):
           self.tree = IpCoreExplorerTree(self.library_manager)
           self.dock = self.context.create_dock_widget("IP Core Library", self.tree)
       
       def on_tree_item_selected(self, core_path: Path):
           """Publish event when user selects an IP core."""
           ip_core = self.parser.parse(core_path)
           self.context.event_bus.publish(IpCoreSelectedEvent(
               source_plugin="ip_core_explorer",
               ip_core=ip_core
           ))
   ```

2. **AI-enhanced search bar**:
   ```python
   class SearchWidget(QWidget):
       def __init__(self, library: LibraryManager):
           super().__init__()
           self.library = library
           self.search_input = QLineEdit()
           self.search_mode = QComboBox()
           self.search_mode.addItems(["Keyword", "Semantic (AI)", "Hybrid"])
           self.search_input.textChanged.connect(self.on_search)
       
       def on_search(self, text: str):
           mode = self.search_mode.currentText()
           
           if mode == "Keyword":
               results = self.library.search(text)
           elif mode == "Semantic (AI)":
               # Natural language search
               results = self.library.semantic_search(text)
           else:  # Hybrid
               # Combine keyword + semantic results
               keyword_results = self.library.search(text)
               semantic_results = self.library.semantic_search(text)
               results = self._merge_results(keyword_results, semantic_results)
           
           self.results_tree.populate(results)
   ```

**Deliverable:** IP core library navigation with AI-powered search

---

### 5.2 Bus Interface Configuration Plugin (Week 14)

**Tasks:**
1. **Visual bus editor**:
   ```python
   # plugins/bus_config/__init__.py
   class BusConfigPlugin(IPlugin):
       def on_bus_interface_selected(self, event: BusInterfaceSelectedEvent):
           """Show bus-specific configuration UI."""
           if event.bus.bus_type == BusType.AXI4L:
               self.show_axi4l_config(event.bus)
   ```

2. **AXI4-Lite validator**:
   ```python
   class Axi4LValidationService(IValidationService):
       def validate(self, ip_core: IpCore) -> List[ValidationError]:
           errors = []
           for bus in ip_core.bus_interfaces:
               if bus.bus_type == BusType.AXI4L:
                   # Check WDATA width = WSTRB width × 8
                   # Check required signals are mapped
                   pass
           return errors
   ```

**Deliverable:** Bus interface configuration and validation

---

### 5.3 Code Generation Preview Plugin (Week 15)

**Tasks:**
1. **Live preview**:
   ```python
   # plugins/code_preview/__init__.py
   class CodePreviewPlugin(IPlugin):
       def on_register_modified(self, event: RegisterModifiedEvent):
           """Regenerate preview when registers change."""
           vhdl_code = self.generator.generate_preview(self.current_ip_core)
           self.preview_widget.set_text(vhdl_code)
   ```

2. **Syntax highlighting**:
   ```python
   from pygments import highlight
   from pygments.lexers import VhdlLexer
   from pygments.formatters import HtmlFormatter
   
   class CodePreviewWidget(QTextEdit):
       def set_text(self, code: str):
           highlighted = highlight(code, VhdlLexer(), HtmlFormatter())
           self.setHtml(highlighted)
   ```

**Deliverable:** Real-time HDL code preview

---

### 5.4 AI Assistant Plugin (Week 16)

**Tasks:**
1. **Integration with LLM API**:
   ```python
   # plugins/ai_assistant/__init__.py
   from openai import OpenAI  # or local LLM via llama.cpp
   
   class AiAssistantPlugin(IPlugin):
       def __init__(self):
           # Use local model for privacy, or API for advanced features
           self.use_local = os.getenv("FPGA_USE_LOCAL_LLM", "true") == "true"
           
           if self.use_local:
               from llama_cpp import Llama
               self.model = Llama(model_path="models/codellama-7b.gguf", n_ctx=4096)
           else:
               self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
       
       def generate_register_documentation(self, register: Register) -> str:
           """Auto-generate register descriptions from names and bit fields."""
           prompt = f"""Generate a clear technical description for this hardware register:
           
           Name: {register.name}
           Bit fields: {[f.name for f in register.fields]}
           Access: {register.access}
           
           Description:"""
           
           return self._generate(prompt)
       
       def suggest_register_names(self, description: str) -> List[str]:
           """Suggest register names from natural language description."""
           prompt = f"""Given this IP core functionality: "{description}"
           
           Suggest 5 appropriate register names following hardware naming conventions:"""
           
           return self._generate(prompt).split('\n')
       
       def explain_bus_protocol(self, bus_type: str) -> str:
           """Generate explanation of bus protocol requirements."""
           prompt = f"""Explain the {bus_type} bus protocol requirements 
           for FPGA IP core implementation. Include timing, signals, and handshake."""
           
           return self._generate(prompt)
       
       def validate_with_ai(self, ip_core: IpCore) -> List[str]:
           """AI-powered validation suggestions."""
           prompt = f"""Review this IP core design for potential issues:
           
           {ip_core.model_dump_json(indent=2)}
           
           Identify: naming inconsistencies, missing signals, address alignment issues."""
           
           return self._generate(prompt).split('\n')
   ```

2. **Chat interface in GUI**:
   ```python
   class AiChatWidget(QWidget):
       def __init__(self, ai_assistant: AiAssistantPlugin):
           super().__init__()
           self.assistant = ai_assistant
           self.chat_history = QTextEdit()
           self.input_field = QLineEdit()
           
           # Context-aware suggestions
           self.input_field.returnPressed.connect(self.on_send)
       
       def on_send(self):
           user_message = self.input_field.text()
           context = self._get_current_context()  # Current IP core, selected register
           
           response = self.assistant.chat(user_message, context)
           self.chat_history.append(f"You: {user_message}\nAI: {response}\n")
   ```

**Deliverable:** AI-powered code generation and design assistance

---

### 5.5 Documentation Generator Plugin (Week 17)

**Tasks:**
1. **Export to Markdown/PDF**:
   ```python
   # plugins/doc_generator/__init__.py
   class DocGeneratorPlugin(IPlugin):
       def export_pdf(self, ip_core: IpCore, output: Path):
           # Generate Markdown
           md_gen = MarkdownGenerator()
           md_content = md_gen.generate_string(ip_core)
           
           # Convert to PDF
           import markdown2pdf
           markdown2pdf.convert(md_content, output)
   ```

2. **Register map diagrams**:
   ```python
   def generate_memory_map_diagram(self, memory_map: MemoryMap) -> Image:
       # Use matplotlib or Pillow to draw register map
       pass
   ```

**Deliverable:** Documentation export plugin

---

## Phase 6: Advanced Features & GPU Acceleration (Weeks 18-21)

### 6.1 GPU-Accelerated Operations (Week 18)

**Goal:** Leverage GPU for compute-intensive tasks

**Tasks:**
1. **Similarity search on GPU**:
   ```python
   # fpga_lib/library/gpu_search.py
   import torch
   import cupy as cp  # CUDA-accelerated NumPy
   
   class GpuAcceleratedSearch:
       def __init__(self, use_gpu: bool = None):
           if use_gpu is None:
               use_gpu = torch.cuda.is_available()
           
           self.device = torch.device("cuda" if use_gpu else "cpu")
           self.embeddings_tensor = None
       
       def load_embeddings_to_gpu(self, embeddings: np.ndarray):
           """Load all core embeddings to GPU memory."""
           self.embeddings_tensor = torch.from_numpy(embeddings).to(self.device)
       
       def batch_similarity_search(self, queries: List[str], top_k: int = 10) -> List[List[int]]:
           """Compute similarity for multiple queries simultaneously on GPU."""
           query_embeddings = self.embedding_model.encode(queries)
           query_tensor = torch.from_numpy(query_embeddings).to(self.device)
           
           # Matrix multiplication on GPU: [num_queries, embedding_dim] × [num_cores, embedding_dim]^T
           # Result: [num_queries, num_cores] similarity matrix
           similarities = torch.mm(query_tensor, self.embeddings_tensor.t())
           
           # Get top-k for each query (parallel across GPU cores)
           top_indices = torch.topk(similarities, k=top_k, dim=1).indices
           
           return top_indices.cpu().numpy().tolist()
   ```

2. **Parallel validation on GPU**:
   ```python
   # fpga_lib/validator/gpu_validator.py
   class GpuValidator:
       def validate_address_alignment_batch(self, registers: List[Register]) -> List[bool]:
           """Check alignment for thousands of registers in parallel."""
           offsets = cp.array([r.offset for r in registers])
           widths = cp.array([r.width for r in registers])
           
           # Vectorized operation on GPU
           alignments = widths // 8
           is_aligned = (offsets % alignments) == 0
           
           return is_aligned.get()  # Transfer back to CPU
   ```

3. **Configuration**:
   ```python
   # fpga_lib/config.py
   @dataclass
   class PerformanceConfig:
       use_gpu: bool = True  # Auto-detect CUDA
       use_multiprocessing: bool = True
       max_workers: int = multiprocessing.cpu_count()
       gpu_batch_size: int = 1024
       
       @classmethod
       def auto_detect(cls):
           """Detect optimal configuration."""
           return cls(
               use_gpu=torch.cuda.is_available(),
               max_workers=min(multiprocessing.cpu_count(), 16)  # Cap to avoid overhead
           )
   ```

**Deliverable:** GPU-accelerated search and validation

---

### 6.2 Distributed Processing (Week 19)

**Goal:** Handle massive projects (1000+ IP cores) efficiently

**Tasks:**
1. **Distributed indexing with Ray**:
   ```python
   # fpga_lib/library/distributed_indexer.py
   import ray
   
   @ray.remote
   class DistributedIndexWorker:
       def __init__(self):
           self.parser_factory = ParserFactory()
       
       def parse_files(self, file_paths: List[Path]) -> List[dict]:
           """Parse batch of files on remote worker."""
           results = []
           for path in file_paths:
               try:
                   parser = self.parser_factory.get_parser(detect_format(path))
                   ip_core = parser.parse(path)
                   results.append(ip_core.model_dump())
               except Exception as e:
                   logger.error(f"Failed to parse {path}: {e}")
           return results
   
   class DistributedIndexer:
       def __init__(self, num_workers: int = None):
           ray.init(num_cpus=num_workers)
           self.workers = [DistributedIndexWorker.remote() for _ in range(num_workers or 4)]
       
       def scan_project(self, file_paths: List[Path]) -> None:
           """Distribute parsing across cluster/multiple machines."""
           # Split files into batches
           batch_size = len(file_paths) // len(self.workers)
           batches = [file_paths[i:i+batch_size] for i in range(0, len(file_paths), batch_size)]
           
           # Submit batches to workers (can run on different machines)
           futures = [worker.parse_files.remote(batch) for worker, batch in zip(self.workers, batches)]
           
           # Collect results
           results = ray.get(futures)
           
           # Index results (single-threaded SQLite writes)
           for batch_results in results:
               for parsed_data in batch_results:
                   self._index_parsed_data(parsed_data)
   ```

2. **Cloud deployment support**:
   ```python
   # Support for AWS Lambda, Google Cloud Functions for massive projects
   # fpga_lib/cloud/lambda_indexer.py
   def lambda_parse_handler(event, context):
       """AWS Lambda function to parse single file."""
       s3_path = event['s3_path']
       file_content = download_from_s3(s3_path)
       
       parser = ParserFactory.get_parser(detect_format(s3_path))
       ip_core = parser.parse_string(file_content)
       
       return ip_core.model_dump()
   ```

**Deliverable:** Distributed processing for enterprise-scale projects

---

### 6.3 User Experience & AI Integration (Week 20)

**Tasks:**
1. **AI-powered command palette** (VS Code style with suggestions):
   ```python
   # fpga_lib/gui/command_palette.py
   class CommandPalette(QDialog):
       def __init__(self, plugin_manager: PluginManager, ai_assistant: AiAssistantPlugin):
           super().__init__()
           self.commands = self._collect_commands(plugin_manager)
           self.ai = ai_assistant
           self.search_box = QLineEdit()
           self.search_box.textChanged.connect(self.on_search_changed)
       
       def on_search_changed(self, text: str):
           """Smart command suggestions using AI."""
           # Traditional fuzzy match
           fuzzy_matches = self._fuzzy_search(text)
           
           # AI-powered intent recognition
           if len(text) > 10:  # Natural language query
               # "show all timer cores" → SearchCommand with filter
               # "generate vhdl for selected register" → GenerateCommand
               suggested_commands = self.ai.interpret_command(text, self.commands)
               matches = suggested_commands + fuzzy_matches
           else:
               matches = fuzzy_matches
           
           self.results_list.populate(matches)
       
       def _collect_commands(self, pm: PluginManager) -> List[Command]:
           commands = []
           for plugin in pm.plugins.values():
               if hasattr(plugin, 'get_commands'):
                   commands.extend(plugin.get_commands())
           return commands
   ```

2. **Keyboard shortcuts**:
   - `Ctrl+P`: Command palette
   - `Ctrl+T`: Quick search IP cores
   - `Ctrl+Shift+F`: Full-text search
   - `Ctrl+,`: Settings

3. **Theme support**:
   ```python
   # fpga_lib/gui/themes.py
   class ThemeManager:
       def apply_theme(self, theme_name: str):
           if theme_name == "dark":
               self.app.setStyleSheet(DARK_THEME_QSS)
   ```

4. **Context menus**:
   - Right-click register → "Generate C Header", "Export to Excel", "Validate"
   - Right-click IP core → "Show Dependencies", "Open in Editor"

5. **Intelligent autocomplete**:
   ```python
   # AI-powered field suggestions
   class RegisterNameCompleter(QCompleter):
       def __init__(self, ai_assistant: AiAssistantPlugin):
           super().__init__()
           self.ai = ai_assistant
       
       def complete_register_name(self, partial: str, context: IpCore) -> List[str]:
           """Suggest register names based on IP core context."""
           return self.ai.suggest_register_names(f"{context.description} {partial}")
   ```

**Deliverable:** Polished, AI-enhanced, keyboard-driven UI

---

### 6.4 Performance & Stability (Week 21)

**Tasks:**
1. **Lazy loading**:
   - Parse full IP core only when opened (not during indexing)
   - Virtualize large register lists (QAbstractItemModel)

2. **Error handling**:
   - Graceful degradation if plugin fails to load
   - Show error dialog with actionable message

3. **Memory optimization**:
   - Close unused tabs automatically
   - Clear undo history for old edits

4. **Profiling and optimization**:
   ```bash
   # Profile CPU usage
   python -m cProfile -o profile.stats fpga_tool gui
   
   # Profile GPU usage
   nsys profile --stats=true python fpga_tool gui
   
   # Monitor memory
   py-spy record -o profile.svg -- python fpga_tool gui
   ```

5. **Adaptive performance**:
   ```python
   # fpga_lib/perf/adaptive.py
   class AdaptivePerformanceManager:
       def __init__(self):
           self.config = PerformanceConfig.auto_detect()
       
       def optimize_for_workload(self, num_files: int, avg_file_size: int):
           """Adjust strategy based on workload."""
           if num_files > 10000:
               # Use distributed processing
               self.enable_distributed()
           elif num_files > 1000:
               # Use multiprocessing
               self.enable_multiprocessing()
           
           if torch.cuda.is_available() and avg_file_size > 1_000_000:
               # GPU beneficial for large files
               self.enable_gpu()
   ```

**Deliverable:** Fast, stable, auto-optimizing application

---

### 6.5 Documentation & Examples (Week 22)

**Tasks:**
1. **User guide**:
   - Quick start tutorial
   - Plugin development guide
   - API reference (Sphinx)

2. **Video tutorials**:
   - "Creating your first IP core"
   - "Converting VHDL to YAML"
   - "Setting up a project library"

3. **Performance configuration guide**:
   ```markdown
   # Performance Optimization Guide
   
   ## CPU-Only Systems
   - Set `use_multiprocessing=True`
   - Workers = CPU cores - 1
   
   ## GPU-Enabled Systems (NVIDIA/AMD)
   - Set `use_gpu=True`
   - Batch size = 1024 for RTX 3080+
   - Use GPU for: semantic search, batch validation
   
   ## Distributed Clusters
   - Set up Ray cluster
   - Configure workers across nodes
   - Ideal for 10,000+ IP core projects
   
   ## Cloud Deployment
   - AWS Lambda: Serverless parsing
   - S3: Store index and embeddings
   - SageMaker: Host embedding model
   ```

4. **Example projects**:
   ```
   examples/
       projects/
           simple_soc/
               cpu.yml
               timer.yml
               uart.yml
               gpio.yml
           video_pipeline/
               scaler.yml
               filter.yml
               dma.yml
           enterprise_soc/  # Large project demonstrating distributed processing
               1000+ IP cores
               benchmark_results.md
   ```

4. **Plugin template**:
   ```bash
   fpga-tool plugin new my_plugin
   # Generates skeleton plugin structure
   ```

**Deliverable:** Comprehensive documentation

---

## Summary: Implementation Timeline

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1: Core Foundation** | 3 weeks | Pydantic models, parser/generator registry, CLI tool |
| **Phase 2: CLI Tool** | 2 weeks | Working CLI, tests, docs |
| **Phase 3: Library Manager** | 3 weeks | Parallel indexing, AI semantic search, dependency graph |
| **Phase 4: GUI Foundation** | 4 weeks | Plugin host, event bus, first plugin (memory map editor) |
| **Phase 5: Additional Plugins** | 5 weeks | Explorer, bus config, preview, AI assistant, docs |
| **Phase 6: Advanced Features** | 5 weeks | GPU acceleration, distributed processing, AI integration, polish |
| **Total** | **22 weeks** (~5.5 months) | Full-featured AI-enhanced application |

### Hardware Requirements by Tier

| Tier | CPU | RAM | GPU | Use Case |
|------|-----|-----|-----|----------|
| **Basic** | 4 cores | 8 GB | None | Small projects (<100 cores), keyword search |
| **Standard** | 8 cores | 16 GB | None | Medium projects (<1000 cores), semantic search on CPU |
| **Advanced** | 16 cores | 32 GB | RTX 3060+ | Large projects (<10K cores), GPU-accelerated search |
| **Enterprise** | Cluster | Distributed | Multi-GPU | Massive projects (10K+ cores), distributed indexing |

---

## Key Success Factors

1. **Start with CLI**: Validate core library before building GUI
2. **Plugin architecture first**: Don't build monolithic GUI
3. **Incremental releases**: Ship CLI tool after Phase 2, GUI shell after Phase 4
4. **Test continuously**: Each phase has tests before moving forward
5. **Document as you go**: API docs written alongside code
6. **Performance from day one**: Use multiprocessing by default, GPU when available
7. **AI as enhancement**: Traditional search works without AI, but AI improves UX
8. **Privacy-first AI**: Support local LLMs (llama.cpp) for air-gapped environments
9. **Graceful degradation**: All features work on CPU-only systems, GPU optional

---

## Next Steps (Immediate Actions)

1. **Week 1, Day 1**: Define `IpCore` Pydantic model in `fpga_lib/model/core.py`
2. **Week 1, Day 2**: Integrate with existing `Register` class
3. **Week 1, Day 3**: Add validation methods
4. **Week 1, Day 4-5**: Create test suite for models
5. **Week 1, Day 5**: Add performance config with multiprocessing support

## Optional Dependencies by Feature

```toml
# pyproject.toml
[project.optional-dependencies]
# Multiprocessing (enabled by default, no extra deps)
multiprocessing = []

# GPU acceleration (NVIDIA CUDA)
gpu = [
    "torch>=2.0",
    "cupy-cuda12x>=12.0",  # Match your CUDA version
]

# AI features (semantic search, code generation)
ai = [
    "sentence-transformers>=2.2",
    "transformers>=4.30",
    "llama-cpp-python>=0.2",  # Local LLM support
    "openai>=1.0",  # Optional: API-based LLM
]

# Distributed processing (enterprise)
distributed = [
    "ray[default]>=2.5",
]

# Full installation (all features)
full = [
    "fpga_lib[gpu,ai,distributed]",
]
```

**Installation Examples:**
```bash
# Basic (CPU only, multiprocessing)
pip install fpga_lib

# With AI features (CPU-based embeddings)
pip install fpga_lib[ai]

# With GPU acceleration
pip install fpga_lib[gpu,ai]

# Enterprise (all features)
pip install fpga_lib[full]
```

This plan builds incrementally, allowing you to ship useful tools early (CLI) while working toward the full vision (AI-enhanced, GPU-accelerated, plugin-based GUI). Each phase has clear deliverables and can be validated independently. Performance optimizations (multiprocessing, GPU, distributed) are designed as opt-in enhancements that don't break the core functionality.
