Here is a detailed summary of our architectural discussion for the **IP Core Manager**.

We have progressively designed a robust, maintainable, and extensible system. The core theme has been to **separate concerns** and **validate data at the boundaries**.

-----

### \#\# 1. The Core Problem & Initial Patterns

You started by asking about design patterns, which led to the core architecture for your project.

  * **Project:** An "IP Core Manager" that parses blueprints (YAML, IP-XACT, etc.) to generate HDL (VHDL, Verilog) and other artifacts (Vivado XML, etc.). It must also reverse-engineer HDL back into a blueprint.
  * **Initial Patterns:**
      * **Strategy:** Chosen to handle the *interchangeable algorithms* for parsing and generating. Instead of one giant `if` block, we define a common interface (e.g., `IIpParser`) and create concrete strategies (`YamlParser`, `IpxactParser`).
      * **Factory:** Chosen to *create* the correct strategy. The main code shouldn't know how to build a `YamlParser`. It just asks a `ParserFactory` to `get_parser("yaml")`.
      * **Facade:** Chosen to *hide all this complexity* from the end-user. The user just interacts with a single `IpCoreManager` class and calls simple methods like `manager.convert("in.yaml", "out.vhd")`.

-----

### \#\# 2. The Overall Architecture: "Hub and Spoke"

Instead of writing a direct converter for every input-to-output combination (e.g., `YAML -> VHDL`, `IPXACT -> VHDL`, `YAML -> Vivado`), we chose a "Hub and Spoke" model.

  * **The Hub:** A central, in-memory **Canonical Data Model**. This is the single source of truth that represents an IP core in a format-agnostic way.
  * **The Spokes:**
      * **Input (Parsers):** A set of strategies that convert a specific format *into* the Canonical Model (e.g., `YamlParser -> Model`).
      * **Output (Generators):** A set of strategies that convert the Canonical Model *into* a specific output (e.g., `Model -> VhdlGenerator`).

**Why?** This prevents a "combinatorial explosion."

  * To add **1** new input (e.g., `JSON`), you write **1** new parser. It automatically works with all existing generators.
  * To add **1** new output (e.g., `Quartus Project`), you write **1** new generator. It automatically works with all existing parsers.

-----

### \#\# 3. The "Hub": Pydantic \> Dataclasses

We had to decide what to use for our Canonical Model.

  * **Decision:** We chose **Pydantic's `BaseModel`** over Python's built-in `@dataclass`.
  * **Why?** **Validation of untrusted external data.** Your YAML/TOML files are "external" and cannot be trusted.
      * `@dataclass` *trusts* data. If you give it a string (`"256"`) for a field type-hinted as `int`, it will silently accept the string, causing bugs later.
      * `pydantic` *validates* data. It will **coerce** `"256"` into the integer `256`. More importantly, if you provide invalid data (e.g., `offset: -1` for a field with `Field(ge=0)`), Pydantic will **raise a clear `ValidationError`** and stop the program, telling the user exactly what is wrong. This "fail-fast" behavior is essential.

**Example:**

```python
# Pydantic model enforces rules
class Register(BaseModel):
    name: str
    offset: int = Field(ge=0) # Must be >= 0

# This data from YAML will be COERCED and VALIDATED
data = {"name": "CONTROL_REG", "offset": "256"}
reg = Register.model_validate(data) 
# reg.offset is now the INTEGER 256

# This data will FAIL FAST
invalid_data = {"name": "STATUS_REG", "offset": -1}
try:
    reg = Register.model_validate(invalid_data)
except ValidationError as e:
    print(e) # Prints a clear error
```

-----

### \#\# 4. The "Spokes": Choosing the Right Tools

We identified specialized tools for our parsers and generators.

  * **`pyparsing`:** Chosen for the `VhdlParser` and `VerilogParser`.
      * **Why?** Simple regular expressions (`re`) are not powerful enough to parse complex, nested languages like HDL. `pyparsing` lets you define a formal "grammar" to robustly parse text, handle comments, and extract data into a structured format.
  * **`bitstring`:** Chosen for the logic *inside* your generators.
      * **Why?** To handle bit-level math safely. When building a register's default value (e.g., `0xA0000001`) from multiple fields, `bitstring` avoids all the error-prone bit-shifting (`<<`) and masking (`&`) logic.
      * **Example:** You can create a `BitArray(length=32)` and use `.overwrite()` to "paste" the bit-values of each field into the correct position.
  * **`typing`:** Chosen for *all* code.
      * **Why?** To make the code readable, self-documenting, and verifiable by static analysis tools (like `mypy`). It's the "contract" for all our functions and models.

-----

### \#\# 5. Evolving the Model: From Simple to Robust

We refined the Pydantic model step-by-step to handle real-world hardware complexities.

