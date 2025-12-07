"""
Unit tests for AI-Enhanced VHDL Parser.

Tests both deterministic parsing (Phase 1) and AI enhancements (Phase 2).
"""

import pytest
from pathlib import Path

from fpga_lib.parser.hdl.vhdl_ai_parser import (
    VHDLAiParser,
    ParserConfig,
    ParsedEntityData,
    VhdlAiAnalyzer
)
from fpga_lib.model.core import IpCore
from fpga_lib.model.port import PortDirection


# ============================================================================
# Test Data
# ============================================================================

SIMPLE_ENTITY = """
entity simple_counter is
    generic (
        WIDTH : integer := 8
    );
    port (
        clk : in std_logic;
        reset : in std_logic;
        enable : in std_logic;
        count : out std_logic_vector(WIDTH-1 downto 0)
    );
end entity simple_counter;
"""

AXI_ENTITY = """
-- AXI4-Lite Slave Interface Example
entity axi_peripheral is
    port (
        -- Clock and Reset
        aclk : in std_logic;
        aresetn : in std_logic;

        -- AXI4-Lite Slave Interface
        s_axi_awaddr : in std_logic_vector(7 downto 0);
        s_axi_awvalid : in std_logic;
        s_axi_awready : out std_logic;
        s_axi_wdata : in std_logic_vector(31 downto 0);
        s_axi_wvalid : in std_logic;
        s_axi_wready : out std_logic;
        s_axi_bresp : out std_logic_vector(1 downto 0);
        s_axi_bvalid : out std_logic;
        s_axi_bready : in std_logic;
        s_axi_araddr : in std_logic_vector(7 downto 0);
        s_axi_arvalid : in std_logic;
        s_axi_arready : out std_logic;
        s_axi_rdata : out std_logic_vector(31 downto 0);
        s_axi_rresp : out std_logic_vector(1 downto 0);
        s_axi_rvalid : out std_logic;
        s_axi_rready : in std_logic
    );
end entity axi_peripheral;
"""


# ============================================================================
# Phase 1 Tests (Deterministic Parsing)
# ============================================================================


class TestDeterministicParsing:
    """Test pyparsing-based structure extraction."""

    def test_simple_entity_parsing(self):
        """Test parsing a simple entity without AI."""
        parser = VHDLAiParser()
        ip_core = parser.parse_text(SIMPLE_ENTITY)

        assert ip_core.vlnv.name == "simple_counter"
        assert len(ip_core.ports) == 4
        assert len(ip_core.parameters) == 1

    def test_port_directions(self):
        """Test port direction parsing."""
        parser = VHDLAiParser()
        ip_core = parser.parse_text(SIMPLE_ENTITY)

        port_map = {port.name: port for port in ip_core.ports}

        assert port_map["clk"].direction == PortDirection.IN
        assert port_map["reset"].direction == PortDirection.IN
        assert port_map["enable"].direction == PortDirection.IN
        assert port_map["count"].direction == PortDirection.OUT

    def test_port_widths(self):
        """Test port width extraction."""
        parser = VHDLAiParser()
        ip_core = parser.parse_text(SIMPLE_ENTITY)

        port_map = {port.name: port for port in ip_core.ports}

        assert port_map["clk"].width == 1
        assert port_map["count"].width == 8  # WIDTH-1 downto 0

    def test_generic_parameters(self):
        """Test generic/parameter parsing."""
        parser = VHDLAiParser()
        ip_core = parser.parse_text(SIMPLE_ENTITY)

        assert len(ip_core.parameters) == 1
        param = ip_core.parameters[0]

        assert param.name == "WIDTH"
        assert param.data_type == "integer"
        assert param.value == "8"

    def test_axi_entity_parsing(self):
        """Test parsing AXI entity without AI."""
        parser = VHDLAiParser()
        ip_core = parser.parse_text(AXI_ENTITY)

        assert ip_core.vlnv.name == "axi_peripheral"
        assert len(ip_core.ports) > 10  # Should have all AXI signals


# ============================================================================
# Phase 2 Tests (AI Enhancement)
# ============================================================================


