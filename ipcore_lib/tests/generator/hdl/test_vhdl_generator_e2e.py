"""End-to-end tests for VHDL generator using example YAML files."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from ipcore_lib.generator.hdl.vhdl_generator import VHDLGenerator
from ipcore_lib.parser.yaml.ip_yaml_parser import YamlIpCoreParser


class TestVHDLGeneratorE2E:
    """End-to-end generation tests using example YAML specs."""

    @pytest.fixture
    def example_dir(self):
        """Get path to example YAML files."""
        return Path(__file__).parent.parent.parent.parent.parent / "ipcore_spec" / "examples"

    @pytest.fixture
    def parser(self):
        """Create YAML parser instance."""
        return YamlIpCoreParser()

    @pytest.fixture
    def generator(self):
        """Create VHDL generator instance."""
        return VHDLGenerator()

    def test_generate_from_minimal_yaml(self, example_dir, parser, generator):
        """Test generation from minimal.ip.yml example."""
        yaml_file = example_dir / "test_cases" / "minimal.ip.yml"

        if not yaml_file.exists():
            pytest.skip(f"Example file not found: {yaml_file}")

        # Parse YAML
        ip_core = parser.parse_file(str(yaml_file))
        assert ip_core is not None

        # Generate all VHDL files
        files = generator.generate_all(ip_core, bus_type="axil")

        # Verify basic structure
        assert len(files) >= 4
        pkg_file = f"{ip_core.vlnv.name.lower()}_pkg.vhd"
        assert pkg_file in files
        assert len(files[pkg_file]) > 0

    def test_generate_from_basic_yaml(self, example_dir, parser, generator):
        """Test generation from basic.ip.yml example."""
        yaml_file = example_dir / "test_cases" / "basic.ip.yml"

        if not yaml_file.exists():
            pytest.skip(f"Example file not found: {yaml_file}")

        # Parse YAML
        ip_core = parser.parse_file(str(yaml_file))
        assert ip_core is not None

        # Generate all VHDL files
        files = generator.generate_all(ip_core, bus_type="axil")

        # Verify files generated
        name = ip_core.vlnv.name.lower()
        assert f"{name}_pkg.vhd" in files
        assert f"{name}.vhd" in files
        assert f"{name}_core.vhd" in files
        assert f"{name}_axil.vhd" in files

        # Verify content is not empty
        for filename, content in files.items():
            assert len(content) > 100, f"{filename} is too short"

    def test_generate_from_timer_yaml(self, example_dir, parser, generator):
        """Test generation from my_timer_core.ip.yml example."""
        yaml_file = example_dir / "timers" / "my_timer_core.ip.yml"

        if not yaml_file.exists():
            pytest.skip(f"Example file not found: {yaml_file}")

        # Parse YAML
        ip_core = parser.parse_file(str(yaml_file))
        assert ip_core is not None

        # Generate VHDL files
        files = generator.generate_all(ip_core, bus_type="axil")

        # Timer should have registers
        name = ip_core.vlnv.name.lower()
        pkg_content = files[f"{name}_pkg.vhd"]
        assert "package" in pkg_content

        # Check for user ports (timer should have some)
        if ip_core.ports:
            top_content = files[f"{name}.vhd"]
            assert "port" in top_content

    def test_generate_testbench_from_yaml(self, example_dir, parser, generator):
        """Test testbench generation from YAML example."""
        yaml_file = example_dir / "test_cases" / "basic.ip.yml"

        if not yaml_file.exists():
            pytest.skip(f"Example file not found: {yaml_file}")

        # Parse YAML
        ip_core = parser.parse_file(str(yaml_file))
        assert ip_core is not None

        # Generate testbench files
        tb_files = generator.generate_testbench(ip_core, bus_type="axil")

        # Verify testbench structure
        assert len(tb_files) == 3
        name = ip_core.vlnv.name.lower()
        assert f"{name}_test.py" in tb_files
        assert "Makefile" in tb_files
        assert f"{name}_memmap.yml" in tb_files

        # Verify cocotb test structure
        test_content = tb_files[f"{name}_test.py"]
        assert "import cocotb" in test_content
        assert "async def" in test_content

    def test_generate_vendor_files_from_yaml(self, example_dir, parser, generator):
        """Test vendor file generation from YAML example."""
        yaml_file = example_dir / "test_cases" / "minimal.ip.yml"

        if not yaml_file.exists():
            pytest.skip(f"Example file not found: {yaml_file}")

        # Parse YAML
        ip_core = parser.parse_file(str(yaml_file))
        assert ip_core is not None

        # Generate vendor files
        intel_files = generator.generate_vendor_files(ip_core, vendor="intel")
        xilinx_files = generator.generate_vendor_files(ip_core, vendor="xilinx")

        # Verify Intel files
        assert len(intel_files) == 1
        name = ip_core.vlnv.name.lower()
        assert f"{name}_hw.tcl" in intel_files

        # Verify Xilinx files
        assert len(xilinx_files) == 1
        assert "component.xml" in xilinx_files


@pytest.mark.slow
class TestVHDLGeneratorSyntaxValidation:
    """Syntax validation tests using GHDL (requires GHDL installed)."""

    @pytest.fixture
    def example_dir(self):
        """Get path to example YAML files."""
        return Path(__file__).parent.parent.parent.parent.parent / "ipcore_spec" / "examples"

    @pytest.fixture
    def parser(self):
        """Create YAML parser instance."""
        return YamlIpCoreParser()

    @pytest.fixture
    def generator(self):
        """Create VHDL generator instance."""
        return VHDLGenerator()

    def _check_ghdl_available(self):
        """Check if GHDL is available."""
        try:
            result = subprocess.run(["ghdl", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _validate_vhdl_syntax(self, vhdl_files: dict) -> bool:
        """
        Validate VHDL syntax using GHDL.

        Args:
            vhdl_files: Dictionary mapping filename to VHDL content

        Returns:
            True if all files are syntactically correct
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Write all VHDL files
            vhdl_only = {}
            for filename, content in vhdl_files.items():
                if filename.endswith(".vhd"):
                    (tmppath / filename).write_text(content)
                    vhdl_only[filename] = content

            # Analyze files in dependency order: package first, then submodules, then top
            filenames = list(vhdl_only.keys())

            # Sort: package (_pkg.vhd) first, submodules (with suffixes) in middle, top-level last
            def sort_key(f):
                if "_pkg.vhd" in f:
                    return (0, f)  # Package first
                elif any(
                    suffix in f
                    for suffix in ["_axil.vhd", "_avmm.vhd", "_core.vhd", "_regfile.vhd"]
                ):
                    return (1, f)  # Submodules with known suffixes
                else:
                    return (2, f)  # Top-level and others last

            filenames.sort(key=sort_key)

            # Analyze each file with GHDL in order
            for filename in filenames:
                result = subprocess.run(
                    ["ghdl", "-a", "--std=08", str(tmppath / filename)],
                    capture_output=True,
                    cwd=tmpdir,
                    timeout=10,
                )
                if result.returncode != 0:
                    print(f"GHDL error in {filename}:")
                    print(result.stderr.decode())
                    return False

            return True

    def test_minimal_yaml_syntax(self, example_dir, parser, generator):
        """Test that minimal.ip.yml generates syntactically correct VHDL."""
        pytest.skip("Minimal IP without registers - generator not designed for this case")
        if not self._check_ghdl_available():
            pytest.skip("GHDL not available")

        yaml_file = example_dir / "test_cases" / "minimal.ip.yml"
        if not yaml_file.exists():
            pytest.skip(f"Example file not found: {yaml_file}")

        # Parse and generate
        ip_core = parser.parse_file(str(yaml_file))
        files = generator.generate_all(ip_core, bus_type="axil")

        # Validate syntax
        assert self._validate_vhdl_syntax(files), "Generated VHDL has syntax errors"

    def test_ip_with_registers_syntax(self, parser, generator):
        """Test GHDL syntax validation with an IP core that has registers."""
        if not self._check_ghdl_available():
            pytest.skip("GHDL not available")

        from ipcore_lib.model.base import VLNV
        from ipcore_lib.model.core import IpCore
        from ipcore_lib.model.memory import AccessType, AddressBlock, BitField, MemoryMap, Register

        # Create IP core with registers
        memory_map = MemoryMap(
            name="regs",
            address_blocks=[
                AddressBlock(
                    name="control",
                    base_address=0x00,
                    range=0x1000,
                    width=32,
                    registers=[
                        Register(
                            name="CTRL",
                            address_offset=0x00,
                            size=32,
                            access=AccessType.READ_WRITE,
                            fields=[
                                BitField(
                                    name="enable",
                                    bit_offset=0,
                                    bit_width=1,
                                    access=AccessType.READ_WRITE,
                                ),
                                BitField(
                                    name="mode",
                                    bit_offset=1,
                                    bit_width=2,
                                    access=AccessType.READ_WRITE,
                                ),
                            ],
                        ),
                        Register(
                            name="STATUS",
                            address_offset=0x04,
                            size=32,
                            access=AccessType.READ_ONLY,
                            fields=[
                                BitField(
                                    name="ready",
                                    bit_offset=0,
                                    bit_width=1,
                                    access=AccessType.READ_ONLY,
                                )
                            ],
                        ),
                    ],
                )
            ],
        )

        ip_core = IpCore(
            api_version="test/v1.0",
            vlnv=VLNV(vendor="test", library="lib", name="syntax_test", version="1.0"),
            description="IP core for GHDL syntax validation",
            memory_maps=[memory_map],
        )

        # Generate all files
        files = generator.generate_all(ip_core, bus_type="axil")

        # Validate VHDL syntax with GHDL
        assert self._validate_vhdl_syntax(files), "Generated VHDL has syntax errors"

    def test_basic_yaml_syntax(self, example_dir, parser, generator):
        """Test that basic.ip.yml generates syntactically correct VHDL."""
        pytest.skip("Basic IP without registers - generator not designed for this case")
        if not self._check_ghdl_available():
            pytest.skip("GHDL not available")

        yaml_file = example_dir / "test_cases" / "basic.ip.yml"
        if not yaml_file.exists():
            pytest.skip(f"Example file not found: {yaml_file}")

        # Parse and generate
        ip_core = parser.parse_file(str(yaml_file))
        files = generator.generate_all(ip_core, bus_type="axil")

        # Validate syntax
        assert self._validate_vhdl_syntax(files), "Generated VHDL has syntax errors"