#### Step 1: Handling Expressions (e.g., `DATA_WIDTH - 1`)

  * **Problem:** A port's width isn't always a number; it can be a generic expression.
  * **Decision:** Use `Union[int, str]`.
  * **Why?** Pydantic will parse `7` as an `int` and `"DATA_WIDTH - 1"` as a `str`. Our Jinja2 template just prints this value, letting the VHDL compiler (the tool that understands expressions) do the work.
  * **Example:** `msb: Union[int, str] = 0`

#### Step 2: Handling Custom Types (e.g., `own_t`)

  * **Problem:** Some ports (`clk_i`, `port_a : own_t`) have no range.
  * **Decision:** Make `msb` and `lsb` `Optional`.
  * **Why?** This is more flexible. If the YAML omits `msb`/`lsb`, the model stores `None`.
  * **Example:** `msb: Optional[Union[int, str]] = None`

#### Step 3: Removing Logic from Templates (Handling `to`/`downto`)

  * **Problem:** The template logic became complex (`{% if p.msb %}...{% endif %}`) and didn't support both `to` and `downto`.
  * **Decision:** Move all logic into a **computed `@property`** in the Pydantic model.
  * **Why?** This is the **"Dumb Template, Smart Model"** principle. Templates should just print values, not contain logic. The Python property is pure, testable, and handles all cases (no range, `to`, `downto`).

**Example:**

```python
class Port(BaseModel):
    name: str
    msb: Optional[Union[int, str]] = None
    lsb: Optional[Union[int, str]] = None
    range_direction: RangeDirection = Field(default="downto")
    
    @property
    def range_string(self) -> str:
        """This property contains all the logic."""
        if self.msb is None:
            return ""
        return f" ( {self.msb} {self.range_direction.value} {self.lsb} )"

# The Jinja2 template becomes trivially simple:
# {{ p.name }} : {{ p.direction }} {{ p.type }}{{- p.range_string -}};
```

#### Step 4: Ensuring Correctness (Enum vs. `str`)

  * **Problem:** A simple `str` for `range_direction` allows typos like `"donwto"`.
  * **Decision:** Use `class RangeDirection(str, Enum)`.
  * **Why?** **Fail-Fast Validation.** Pydantic now *enforces* that the value must be `"to"` or `"downto"`. If a user makes a typo, the program fails immediately with a clear error, rather than generating broken VHDL. Inheriting from `str` gives us the validation of an `Enum` with the simple string storage of a `str`.

This process has led us to a clean, highly modular, and validated architecture that is easy to maintain and extend.

-----

### ## 6. GUI Architecture: Plugin-Based Extensibility

The GUI layer builds upon the same architectural principles, with an emphasis on **modularity**, **extensibility**, and **world-class usability**. The core idea is that the GUI is not monolithic—it's a **plugin host** with a minimal core and rich plugin ecosystem.

#### The Core Problem

  * **Varied Use Cases:** Different teams need different views of IP cores:
      * Verification engineers need register maps and test vector generation
      * RTL designers need bus interface configuration
      * Documentation teams need export to Word/PDF
      * System architects need visual block diagrams
  * **Evolving Requirements:** New features (e.g., power analysis, timing constraints) should not require rewriting the entire GUI.
  * **Distribution:** Some teams may only need specific plugins, not the entire toolset.

#### Architecture: The Plugin Host Pattern

We separate the GUI into three layers:

```
┌─────────────────────────────────────────┐
│         Plugin Layer (Extensions)        │
│  Memory Map Editor | Bus Config | Docs  │
│  Power Analyzer | Timing Editor | etc.  │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│        Core Framework (Host)             │
│  Plugin Manager | Event Bus | Services  │
│  View Management | Data Validation       │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│       Domain Model (Shared)              │
│  Pydantic Models | Core Business Logic  │
└─────────────────────────────────────────┘
```

**Layer 1: Domain Model (Shared Foundation)**

  * The same Pydantic models from the core library (`IpCore`, `Register`, `BitField`, etc.)
  * **Why?** Single source of truth. Validation happens once at the boundary.
  * All plugins read/write through these validated models.

**Layer 2: Core Framework (The Host)**

