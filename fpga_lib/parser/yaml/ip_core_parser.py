"""
YAML Parser for IP Core definitions.

Loads YAML files and converts them to canonical Pydantic models.
Supports imports, bus library loading, and memory map references.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from pydantic import ValidationError

from fpga_lib.model import (
    IpCore,
    VLNV,
    Clock,
    Reset,
    Polarity,
    Port,
    PortDirection,
    BusInterface,
    ArrayConfig,
    Parameter,
    MemoryMap,
    AddressBlock,
    Register,
    BitField,
    AccessType,
    FileSet,
    File,
    FileType,
)


class ParseError(Exception):
    """Error during YAML parsing."""

    def __init__(self, message: str, file_path: Optional[Path] = None, line: Optional[int] = None):
        self.file_path = file_path
        self.line = line
        super().__init__(self._format_message(message))

    def _format_message(self, message: str) -> str:
        """Format error message with file and line information."""
        parts = []
        if self.file_path:
            parts.append(f"File: {self.file_path}")
        if self.line is not None:
            parts.append(f"Line: {self.line}")
        parts.append(message)
        return " | ".join(parts)


class YamlIpCoreParser:
    """
    Parser for IP core YAML definitions.

    Handles:
    - Main IP core file parsing
    - Bus library loading and caching
    - Memory map imports (separate files)
    - FileSet imports
    - Validation and error reporting with line numbers
    """

    def __init__(self):
        self._bus_library_cache: Dict[Path, Dict[str, Any]] = {}
        self._register_templates: Dict[str, List[Dict[str, Any]]] = {}
        self._current_file: Optional[Path] = None

    @staticmethod
    def _filter_none(data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove keys with None values from dictionary."""
        return {k: v for k, v in data.items() if v is not None}

    def parse_file(self, file_path: Union[str, Path]) -> IpCore:
        """
        Parse an IP core YAML file.

        Args:
            file_path: Path to the IP core YAML file

        Returns:
            IpCore: Validated IP core model

        Raises:
            ParseError: If parsing or validation fails
        """
        file_path = Path(file_path).resolve()
        self._current_file = file_path

        if not file_path.exists():
            raise ParseError(f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            line = getattr(e, "problem_mark", None)
            line_num = line.line + 1 if line else None
            raise ParseError(f"YAML syntax error: {e}", file_path, line_num)

        if not isinstance(data, dict):
            raise ParseError("Root element must be a YAML object/dictionary", file_path)

        try:
            return self._parse_ip_core(data, file_path)
        except ValidationError as e:
            # Convert Pydantic validation errors to ParseError
            errors = []
            for error in e.errors():
                loc = " -> ".join(str(x) for x in error["loc"])
                errors.append(f"{loc}: {error['msg']}")
            raise ParseError(f"Validation failed:\n  " + "\n  ".join(errors), file_path)

    def _parse_ip_core(self, data: Dict[str, Any], file_path: Path) -> IpCore:
        """Parse the main IP core structure."""
        # Required fields
        api_version = data.get("apiVersion")
        if not api_version:
            raise ParseError("Missing required field: apiVersion", file_path)

        vlnv_data = data.get("vlnv")
        if not vlnv_data:
            raise ParseError("Missing required field: vlnv", file_path)

        # Parse VLNV
        vlnv = self._parse_vlnv(vlnv_data, file_path)

        # Parse optional sections
        description = data.get("description")
        clocks = self._parse_clocks(data.get("clocks", []), file_path)
        resets = self._parse_resets(data.get("resets", []), file_path)
        ports = self._parse_ports(data.get("ports", []), file_path)

        # Load bus library if specified
        bus_library = data.get("useBusLibrary")
        if bus_library:
            # Resolve relative to the current file
            bus_lib_path = (file_path.parent / bus_library).resolve()
            self._load_bus_library(bus_lib_path)

        bus_interfaces = self._parse_bus_interfaces(data.get("busInterfaces", []), file_path)
        parameters = self._parse_parameters(data.get("parameters", []), file_path)

        # Parse memory maps (may include imports)
        memory_maps = self._parse_memory_maps(data.get("memoryMaps", {}), file_path)

        # Parse file sets (may include imports)
        file_sets = self._parse_file_sets(data.get("fileSets", []), file_path)

        # Create IpCore model - use _filter_none to avoid passing None for lists
        kwargs = {
            "api_version": api_version,
            "vlnv": vlnv,
        }
        if description:
            kwargs["description"] = description
        if clocks:
            kwargs["clocks"] = clocks
        if resets:
            kwargs["resets"] = resets
        if ports:
            kwargs["ports"] = ports
        if bus_interfaces:
            kwargs["bus_interfaces"] = bus_interfaces
        if memory_maps:
            kwargs["memory_maps"] = memory_maps
        if parameters:
            kwargs["parameters"] = parameters
        if file_sets:
            kwargs["file_sets"] = file_sets
        if bus_library:
            kwargs["use_bus_library"] = bus_library

        return IpCore(**kwargs)

    def _parse_vlnv(self, data: Dict[str, Any], file_path: Path) -> VLNV:
        """Parse VLNV structure."""
        required = ["vendor", "library", "name", "version"]
        for field in required:
            if field not in data:
                raise ParseError(f"VLNV missing required field: {field}", file_path)

        return VLNV(
            vendor=data["vendor"],
            library=data["library"],
            name=data["name"],
            version=data["version"],
        )

    def _parse_clocks(self, data: List[Dict[str, Any]], file_path: Path) -> List[Clock]:
        """Parse clock definitions."""
        clocks = []
        for idx, clock_data in enumerate(data):
            try:
                # Convert camelCase to snake_case for Pydantic
                clocks.append(
                    Clock(
                        **self._filter_none({
                            "name": clock_data.get("name"),
                            "physical_port": clock_data.get("physicalPort"),
                            "direction": clock_data.get("direction", "in"),
                            "frequency": clock_data.get("frequency"),
                            "description": clock_data.get("description"),
                        })
                    )
                )
            except Exception as e:
                raise ParseError(f"Error parsing clock[{idx}]: {e}", file_path)
        return clocks

    def _parse_resets(self, data: List[Dict[str, Any]], file_path: Path) -> List[Reset]:
        """Parse reset definitions."""
        resets = []
        for idx, reset_data in enumerate(data):
            try:
                # Map polarity string to enum
                polarity_str = reset_data.get("polarity", "activeLow")
                polarity = Polarity.ACTIVE_LOW if polarity_str == "activeLow" else Polarity.ACTIVE_HIGH

                resets.append(
                    Reset(
                        **self._filter_none({
                            "name": reset_data.get("name"),
                            "physical_port": reset_data.get("physicalPort"),
                            "direction": reset_data.get("direction", "in"),
                            "polarity": polarity,
                            "description": reset_data.get("description"),
                        })
                    )
                )
            except Exception as e:
                raise ParseError(f"Error parsing reset[{idx}]: {e}", file_path)
        return resets

    def _parse_ports(self, data: List[Dict[str, Any]], file_path: Path) -> List[Port]:
        """Parse port definitions."""
        ports = []
        for idx, port_data in enumerate(data):
            try:
                ports.append(
                    Port(
                        **self._filter_none({
                            "name": port_data.get("name"),
                            "physical_port": port_data.get("physicalPort"),
                            "direction": port_data.get("direction"),
                            "width": port_data.get("width", 1),
                            "description": port_data.get("description"),
                        })
                    )
                )
            except Exception as e:
                raise ParseError(f"Error parsing port[{idx}]: {e}", file_path)
        return ports

    def _parse_bus_interfaces(
        self, data: List[Dict[str, Any]], file_path: Path
    ) -> List[BusInterface]:
        """Parse bus interface definitions."""
        interfaces = []
        for idx, bus_data in enumerate(data):
            try:
                # Parse array configuration if present
                array_config = None
                if "array" in bus_data:
                    array_data = bus_data["array"]
                    array_config = ArrayConfig(
                        count=array_data.get("count"),
                        index_start=array_data.get("indexStart", 0),
                        naming_pattern=array_data.get("namingPattern"),
                        physical_prefix_pattern=array_data.get("physicalPrefixPattern"),
                    )

                interfaces.append(
                    BusInterface(
                        **self._filter_none({
                            "name": bus_data.get("name"),
                            "type": bus_data.get("type"),
                            "mode": bus_data.get("mode"),
                            "physical_prefix": bus_data.get("physicalPrefix"),
                            "associated_clock": bus_data.get("associatedClock"),
                            "associated_reset": bus_data.get("associatedReset"),
                            "memory_map_ref": bus_data.get("memoryMapRef"),
                            "use_optional_ports": bus_data.get("useOptionalPorts"),
                            "port_width_overrides": bus_data.get("portWidthOverrides"),
                            "array": array_config,
                        })
                    )
                )
            except Exception as e:
                raise ParseError(f"Error parsing busInterface[{idx}]: {e}", file_path)
        return interfaces

    def _parse_parameters(self, data: List[Dict[str, Any]], file_path: Path) -> List[Parameter]:
        """Parse parameter definitions."""
        parameters = []
        for idx, param_data in enumerate(data):
            try:
                parameters.append(
                    Parameter(
                        **self._filter_none({
                            "name": param_data.get("name"),
                            "value": param_data.get("value"),
                            "data_type": param_data.get("dataType", "integer"),
                            "description": param_data.get("description"),
                        })
                    )
                )
            except Exception as e:
                raise ParseError(f"Error parsing parameter[{idx}]: {e}", file_path)
        return parameters

    def _parse_memory_maps(
        self, data: Union[Dict[str, Any], List[Dict[str, Any]]], file_path: Path
    ) -> List[MemoryMap]:
        """
        Parse memory maps, handling imports.

        Supports both:
        - memoryMaps: { import: "file.yml" }
        - memoryMaps: [{ name: "MAP1", ... }]
        """
        if not data:
            return []

        # Handle import case
        if isinstance(data, dict) and "import" in data:
            import_path = (file_path.parent / data["import"]).resolve()
            return self._load_memory_maps_from_file(import_path)

        # Handle inline list
        if isinstance(data, list):
            return self._parse_memory_map_list(data, file_path)

        raise ParseError("memoryMaps must be either {import: ...} or a list", file_path)

    def _load_memory_maps_from_file(self, file_path: Path) -> List[MemoryMap]:
        """Load memory maps from an external YAML file."""
        if not file_path.exists():
            raise ParseError(f"Memory map file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                docs = list(yaml.safe_load_all(f))  # Support multi-document YAML
        except yaml.YAMLError as e:
            raise ParseError(f"YAML syntax error in memory map file: {e}", file_path)

        # First document might contain templates
        if len(docs) > 1 and isinstance(docs[0], dict) and "registerTemplates" in docs[0]:
            self._register_templates = docs[0]["registerTemplates"]
            map_data = docs[1]  # Second document has the actual maps
        else:
            # Single document or no templates
            map_data = docs[-1] if docs else []

        if not isinstance(map_data, list):
            map_data = [map_data]

        return self._parse_memory_map_list(map_data, file_path)

    def _parse_memory_map_list(
        self, data: List[Dict[str, Any]], file_path: Path
    ) -> List[MemoryMap]:
        """Parse a list of memory map definitions."""
        memory_maps = []
        for idx, map_data in enumerate(data):
            try:
                address_blocks = self._parse_address_blocks(
                    map_data.get("addressBlocks", []), file_path
                )

                memory_maps.append(
                    MemoryMap(
                        **self._filter_none({
                            "name": map_data.get("name"),
                            "description": map_data.get("description"),
                            "address_blocks": address_blocks if address_blocks else None,
                        })
                    )
                )
            except Exception as e:
                raise ParseError(f"Error parsing memoryMap[{idx}]: {e}", file_path)
        return memory_maps

    def _parse_address_blocks(
        self, data: List[Dict[str, Any]], file_path: Path
    ) -> List[AddressBlock]:
        """Parse address block definitions."""
        blocks = []
        for idx, block_data in enumerate(data):
            try:
                registers = self._parse_registers(block_data.get("registers", []), file_path)

                blocks.append(
                    AddressBlock(
                        **self._filter_none({
                            "name": block_data.get("name"),
                            "base_address": block_data.get("baseAddress", 0),
                            "range": block_data.get("range"),
                            "description": block_data.get("description"),
                            "usage": block_data.get("usage", "register"),
                            "registers": registers if registers else None,
                        })
                    )
                )
            except Exception as e:
                raise ParseError(f"Error parsing addressBlock[{idx}]: {e}", file_path)
        return blocks

    def _parse_registers(self, data: List[Dict[str, Any]], file_path: Path) -> List[Register]:
        """Parse register definitions, including template expansion."""
        registers = []
        current_offset = 0

        for idx, reg_data in enumerate(data):
            try:
                # Handle reserved space
                if "reserved" in reg_data:
                    current_offset += reg_data["reserved"]
                    continue

                # Handle generateArray - expand template into multiple registers
                if "generateArray" in reg_data:
                    expanded_regs = self._expand_register_array(
                        reg_data["generateArray"], current_offset, file_path
                    )
                    registers.extend(expanded_regs)
                    # Update offset after expanded registers
                    if expanded_regs:
                        last_reg = expanded_regs[-1]
                        current_offset = last_reg.address_offset + (last_reg.size // 8)
                    continue

                # Parse regular register
                address_offset = reg_data.get("addressOffset")
                if address_offset is None:
                    address_offset = current_offset

                size = reg_data.get("size", 32)
                access = reg_data.get("access", "read-write")

                # Normalize access type
                if access in AccessType.__members__.values():
                    access_type = AccessType(access)
                else:
                    # Try to normalize
                    access_type = AccessType.normalize(access)

                fields = self._parse_bit_fields(reg_data.get("fields", []), file_path)

                registers.append(
                    Register(
                        **self._filter_none({
                            "name": reg_data.get("name"),
                            "address_offset": address_offset,
                            "size": size,
                            "access": access_type,
                            "description": reg_data.get("description"),
                            "reset_value": reg_data.get("resetValue"),
                            "fields": fields if fields else None,
                        })
                    )
                )

                # Update offset for next register (align to register size)
                current_offset = address_offset + (size // 8)

            except Exception as e:
                raise ParseError(f"Error parsing register[{idx}]: {e}", file_path)

        return registers

    def _expand_register_array(
        self,
        array_spec: Dict[str, Any],
        start_offset: int,
        file_path: Path
    ) -> List[Register]:
        """
        Expand a generateArray specification into multiple registers.

        Args:
            array_spec: Dict with 'name', 'count', 'template' keys
            start_offset: Starting address offset for the array
            file_path: File path for error reporting

        Returns:
            List of Register instances
        """
        base_name = array_spec.get("name", "REG")
        count = array_spec.get("count", 1)
        template_name = array_spec.get("template")

        if not template_name:
            raise ParseError("generateArray requires 'template' field", file_path)

        if template_name not in self._register_templates:
            raise ParseError(
                f"Register template '{template_name}' not found. Available: {list(self._register_templates.keys())}",
                file_path
            )

        template = self._register_templates[template_name]
        registers = []
        current_offset = start_offset

        # Generate instances for each array element
        for instance_idx in range(count):
            instance_num = instance_idx + 1  # 1-indexed (TIMER1, TIMER2, etc.)

            # Expand each register in the template
            for template_reg in template:
                reg_name = template_reg.get("name", "")

                # Replace '_' prefix with instance name (e.g., "_CTRL" -> "TIMER1_CTRL")
                if reg_name.startswith("_"):
                    reg_name = f"{base_name}{instance_num}{reg_name}"
                else:
                    reg_name = f"{base_name}{instance_num}_{reg_name}"

                # Parse the register with the new name
                size = template_reg.get("size", 32)
                access = template_reg.get("access", "read-write")

                # Normalize access type
                if access in AccessType.__members__.values():
                    access_type = AccessType(access)
                else:
                    access_type = AccessType.normalize(access)

                fields = self._parse_bit_fields(template_reg.get("fields", []), file_path)

                registers.append(
                    Register(
                        **self._filter_none({
                            "name": reg_name,
                            "address_offset": current_offset,
                            "size": size,
                            "access": access_type,
                            "description": template_reg.get("description"),
                            "reset_value": template_reg.get("resetValue"),
                            "fields": fields if fields else None,
                        })
                    )
                )

                # Update offset for next register
                current_offset += (size // 8)

        return registers

    def _parse_bit_fields(self, data: List[Dict[str, Any]], file_path: Path) -> List[BitField]:
        """Parse bit field definitions."""
        fields = []
        current_bit = 0

        for idx, field_data in enumerate(data):
            try:
                # Auto-calculate bit offset if not provided
                bit_offset = field_data.get("bitOffset")
                if bit_offset is None:
                    bit_offset = current_bit

                bit_width = field_data.get("bitWidth", 1)
                access = field_data.get("access", "read-write")

                # Normalize access type
                if access in AccessType.__members__.values():
                    access_type = AccessType(access)
                else:
                    access_type = AccessType.normalize(access)

                fields.append(
                    BitField(
                        **self._filter_none({
                            "name": field_data.get("name"),
                            "bit_offset": bit_offset,
                            "bit_width": bit_width,
                            "access": access_type,
                            "description": field_data.get("description"),
                            "reset_value": field_data.get("resetValue"),
                        })
                    )
                )

                # Update bit offset for next field
                current_bit = bit_offset + bit_width

            except Exception as e:
                raise ParseError(f"Error parsing bitField[{idx}]: {e}", file_path)

        return fields

    def _parse_file_sets(self, data: List[Dict[str, Any]], file_path: Path) -> List[FileSet]:
        """Parse file set definitions, handling imports."""
        file_sets = []
        for idx, fs_data in enumerate(data):
            try:
                # Handle import case
                if "import" in fs_data:
                    import_path = (file_path.parent / fs_data["import"]).resolve()
                    imported_fs = self._load_file_set_from_file(import_path)
                    file_sets.extend(imported_fs)
                    continue

                # Parse inline file set
                files = self._parse_files(fs_data.get("files", []), file_path)

                file_sets.append(
                    FileSet(
                        **self._filter_none({
                            "name": fs_data.get("name"),
                            "description": fs_data.get("description"),
                            "files": files if files else None,
                        })
                    )
                )
            except Exception as e:
                raise ParseError(f"Error parsing fileSet[{idx}]: {e}", file_path)
        return file_sets

    def _load_file_set_from_file(self, file_path: Path) -> List[FileSet]:
        """Load file sets from an external YAML file."""
        if not file_path.exists():
            raise ParseError(f"FileSet file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ParseError(f"YAML syntax error in fileset file: {e}", file_path)

        if not isinstance(data, list):
            data = [data]

        return self._parse_file_sets(data, file_path)

    def _parse_files(self, data: List[Dict[str, Any]], file_path: Path) -> List[File]:
        """Parse file definitions."""
        files = []
        for idx, file_data in enumerate(data):
            try:
                file_type_str = file_data.get("type", "unknown")

                # Normalize file type to enum
                try:
                    file_type = FileType(file_type_str)
                except ValueError:
                    # Try uppercase
                    file_type = FileType(file_type_str.upper())

                files.append(
                    File(
                        **self._filter_none({
                            "path": file_data.get("path"),
                            "type": file_type,
                            "description": file_data.get("description"),
                        })
                    )
                )
            except Exception as e:
                raise ParseError(f"Error parsing file[{idx}]: {e}", file_path)
        return files

    def _load_bus_library(self, file_path: Path) -> Dict[str, Any]:
        """Load and cache bus library definitions."""
        if file_path in self._bus_library_cache:
            return self._bus_library_cache[file_path]

        if not file_path.exists():
            raise ParseError(f"Bus library file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                bus_lib = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ParseError(f"YAML syntax error in bus library: {e}", file_path)

        self._bus_library_cache[file_path] = bus_lib
        return bus_lib
