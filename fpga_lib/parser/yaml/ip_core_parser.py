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
        """
        Remove keys with None values from dictionary.

        This is required for Pydantic v2 compatibility. When a model field has
        a default value or default_factory, passing None explicitly causes
        validation errors. By filtering None values, we let Pydantic use its
        own defaults instead.

        Args:
            data: Dictionary that may contain None values

        Returns:
            Dictionary with all None-valued keys removed

        Example:
            >>> # Without filtering - FAILS if description has default value:
            >>> Clock(name="CLK", description=None)
            ValidationError: description field expects string, got None

            >>> # With filtering - WORKS:
            >>> Clock(**_filter_none({"name": "CLK", "description": None}))
            Clock(name="CLK", description="")  # Uses default value
        """
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

        # Create IpCore model - only pass non-empty values to use Pydantic defaults
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
        - memoryMaps: { import: "file.yml" } or { import: "file.memmap.yml" }
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
        """
        Load memory maps from an external YAML file.

        Supports both:
        - Legacy multi-document format with registerTemplates
        - New .memmap.yml format (list at root with addressBlocks)
        """
        if not file_path.exists():
            raise ParseError(f"Memory map file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Try parsing as multi-document YAML first (legacy format)
            docs = list(yaml.safe_load_all(content))
        except yaml.YAMLError as e:
            raise ParseError(f"YAML syntax error in memory map file: {e}", file_path)

        # Detect format based on structure
        if len(docs) > 1 and isinstance(docs[0], dict) and "registerTemplates" in docs[0]:
            # Legacy multi-document format with templates
            self._register_templates = docs[0]["registerTemplates"]
            map_data = docs[1]  # Second document has the actual maps
        else:
            # Single document or new format
            map_data = docs[-1] if docs else []

        # Check if map_data is a list (new .memmap.yml format) or dict (legacy)
        if isinstance(map_data, list):
            # New format: list of memory maps with addressBlocks
            return self._parse_memory_map_list(map_data, file_path)
        elif isinstance(map_data, dict):
            # Legacy format: single dict, convert to list
            return self._parse_memory_map_list([map_data], file_path)
        else:
            raise ParseError(f"Invalid memory map structure in {file_path}", file_path)

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
        """Parse address block definitions. Supports both 'baseAddress' (legacy) and 'offset' (new)."""
        blocks = []
        for idx, block_data in enumerate(data):
            try:
                # Support both 'baseAddress' (legacy) and 'offset' (new format)
                base_address = block_data.get("baseAddress") or block_data.get("offset", 0)

                registers = self._parse_registers(block_data.get("registers", []), file_path)

                # Calculate range if not provided (new format compatibility)
                range_value = block_data.get("range")
                if range_value is None and registers:
                    # Calculate range based on last register
                    max_offset = max(reg.address_offset + (reg.size // 8) for reg in registers)
                    # Round up to nearest power of 2 or use max_offset + padding
                    range_value = max(max_offset, 64)  # Minimum 64 bytes
                elif range_value is None:
                    range_value = 4096  # Default 4KB if no registers

                blocks.append(
                    AddressBlock(
                        **self._filter_none({
                            "name": block_data.get("name"),
                            "base_address": base_address,
                            "range": range_value,
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
        """
        Parse register definitions, including template expansion and nested arrays.

        Supports:
        - Legacy: addressOffset, generateArray with templates
        - New: offset, nested 'registers' arrays with count/stride
        """
        registers = []
        current_offset = 0

        for idx, reg_data in enumerate(data):
            try:
                # Handle reserved space
                if "reserved" in reg_data:
                    current_offset += reg_data["reserved"]
                    continue

                # Handle nested register arrays (new .memmap.yml format)
                # Example: TIMER with count=4 containing nested CTRL, STATUS registers
                if "registers" in reg_data and "count" in reg_data:
                    expanded_regs = self._expand_nested_register_array(
                        reg_data, current_offset, file_path
                    )
                    registers.extend(expanded_regs)
                    # Update offset after expanded registers
                    if expanded_regs:
                        last_reg = expanded_regs[-1]
                        current_offset = last_reg.address_offset + (last_reg.size // 8)
                    continue

                # Handle generateArray - expand template into multiple registers (legacy)
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
                # Support both 'addressOffset' (legacy) and 'offset' (new)
                address_offset = reg_data.get("addressOffset") or reg_data.get("offset")
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

    def _expand_nested_register_array(
        self,
        array_spec: Dict[str, Any],
        base_offset: int,
        file_path: Path
    ) -> List[Register]:
        """
        Expand a nested register array (new .memmap.yml format).

        Example:
            - name: TIMER
              count: 4
              stride: 16
              registers:
                - name: CTRL
                  offset: 0
                - name: STATUS
                  offset: 4

        Creates:
            TIMER_0_CTRL @ base + 0
            TIMER_0_STATUS @ base + 4
            TIMER_1_CTRL @ base + 16
            TIMER_1_STATUS @ base + 20
            ...

        Args:
            array_spec: Dict with 'name', 'count', 'stride', 'registers' keys
            base_offset: Starting address offset
            file_path: File path for error reporting

        Returns:
            List of Register instances with hierarchical names
        """
        base_name = array_spec.get("name", "REG")
        count = array_spec.get("count", 1)
        stride = array_spec.get("stride", 4)
        sub_registers = array_spec.get("registers", [])

        if not sub_registers:
            raise ParseError(
                f"Nested register array '{base_name}' has no sub-registers",
                file_path
            )

        registers = []

        # Generate instances for each array element
        for instance_idx in range(count):
            instance_offset = base_offset + (instance_idx * stride)

            # Expand each sub-register
            for sub_reg in sub_registers:
                # Create hierarchical name: TIMER_0_CTRL, TIMER_1_STATUS, etc.
                reg_name = f"{base_name}_{instance_idx}_{sub_reg['name']}"

                # Get offset relative to array instance
                sub_offset = sub_reg.get("offset", 0)
                final_offset = instance_offset + sub_offset

                size = sub_reg.get("size", 32)
                access = sub_reg.get("access", "read-write")

                # Normalize access type
                if access in AccessType.__members__.values():
                    access_type = AccessType(access)
                else:
                    access_type = AccessType.normalize(access)

                fields = self._parse_bit_fields(sub_reg.get("fields", []), file_path)

                registers.append(
                    Register(
                        **self._filter_none({
                            "name": reg_name,
                            "address_offset": final_offset,
                            "size": size,
                            "access": access_type,
                            "description": sub_reg.get("description"),
                            "reset_value": sub_reg.get("resetValue"),
                            "fields": fields if fields else None,
                        })
                    )
                )

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
        """
        Parse bit field definitions.

        Supports both:
        - Legacy: bitOffset, bitWidth
        - New: bits: "[msb:lsb]" or bits: "[n:n]" for single bit
        """
        fields = []
        current_bit = 0

        for idx, field_data in enumerate(data):
            try:
                bit_offset = None
                bit_width = None

                # Check for new 'bits' format first
                if "bits" in field_data:
                    bits_str = field_data["bits"]
                    bit_offset, bit_width = self._parse_bits_notation(bits_str)
                else:
                    # Legacy format: bitOffset and bitWidth
                    bit_offset = field_data.get("bitOffset")
                    bit_width = field_data.get("bitWidth", 1)

                # Auto-calculate bit offset if not provided
                if bit_offset is None:
                    bit_offset = current_bit

                if bit_width is None:
                    bit_width = 1

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
                            "reset_value": field_data.get("resetValue") or field_data.get("reset"),
                        })
                    )
                )

                # Update bit offset for next field
                current_bit = bit_offset + bit_width

            except Exception as e:
                raise ParseError(f"Error parsing bitField[{idx}]: {e}", file_path)

        return fields

    def _parse_bits_notation(self, bits_str: str) -> tuple[int, int]:
        """
        Parse bits notation like "[7:4]" or "[0:0]" into (offset, width).

        Args:
            bits_str: String like "[7:4]" or "[0:0]"

        Returns:
            Tuple of (bit_offset, bit_width)

        Raises:
            ValueError: If format is invalid

        Examples:
            "[7:4]" -> (4, 4)   # offset=4, width=4
            "[0:0]" -> (0, 1)   # offset=0, width=1
            "[31:0]" -> (0, 32) # offset=0, width=32
        """
        if not bits_str:
            raise ValueError("Empty bits notation")

        # Remove brackets and whitespace
        clean_str = bits_str.strip().strip("[]").strip()

        if ":" not in clean_str:
            raise ValueError(f"Invalid bits notation (missing colon): {bits_str}")

        try:
            parts = clean_str.split(":")
            if len(parts) != 2:
                raise ValueError(f"Invalid bits notation (expected MSB:LSB): {bits_str}")

            msb = int(parts[0].strip())
            lsb = int(parts[1].strip())

            if msb < lsb:
                raise ValueError(f"Invalid bits notation (MSB < LSB): {bits_str}")

            bit_offset = lsb
            bit_width = msb - lsb + 1

            return bit_offset, bit_width

        except ValueError as e:
            raise ValueError(f"Failed to parse bits notation '{bits_str}': {e}")

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