The minimal, stable core that all plugins depend on:

  * **Plugin Manager:**
      * Discovers plugins via entry points or a plugin directory
      * Loads/unloads plugins dynamically
      * Manages plugin lifecycle (initialize, activate, deactivate, cleanup)
      * Resolves dependencies between plugins
  * **Event Bus (Pub/Sub):**
      * Central message broker for loose coupling
      * Plugins subscribe to events (`register_modified`, `bitfield_changed`, `file_loaded`)
      * Plugins publish events without knowing who's listening
      * **Why?** Eliminates tight coupling. The Memory Map Editor doesn't need to know about the Documentation Generator. When a register changes, it publishes `register_modified`. Any interested plugin (docs, code generator, validation) can react.
  * **Service Registry:**
      * Plugins register services they provide (`IValidationService`, `IExportService`)
      * Other plugins consume services by interface, not concrete class
      * **Why?** Inversion of Control. A plugin can request "give me all validation services" and the framework provides them, even if they come from 3rd-party plugins.
  * **View Management:**
      * Dockable window system (Qt's QDockWidget or similar)
      * Tab groups, split views, floating windows
      * Persistent layout (save/restore user's preferred arrangement)
  * **Data Manager:**
      * Centralized access to the current `IpCore` model
      * Undo/Redo stack (Command pattern)
      * Dirty state tracking (has the model changed since last save?)

**Layer 3: Plugin Layer (The Extensions)**

Each plugin is a self-contained package that provides specific functionality:

**Example 1: Memory Map Editor Plugin**

  * **What it does:**
      * Tree view of registers/fields (the left panel)
      * Register detail form (the right panel)
      * Bit field visualizer
      * Live debug value comparison
  * **What it provides:**
      * Registers as a service: `IRegisterEditorService`
      * Subscribes to: `file_loaded`, `register_selected`
      * Publishes: `register_modified`, `bitfield_changed`
  * **How it's isolated:**
      * Lives in its own module: `plugins/memory_map_editor/`
      * Has its own entry point in `setup.py`:
        ```python
        entry_points={
            'fpga_lib.plugins': [
                'memory_map_editor = plugins.memory_map_editor:MemoryMapEditorPlugin'
            ]
        }
        ```
      * Can be distributed separately

**Example 2: Bus Interface Configuration Plugin**

  * **What it does:**
      * Visual editor for AXI4L/AXIS/Avalon interfaces
      * Port width override configuration
      * Signal mapping (logical ↔ physical)
      * Protocol validation (e.g., "AXI requires WDATA width = WSTRB width × 8")
  * **What it provides:**
      * Service: `IBusConfigService`
      * Subscribes to: `ip_core_loaded`
      * Publishes: `bus_interface_modified`

**Example 3: Documentation Generator Plugin**

  * **What it does:**
      * Export register map to PDF/Word/Markdown
      * Generate memory map diagrams
      * Include timing diagrams from IP-XACT
  * **What it provides:**
      * Service: `IExportService`
      * Subscribes to: `register_modified` (auto-regenerate docs)
      * Publishes: `export_complete`

**Example 4: Code Generation Preview Plugin**

  * **What it does:**
      * Live preview of generated VHDL/Verilog
      * Syntax highlighting
      * Diff view (before/after changes)
  * **What it provides:**
      * Service: `IPreviewService`
      * Subscribes to: `register_modified`, `bus_interface_modified`
      * Publishes: `preview_updated`

#### Plugin Contract (The Interface)

Every plugin must implement:

```python
class IPlugin(ABC):
    """Base interface for all plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin display name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version (semver)."""
        pass
    
    @property
    def dependencies(self) -> List[str]:
        """List of plugin names this depends on."""
        return []
    
    @abstractmethod
    def initialize(self, context: PluginContext) -> None:
        """Called once when plugin is loaded.
        
        Args:
            context: Provides access to event bus, service registry, etc.
        """
        pass
    
    @abstractmethod
    def activate(self) -> None:
        """Called when plugin should show its UI / start its services."""
        pass
    
    @abstractmethod
    def deactivate(self) -> None:
        """Called when plugin should hide its UI / stop its services."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Called when plugin is being unloaded."""
        pass
```

#### Event Bus Design

```python
class Event(BaseModel):
    """Base event type."""
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    source_plugin: str

class RegisterModifiedEvent(Event):
    event_type: Literal["register_modified"] = "register_modified"
    register_name: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Dict[str, Any]

class EventBus:
    """Central pub/sub message broker."""
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        pass
    
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        pass
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type."""
        pass
```

**Example Usage:**

```python
# In Memory Map Editor Plugin
def on_register_changed(self, register: Register):
    event = RegisterModifiedEvent(
        source_plugin="memory_map_editor",
        register_name=register.name,
        new_value=register.model_dump()
    )
    self.event_bus.publish(event)

# In Documentation Generator Plugin
def on_register_modified(self, event: RegisterModifiedEvent):
    # Auto-regenerate docs when register changes
    self.regenerate_docs()

# During plugin initialization
self.event_bus.subscribe("register_modified", self.on_register_modified)
```

#### Service Registry Design

```python
class IService(ABC):
    """Base interface for all services."""
    pass

class IValidationService(IService):
    """Service for validating IP core data."""
    
    @abstractmethod
    def validate(self, ip_core: IpCore) -> List[ValidationError]:
        """Validate IP core and return errors."""
        pass

class ServiceRegistry:
    """Central registry for services."""
    
    def register_service(self, interface: Type[IService], implementation: IService) -> None:
        """Register a service implementation."""
        pass
    
    def get_service(self, interface: Type[IService]) -> Optional[IService]:
        """Get first service implementing an interface."""
        pass
    
    def get_all_services(self, interface: Type[IService]) -> List[IService]:
        """Get all services implementing an interface."""
        pass
```

**Example Usage:**

```python
# Plugin A registers a validation service
class Axi4ValidationService(IValidationService):
    def validate(self, ip_core: IpCore) -> List[ValidationError]:
        errors = []
        for bus in ip_core.bus_interfaces:
            if bus.type == "AXI4L":
                # Check AXI-specific rules
                if bus.wdata_width != bus.wstrb_width * 8:
                    errors.append(ValidationError("WDATA must be WSTRB × 8"))
        return errors

service_registry.register_service(IValidationService, Axi4ValidationService())

# Plugin B consumes all validation services
validators = service_registry.get_all_services(IValidationService)
all_errors = []
for validator in validators:
    all_errors.extend(validator.validate(current_ip_core))
```

#### World-Class Usability Features

**1. Command Palette (VS Code style)**

  * Keyboard-first workflow: `Ctrl+Shift+P` opens command palette
  * Fuzzy search for all commands across all plugins
  * Recent commands at the top
  * Keyboard shortcuts shown inline

**2. Context-Aware Actions**

  * Right-click on register → "Generate C Header", "Export to Excel", "Validate"
  * Actions provided by plugins that registered for that context
  * Plugins can add actions dynamically

**3. Smart Search**

  * Global search: `Ctrl+T` searches registers, fields, buses, parameters
  * Filter by type: `reg:control` finds registers with "control" in name
  * Jump to definition: Click on a register reference → opens in Memory Map Editor

**4. Integrated Help**

  * Tooltips with bus protocol info (e.g., hover over AWADDR → explains AXI write address channel)
  * Context-sensitive documentation panel
  * Plugin-provided help content

**5. Theme Support**

  * Light/Dark mode
  * High contrast mode for accessibility
  * Customizable syntax highlighting

**6. Workspace Management**

  * Save entire workspace state (open files, layouts, debug values)
  * Project-based organization
  * Recent projects list

#### Extensibility Mechanisms

**1. Slot System (for UI extensions)**

The host defines "slots" where plugins can inject UI:

```python
class UISlot(str, Enum):
    MAIN_TOOLBAR = "main_toolbar"
    CONTEXT_MENU_REGISTER = "context_menu_register"
    PROPERTIES_PANEL = "properties_panel"
    STATUS_BAR = "status_bar"

# Plugin contributes a toolbar button
plugin_context.ui_manager.add_to_slot(
    UISlot.MAIN_TOOLBAR,
    QPushButton("Export", icon=QIcon("export.png"))
)
```

**2. Data Validators (Composable)**

Plugins can register validators that run on save:

```python
@validator_plugin.register
def validate_address_alignment(register: Register) -> Optional[str]:
    if register.address % 4 != 0:
        return "Register address must be 4-byte aligned"
    return None
```

**3. File Format Handlers**

Plugins can register support for new formats:

```python
@plugin.register_parser("json", priority=10)
def parse_json(file_path: Path) -> IpCore:
    # Parse JSON into IpCore model
    pass
```

**4. Template Providers**

Plugins can provide Jinja2 templates for code generation:

```python
plugin.register_template("c_header", "templates/register_map.h.j2")
```

#### Implementation Technology Choices

  * **GUI Framework:** PySide6 (Qt6)
      * **Why?** Mature, cross-platform, professional look
      * Rich widget library (tables, trees, graphics views)
      * Built-in docking system
      * Strong community and documentation
  * **Plugin Loading:** `importlib.metadata` + entry points
      * **Why?** Standard Python mechanism
      * Works with pip/setuptools
      * No custom plugin format needed
  * **Configuration:** TOML files
      * **Why?** Human-readable, supports complex nested data
      * Plugin settings isolated in `plugins/<name>/config.toml`
  * **State Management:** Observer pattern + Event Bus
      * **Why?** Unidirectional data flow
      * Easy to reason about
      * Plugins can't corrupt shared state

#### Example: Adding a New Plugin

A developer wants to add a "Timing Constraints Generator" plugin:

1. Create plugin structure:
```
plugins/timing_generator/
    __init__.py           # PluginClass
    ui/
        timing_editor.py  # QWidget for UI
    services/
        timing_service.py # ITimingService
    templates/
        sdc.j2            # Synopsys Design Constraints template
```

2. Implement `IPlugin`:
```python
class TimingGeneratorPlugin(IPlugin):
    name = "Timing Constraints Generator"
    version = "1.0.0"
    
    def initialize(self, context: PluginContext):
        self.context = context
        self.service = TimingService()
        context.service_registry.register_service(ITimingService, self.service)
        context.event_bus.subscribe("clock_modified", self.on_clock_changed)
```

3. Register in `setup.py`:
```python
entry_points={
    'fpga_lib.plugins': [
        'timing_generator = plugins.timing_generator:TimingGeneratorPlugin'
    ]
}
```

4. Install: `pip install plugins/timing_generator`

5. The plugin appears automatically in the GUI's plugin manager, can be enabled/disabled, and integrates seamlessly.

#### Migration Path: Existing Memory Map Editor

The current monolithic Memory Map Editor becomes a plugin:

  * **Phase 1:** Extract the core framework
      * Move Pydantic models to shared library
      * Create minimal plugin host with event bus
      * Extract Memory Map Editor as first plugin (but keep it working)
  * **Phase 2:** Add plugin infrastructure
      * Implement service registry
      * Add plugin discovery
      * Create plugin API documentation
  * **Phase 3:** Break apart the editor
      * Register detail form → separate plugin
      * Bit field visualizer → separate plugin  
      * Debug mode → separate plugin
      * Each can now evolve independently

**Why This Architecture?**

  * **Modularity:** Each plugin is isolated, testable, and replaceable
  * **Extensibility:** New features = new plugins, no core changes
  * **Scalability:** Large teams can work on separate plugins without conflicts
  * **Usability:** Users install only the plugins they need
  * **Maintainability:** Clear boundaries reduce cognitive load
  * **Professionalism:** Matches patterns from VS Code, IntelliJ, Eclipse—proven at scale

-----

### ## 7. IP Core Project Management: Fast Discovery & Multi-Core Editing

A critical aspect missing from basic editors is **project-level management**. Users don't work on a single IP core—they manage entire libraries. The application must provide **lightning-fast discovery**, **intelligent organization**, and **seamless multi-core editing**.

#### The Core Problems

  * **Discovery:** Finding IP cores scattered across a directory tree is slow
  * **Context Switching:** Opening/closing files manually is tedious
  * **Relationships:** IP cores reference each other (dependencies, bus connections)
  * **Scale:** A project might have 50+ IP cores with hundreds of registers
  * **Filtering:** Users need to quickly find "all AXI4 slaves with interrupts"

#### Solution: The IP Core Library Manager

Think of VS Code's workspace explorer, but specialized for hardware IP.

#### Architecture: Three-Layer Indexing System

```
┌─────────────────────────────────────────┐
│    UI Layer (Explorer Tree)             │
│  Group by: Vendor | Type | Bus | Custom │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│    Search & Filter Engine                │
│  Full-text | Fuzzy | Query DSL           │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│    Fast Index (SQLite FTS5)              │
│  Metadata Cache | Dependency Graph       │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│    File Watcher (Incremental Updates)   │
│  Detects new/modified/deleted YAMLs      │
└─────────────────────────────────────────┘
```

#### Layer 1: Fast Discovery via File System Watching

**The Challenge:** Scanning a large directory tree for YAML files is slow (seconds on network drives).

**The Solution:** Incremental indexing with file system watchers.

```python
class IpCoreIndexer:
    """Fast indexing of IP cores in a project directory."""
    
    def __init__(self, project_root: Path, index_db: Path):
        self.project_root = project_root
        self.db = sqlite3.connect(index_db)
        self._init_database()
        self.watcher = FileSystemWatcher(project_root)
        self.watcher.on_created = self._on_file_created
        self.watcher.on_modified = self._on_file_modified
        self.watcher.on_deleted = self._on_file_deleted
    
    def scan_project(self) -> None:
        """Initial scan of project (only runs once)."""
        for yaml_file in self.project_root.rglob("*.yml"):
            if self._is_ip_core_file(yaml_file):
                self._index_file(yaml_file)
    
    def _is_ip_core_file(self, path: Path) -> bool:
        """Fast heuristic check without full parsing."""
        # Check first few lines for IP-XACT or custom schema markers
        with open(path, 'r') as f:
            header = f.read(500)
            return 'apiVersion:' in header or 'vlnv:' in header
    
    def _index_file(self, path: Path) -> None:
        """Parse and index a single IP core file."""
        try:
            ip_core = self._quick_parse(path)  # Lightweight parse
            self._store_metadata(ip_core, path)
        except Exception as e:
            logger.warning(f"Failed to index {path}: {e}")
    
    def _quick_parse(self, path: Path) -> IpCoreMetadata:
        """Fast parse: extract only metadata, not full model."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        return IpCoreMetadata(
            path=path,
            name=data.get('vlnv', {}).get('name', path.stem),
            vendor=data.get('vlnv', {}).get('vendor', 'unknown'),
            version=data.get('vlnv', {}).get('version', '0.0.0'),
            description=data.get('description', ''),
            bus_interfaces=[bi['type'] for bi in data.get('busInterfaces', [])],
            num_registers=self._count_registers(data),
            last_modified=path.stat().st_mtime,
        )
    
    def _count_registers(self, data: dict) -> int:
        """Quick count without full model validation."""
        memmap = data.get('memoryMaps', {})
        if isinstance(memmap, dict) and 'import' in memmap:
            # Would need to follow import
            return -1  # Unknown
        return len(memmap.get('registers', []))
```

**Key Insight:** Don't parse the full Pydantic model during indexing. Extract only metadata (name, vendor, bus types) for fast display. Full parsing happens only when the user opens the IP core.

#### Layer 2: SQLite Full-Text Search Index

**Why SQLite?**
  * **Fast:** Millions of queries/sec
  * **Full-text search:** SQLite FTS5 supports complex queries
  * **Embedded:** No separate database server
  * **Transactions:** Atomic updates when files change

**Schema:**

```sql
-- Main metadata table
CREATE TABLE ip_cores (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    vendor TEXT,
    library TEXT,
    version TEXT,
    description TEXT,
    bus_interfaces TEXT,  -- JSON array
    num_registers INTEGER,
    num_interrupts INTEGER,
    last_modified REAL,
    last_indexed REAL
);

-- Full-text search virtual table
CREATE VIRTUAL TABLE ip_cores_fts USING fts5(
    name,
    vendor,
    description,
    register_names,  -- Concatenated register names for searching
    content=ip_cores,
    content_rowid=id
);

-- Dependency graph
CREATE TABLE dependencies (
    ip_core_id INTEGER,
    depends_on_path TEXT,
    dependency_type TEXT,  -- 'import', 'bus_connection', etc.
    FOREIGN KEY(ip_core_id) REFERENCES ip_cores(id)
);

-- Bus interface index (for finding compatible cores)
CREATE TABLE bus_interfaces (
    ip_core_id INTEGER,
    interface_name TEXT,
    bus_type TEXT,  -- 'AXI4L', 'AXIS', etc.
    mode TEXT,      -- 'master', 'slave'
    FOREIGN KEY(ip_core_id) REFERENCES ip_cores(id)
);

CREATE INDEX idx_bus_type_mode ON bus_interfaces(bus_type, mode);
```

**Query Examples:**

```python
class IpCoreQuery:
    """Fast queries against the index."""
    
    def find_by_name(self, pattern: str) -> List[IpCoreMetadata]:
        """Fuzzy search by name."""
        return self.db.execute("""
            SELECT * FROM ip_cores 
            WHERE name LIKE ? 
            ORDER BY name
        """, (f"%{pattern}%",)).fetchall()
    
    def find_axi_slaves(self) -> List[IpCoreMetadata]:
        """Find all IP cores with AXI slave interfaces."""
        return self.db.execute("""
            SELECT DISTINCT ic.* 
            FROM ip_cores ic
            JOIN bus_interfaces bi ON ic.id = bi.ip_core_id
            WHERE bi.bus_type = 'AXI4L' AND bi.mode = 'slave'
        """).fetchall()
    
    def full_text_search(self, query: str) -> List[IpCoreMetadata]:
        """Search across names, descriptions, register names."""
        return self.db.execute("""
            SELECT ic.* 
            FROM ip_cores_fts fts
            JOIN ip_cores ic ON fts.rowid = ic.id
            WHERE ip_cores_fts MATCH ?
            ORDER BY rank
        """, (query,)).fetchall()
    
    def find_compatible_masters(self, slave_core_id: int) -> List[IpCoreMetadata]:
        """Find all master cores compatible with a given slave."""
        # Get slave's bus types
        slave_buses = self.db.execute("""
            SELECT bus_type FROM bus_interfaces 
            WHERE ip_core_id = ? AND mode = 'slave'
        """, (slave_core_id,)).fetchall()
        
        # Find masters with matching bus types
        bus_types = [b[0] for b in slave_buses]
        placeholders = ','.join('?' * len(bus_types))
        return self.db.execute(f"""
            SELECT DISTINCT ic.* 
            FROM ip_cores ic
            JOIN bus_interfaces bi ON ic.id = bi.ip_core_id
            WHERE bi.bus_type IN ({placeholders}) 
              AND bi.mode = 'master'
        """, bus_types).fetchall()
```

#### Layer 3: UI - The IP Core Explorer

**Design Principles:**
  * **Instant feedback:** Search results appear as you type (< 50ms)
  * **Multiple views:** Tree, grid, graph (dependency visualization)
  * **Context preservation:** Remember which cores are open, scroll positions
  * **Bulk operations:** Select multiple cores → export all, validate all

**Main UI Components:**

```
┌─────────────────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help                        [Search]│
├─────────────────┬───────────────────────────────────────────┤
│ IP Core Library │  my_timer_core.yml                        │
├─────────────────┤  ┌─────────────────────────────────────┐  │
│ 📁 Project Root │  │ Memory Map Editor                   │  │
│  └📦 Timers (3) │  │  • CTRL_REG [0x00]                  │  │
│     • timer_v1  │  │  • STATUS_REG [0x04]                │  │
│     • timer_v2  │  └─────────────────────────────────────┘  │
│     • watchdog  │  ┌─────────────────────────────────────┐  │
│  └📦 Comm (5)   │  │ Bus Interfaces                      │  │
│     • uart      │  │  S_AXI_LITE: AXI4L Slave            │  │
│     • spi       │  │  M_AXIS_EVENTS[4]: AXIS Master      │  │
│     • i2c       │  └─────────────────────────────────────┘  │
│  └📦 Memory (2) │                                           │
│     • dma       │  [Tabs: Details | Registers | Code | ...]│
│     • cache     │                                           │
├─────────────────┼───────────────────────────────────────────┤
│ 🔍 Find         │  Status: 10 IP cores indexed              │
│  Type: All      │  Last scan: 2s ago                        │
│  Bus: All       │                                           │
│  [Advanced...]  │                                           │
└─────────────────┴───────────────────────────────────────────┘
```

**Tree View Grouping Options:**

```python
class GroupingMode(str, Enum):
    BY_FOLDER = "folder"        # Mirror directory structure
    BY_VENDOR = "vendor"        # Group by vlnv.vendor
    BY_BUS_TYPE = "bus_type"    # Group by AXI4L, AXIS, Avalon, etc.
    BY_FUNCTION = "function"     # Group by library (timers, comm, memory)
    FLAT = "flat"               # No grouping, alphabetical list

class IpCoreExplorerTree(QTreeWidget):
    """Tree view of IP cores with dynamic grouping."""
    
    def __init__(self, indexer: IpCoreIndexer):
        super().__init__()
        self.indexer = indexer
        self.grouping_mode = GroupingMode.BY_FOLDER
        
    def refresh(self):
        """Rebuild tree based on current grouping mode."""
        self.clear()
        cores = self.indexer.get_all_cores()
        
        if self.grouping_mode == GroupingMode.BY_FOLDER:
            self._build_folder_tree(cores)
        elif self.grouping_mode == GroupingMode.BY_VENDOR:
            self._build_vendor_tree(cores)
        elif self.grouping_mode == GroupingMode.BY_BUS_TYPE:
            self._build_bus_type_tree(cores)
    
    def _build_bus_type_tree(self, cores: List[IpCoreMetadata]):
        """Group by bus interface types (AXI4L, AXIS, etc.)."""
        by_bus = defaultdict(list)
        for core in cores:
            for bus_type in core.bus_interfaces:
                by_bus[bus_type].append(core)
        
        for bus_type, core_list in sorted(by_bus.items()):
            bus_item = QTreeWidgetItem([f"📡 {bus_type} ({len(core_list)})"])
            for core in sorted(core_list, key=lambda c: c.name):
                core_item = QTreeWidgetItem([core.name])
                core_item.setData(0, Qt.UserRole, core)
                bus_item.addChild(core_item)
            self.addTopLevelItem(bus_item)
```

#### Fast Search with Query DSL

Support both simple and advanced queries:

**Simple Queries:**
  * `timer` - Search in names/descriptions
  * `vendor:acme` - Filter by vendor
  * `bus:AXI4L` - Filter by bus type
  * `reg:>100` - Filter by register count

**Advanced Query DSL:**

```python
class IpCoreQueryParser:
    """Parse user queries into SQL."""
    
    def parse(self, query: str) -> Tuple[str, List[Any]]:
        """Convert query DSL to SQL.
        
        Examples:
            'timer AND bus:AXI4L' -> Find timers with AXI4L
            'vendor:acme OR vendor:xilinx' -> Multi-vendor search
            'reg:>50 AND int:>0' -> Cores with >50 regs and interrupts
        """
        # Tokenize
        tokens = self._tokenize(query)
        
        # Build SQL WHERE clause
        conditions = []
        params = []
        
        for token in tokens:
            if ':' in token:
                field, value = token.split(':', 1)
                if field == 'vendor':
                    conditions.append("vendor = ?")
                    params.append(value)
                elif field == 'bus':
                    conditions.append("""
                        id IN (
                            SELECT ip_core_id FROM bus_interfaces 
                            WHERE bus_type = ?
                        )
                    """)
                    params.append(value)
                elif field == 'reg':
                    # Handle comparisons: reg:>50, reg:10, reg:<20
                    if value.startswith('>'):
                        conditions.append("num_registers > ?")
                        params.append(int(value[1:]))
                    elif value.startswith('<'):
                        conditions.append("num_registers < ?")
                        params.append(int(value[1:]))
                    else:
                        conditions.append("num_registers = ?")
                        params.append(int(value))
            else:
                # Full-text search
                conditions.append("""
                    id IN (
                        SELECT rowid FROM ip_cores_fts 
                        WHERE ip_cores_fts MATCH ?
                    )
                """)
                params.append(token)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM ip_cores WHERE {where_clause}"
        return sql, params
```

#### Multi-Core Editing: Tab Groups

Users often work on related IP cores simultaneously (e.g., a master and its slave).

**Tab Group Features:**
  * **Linked scrolling:** Scroll through registers of two cores side-by-side
  * **Diff mode:** Compare registers between two versions of an IP core
  * **Cross-references:** Click on a bus interface → automatically open connected IP core

```python
class IpCoreTabManager:
    """Manage multiple open IP cores with intelligent grouping."""
    
    def open_core(self, core_path: Path) -> IpCoreEditorTab:
        """Open or focus existing tab for this core."""
        if core_path in self.open_tabs:
            self.focus_tab(core_path)
            return self.open_tabs[core_path]
        
        # Full parse only when opening (not during indexing)
        ip_core = self.parser.parse(core_path)
        tab = IpCoreEditorTab(ip_core)
        self.tab_widget.addTab(tab, ip_core.name)
        self.open_tabs[core_path] = tab
        return tab
    
    def open_related_cores(self, core: IpCore) -> None:
        """Open all IP cores referenced by this one."""
        # Find dependencies
        deps = self.indexer.get_dependencies(core.path)
        for dep_path in deps:
            self.open_core(dep_path)
    
    def create_linked_view(self, core1: IpCore, core2: IpCore) -> None:
        """Open two cores side-by-side with synchronized scrolling."""
        tab1 = self.open_core(core1.path)
        tab2 = self.open_core(core2.path)
        
        # Link scroll events
        tab1.register_tree.verticalScrollBar().valueChanged.connect(
            tab2.register_tree.verticalScrollBar().setValue
        )
```

#### Incremental Updates: File Watching

When files change on disk (e.g., from git pull or external editor):

```python
class FileSystemWatcher:
    """Watch for changes and incrementally update index."""
    
    def __init__(self, root: Path):
        self.observer = Observer()
        self.handler = IpCoreFileHandler(self.on_file_event)
        self.observer.schedule(self.handler, str(root), recursive=True)
        self.observer.start()
    
    def on_file_event(self, event):
        """Handle file creation/modification/deletion."""
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        if path.suffix not in ['.yml', '.yaml']:
            return
        
        if event.event_type == 'created':
            self.indexer.add_core(path)
            self.ui.explorer.add_core_to_tree(path)
        
        elif event.event_type == 'modified':
            # Re-index just this file
            self.indexer.update_core(path)
            
            # If currently open, offer to reload
            if path in self.tab_manager.open_tabs:
                self.prompt_reload(path)
        
        elif event.event_type == 'deleted':
            self.indexer.remove_core(path)
            self.ui.explorer.remove_core_from_tree(path)
            
            # Close tab if open
            if path in self.tab_manager.open_tabs:
                self.tab_manager.close_tab(path)
```

#### Performance Characteristics

With this architecture:

  * **Initial scan:** 1000 IP cores in ~2 seconds (metadata extraction only)
  * **Search:** < 50ms for any query (SQLite index)
  * **Open core:** ~100ms (full Pydantic validation only on open)
  * **File change detection:** < 10ms (incremental update)
  * **Memory usage:** ~1MB per 1000 indexed cores

#### Smart Features

**1. Recent & Favorites**

```python
class RecentCoresManager:
    """Track recently opened cores."""
    
    def __init__(self):
        self.recent = deque(maxlen=20)  # Last 20 opened
        self.favorites = set()          # User-starred cores
    
    def add_recent(self, core_path: Path):
        if core_path in self.recent:
            self.recent.remove(core_path)
        self.recent.appendleft(core_path)
    
    def toggle_favorite(self, core_path: Path):
        if core_path in self.favorites:
            self.favorites.remove(core_path)
        else:
            self.favorites.add(core_path)
```

**2. Dependency Graph Visualization**

```python
class DependencyGraphView(QGraphicsView):
    """Visual graph of IP core dependencies."""
    
    def show_dependencies(self, core: IpCore):
        """Show all cores this one depends on (and vice versa)."""
        graph = self.indexer.build_dependency_graph(core)
        
        # Use graphviz for layout
        layout = graphviz_layout(graph)
        
        # Draw nodes (IP cores) and edges (dependencies)
        for node, pos in layout.items():
            self.scene.addItem(IpCoreNode(node, pos))
        
        for src, dst in graph.edges:
            self.scene.addItem(DependencyEdge(src, dst))
```

**3. Project Templates**

```python
class ProjectTemplate:
    """Create new IP core from template."""
    
    templates = {
        'axi_slave': {
            'description': 'AXI4-Lite slave with register map',
            'files': ['template_axi_slave.yml', 'template_memmap.yml']
        },
        'axis_filter': {
            'description': 'AXI Stream data filter',
            'files': ['template_axis_filter.yml']
        }
    }
    
    def create_from_template(self, template_name: str, 
                            output_dir: Path, core_name: str):
        """Create new IP core from template."""
        template = self.templates[template_name]
        for file in template['files']:
            content = self.render_template(file, {'name': core_name})
            output_path = output_dir / file.replace('template_', f'{core_name}_')
            output_path.write_text(content)
        
        # Automatically index new core
        self.indexer.scan_directory(output_dir)
```

**Why This Matters:**

  * **Productivity:** Users spend seconds, not minutes, navigating projects
  * **Discoverability:** "Show me all AXI slaves" answered instantly
  * **Context:** Work on multiple related cores without losing state
  * **Scale:** Handles hundreds of IP cores without slowdown
  * **Integration:** Search works across all plugins (regs, buses, docs)
