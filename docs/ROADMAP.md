# Project Roadmap

This document outlines the future development plans for the IP Core Manager ecosystem.

## Phase 1: Core Library & CLI (✅ Completed)
*   [x] **Canonical Data Model**: Pydantic-based `IpCore` model.
*   [x] **CLI Tool**: `ipcore` command for parsing/generating.
*   [x] **AI VHDL Parser**: Pure LLM-based parsing with automatic bus detection.
*   [x] **Drivers**: Python drivers for Cocotb and Hardware.

---

## Phase 2: Library Management (Planned)

The goal is to provide **project-level management** for entire libraries of IP cores, solving discovery and dependency problems.

### 2.1 Indexing System
*   **Concept**: Incremental indexing of YAML/VHDL files using file system watchers.
*   **Tech**: SQLite with FTS5 for sub-millisecond full-text search.
*   **Query Engine**: Find cores by strict bus types (e.g., "Find all AXI4-Lite Slaves").

### 2.2 Semantic Search
*   **Concept**: AI-powered search to find cores by functionality ("timer", "counter") rather than just keyword match.
*   **Implementation**: Vector embeddings of core descriptions.

### 2.3 Dependency Graph
*   **Concept**: Visualize and manage dependencies between cores (imports, sub-cores).
*   **Features**: Cycle detection, build order generation.

---

## Phase 3: Modular GUI Architecture (Planned)

The GUI should be a **Plugin Host**, not a monolithic application.

### 3.1 Plugin System
*   **Core**: Minimal host providing Event Bus, Service Registry, and View Management.
*   **Plugins**: All functionality (Editors, Viewers, Generators) implemented as plugins.
    *   *Memory Map Editor*
    *   *Bus Configurator*
    *   *Documentation Generator*
    *   *Code Preview*

### 3.2 Usability Features
*   **Command Palette**: VS Code style `Ctrl+Shift+P` for keyboard workflow.
*   **Context-Aware Actions**: Right-click actions injected by plugins.
*   **Global Search**: Unified search across all registers, fields, and files.

---

## Phase 4: Integration
*   [ ] **Vivado/Quartus Integration**: Tcl script generation for project creation.
*   [ ] **IP-XACT Support**: Full import/export compliance.
*   [ ] **C/Header Generation**: Automatic driver header generation.