class TestAiEnhancement:
    """Test AI-powered features (requires LLM)."""

    @pytest.fixture
    def ai_parser(self):
        """Create AI-enabled parser."""
        config = ParserConfig(
            enable_llm=True,
            llm_provider="ollama",
            llm_model="llama3.3:latest"
        )
        return VHDLAiParser(config=config)

    @pytest.fixture
    def ai_analyzer(self):
        """Create AI analyzer."""
        return VhdlAiAnalyzer(provider_name="ollama")

    def test_ai_availability(self, ai_analyzer):
        """Test if AI is available (skip if not)."""
        if not ai_analyzer.is_available():
            pytest.skip("LLM not available (Ollama not running or llm_core not installed)")

    @pytest.mark.integration
    def test_bus_interface_detection(self, ai_parser, ai_analyzer):
        """Test AI detection of AXI bus interface."""
        if not ai_analyzer.is_available():
            pytest.skip("LLM not available")

        ip_core = ai_parser.parse_text(AXI_ENTITY)

        # AI should detect AXI interface
        assert len(ip_core.bus_interfaces) > 0, "AI should detect at least one bus interface"

        # Check if AXI detected
        bus_types = [bus.type.upper() for bus in ip_core.bus_interfaces]
        assert any("AXI" in bt for bt in bus_types), f"Expected AXI, got {bus_types}"

    @pytest.mark.integration
    def test_description_generation(self, ai_parser, ai_analyzer):
        """Test AI-generated description."""
        if not ai_analyzer.is_available():
            pytest.skip("LLM not available")

        ip_core = ai_parser.parse_text(AXI_ENTITY)

        # AI should generate meaningful description
        assert len(ip_core.description) > 10
        assert "axi" in ip_core.description.lower() or "peripheral" in ip_core.description.lower()


# ============================================================================
# Configuration Tests
# ============================================================================


class TestConfiguration:
    """Test parser configuration options."""

    def test_default_config(self):
        """Test default configuration."""
        config = ParserConfig()

        assert config.enable_llm is False
        assert config.llm_provider == "ollama"
        assert config.strict_mode is False

    def test_ai_disabled_by_default(self):
        """Test that AI is disabled by default."""
        parser = VHDLAiParser()
        assert parser.ai_analyzer is None

    def test_strict_mode_disabled(self):
        """Test graceful degradation in non-strict mode."""
        config = ParserConfig(strict_mode=False)
        parser = VHDLAiParser(config=config)

        # Invalid VHDL should return minimal valid core
        ip_core = parser.parse_text("invalid vhdl code")
        assert ip_core is not None
        assert isinstance(ip_core, IpCore)

    def test_strict_mode_enabled(self):
        """Test strict mode fails on invalid input."""
        config = ParserConfig(strict_mode=True)
        parser = VHDLAiParser(config=config)

        with pytest.raises(ValueError):
            parser.parse_text("invalid vhdl code")


# ============================================================================
# Model Validation Tests
# ============================================================================


class TestModelValidation:
    """Test Pydantic model validation."""

    def test_ip_core_model_valid(self):
        """Test that parsed IP core is valid Pydantic model."""
        parser = VHDLAiParser()
        ip_core = parser.parse_text(SIMPLE_ENTITY)

        # Should be able to export to dict
        data = ip_core.model_dump()
        assert isinstance(data, dict)
        assert "vlnv" in data
        assert "ports" in data

    def test_ip_core_json_export(self):
        """Test JSON export."""
        parser = VHDLAiParser()
        ip_core = parser.parse_text(SIMPLE_ENTITY)

        # Should be able to export to JSON
        json_str = ip_core.model_dump_json()
        assert isinstance(json_str, str)
        assert "simple_counter" in json_str

    def test_port_validation(self):
        """Test port model validation."""
        parser = VHDLAiParser()
        ip_core = parser.parse_text(SIMPLE_ENTITY)

        for port in ip_core.ports:
            # Port should have valid direction
            assert port.direction in [PortDirection.IN, PortDirection.OUT, PortDirection.INOUT]
            # Port width should be positive
            assert port.width > 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests with real files."""

    def test_parse_example_file(self):
        """Test parsing the example AXI peripheral file."""
        example_file = Path(__file__).parent.parent.parent.parent / "examples" / "test_vhdl" / "axi_example_peripheral.vhd"

        if not example_file.exists():
            pytest.skip(f"Example file not found: {example_file}")

        parser = VHDLAiParser()
        ip_core = parser.parse_file(example_file)

        assert ip_core.vlnv.name == "axi_example_peripheral"
        assert len(ip_core.ports) > 0
        assert len(ip_core.parameters) > 0


# ============================================================================
# Run Tests
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
