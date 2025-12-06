# Implementation Plan for FPGA IP Core Management Application

Based on the comprehensive architecture in `docs/notes.md`, here's a phased implementation plan that builds incrementally from foundational components to the full plugin-based GUI system.

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

2. **VHDL Parser** (enhance existing):
   - Build on existing `fpga_lib/parser/hdl/vhdl_parser.py`
   - Use `pyparsing` for robust entity extraction
   - Handle generics, ports with expressions (`DATA_WIDTH - 1`)
   - Extract bus interface hints from comments or pragmas

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

**Deliverable:** Pluggable parser system that converts YAML/VHDL → `IpCore` model

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

## Phase 3: IP Core Library Manager (Weeks 6-8)

### 3.1 Indexing System (Week 6)
**Goal:** Fast discovery and search

**Tasks:**
1. **SQLite index schema**:
   ```sql
   -- fpga_lib/library/schema.sql
   CREATE TABLE ip_cores ( ... );  -- As defined in notes.md
   CREATE VIRTUAL TABLE ip_cores_fts USING fts5( ... );
   CREATE TABLE dependencies ( ... );
   CREATE TABLE bus_interfaces ( ... );
   ```

2. **Indexer implementation**:
   ```python
   # fpga_lib/library/indexer.py
   class IpCoreIndexer:
       def __init__(self, project_root: Path, index_db: Path):
           # As detailed in notes.md
           pass
       
       def scan_project(self) -> None:
           """Initial scan (runs once)."""
           pass
       
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

4. **Query engine**:
   ```python
   # fpga_lib/library/query.py
   class IpCoreQuery:
       def find_by_name(self, pattern: str) -> List[IpCoreMetadata]:
           pass
       
       def find_axi_slaves(self) -> List[IpCoreMetadata]:
           pass
       
       def full_text_search(self, query: str) -> List[IpCoreMetadata]:
           pass
   ```

**Deliverable:** Fast indexing and search backend

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

## Phase 5: Additional Plugins (Weeks 13-16)

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

2. **Search bar**:
   ```python
   class SearchWidget(QWidget):
       def __init__(self, library: LibraryManager):
           super().__init__()
           self.library = library
           self.search_input = QLineEdit()
           self.search_input.textChanged.connect(self.on_search)
       
       def on_search(self, text: str):
           results = self.library.search(text)
           self.results_tree.populate(results)
   ```

**Deliverable:** IP core library navigation plugin

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

### 5.4 Documentation Generator Plugin (Week 16)

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

## Phase 6: Polish & Release (Weeks 17-20)

### 6.1 User Experience (Weeks 17-18)

**Tasks:**
1. **Command palette** (VS Code style):
   ```python
   # fpga_lib/gui/command_palette.py
   class CommandPalette(QDialog):
       def __init__(self, plugin_manager: PluginManager):
           super().__init__()
           self.commands = self._collect_commands(plugin_manager)
       
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

**Deliverable:** Polished, keyboard-driven UI

---

### 6.2 Performance & Stability (Week 19)

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

4. **Profiling**:
   ```bash
   python -m cProfile -o profile.stats fpga_tool gui
   python -m pstats profile.stats
   ```

**Deliverable:** Fast, stable application

---

### 6.3 Documentation & Examples (Week 20)

**Tasks:**
1. **User guide**:
   - Quick start tutorial
   - Plugin development guide
   - API reference (Sphinx)

2. **Video tutorials**:
   - "Creating your first IP core"
   - "Converting VHDL to YAML"
   - "Setting up a project library"

3. **Example projects**:
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
| **Phase 3: Library Manager** | 3 weeks | Fast indexing, search, dependency graph |
| **Phase 4: GUI Foundation** | 4 weeks | Plugin host, event bus, first plugin (memory map editor) |
| **Phase 5: Additional Plugins** | 4 weeks | Explorer, bus config, preview, docs |
| **Phase 6: Polish** | 4 weeks | UX, performance, documentation |
| **Total** | **20 weeks** (~5 months) | Full-featured application |

---

## Key Success Factors

1. **Start with CLI**: Validate core library before building GUI
2. **Plugin architecture first**: Don't build monolithic GUI
3. **Incremental releases**: Ship CLI tool after Phase 2, GUI shell after Phase 4
4. **Test continuously**: Each phase has tests before moving forward
5. **Document as you go**: API docs written alongside code

---

## Next Steps (Immediate Actions)

1. **Week 1, Day 1**: Define `IpCore` Pydantic model in `fpga_lib/model/core.py`
2. **Week 1, Day 2**: Integrate with existing `Register` class
3. **Week 1, Day 3**: Add validation methods
4. **Week 1, Day 4-5**: Create test suite for models

This plan builds incrementally, allowing you to ship useful tools early (CLI) while working toward the full vision (plugin-based GUI). Each phase has clear deliverables and can be validated independently.
