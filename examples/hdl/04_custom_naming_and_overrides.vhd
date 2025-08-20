-- 04_custom_naming_and_overrides.vhd
-- This entity is generated from examples/yaml/ip/04_custom_naming_and_overrides.yaml

library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

entity customnamer is
  port (
    -- Global signals
    core_clk   : in    std_logic;
    core_reset : in    std_logic;

    -- Avalon Memory Mapped Slave Interface (AVALON_MM_IF)
    avs_address   : in    std_logic_vector(31 downto 0);
    avs_writedata : in    std_logic_vector(31 downto 0);
    avs_readdata  : out   std_logic_vector(31 downto 0);
    avs_write     : in    std_logic;
    avs_read      : in    std_logic;

    -- AXI4-Stream Master Interface Array (DEBUG_STREAM)
    -- Channel 0
    debug_stream_0_data   : out   std_logic_vector(31 downto 0);
    debug_stream_0_valid  : out   std_logic;
    debug_stream_0_tready : in    std_logic;
    -- Channel 1
    debug_stream_1_data   : out   std_logic_vector(31 downto 0);
    debug_stream_1_valid  : out   std_logic;
    debug_stream_1_tready : in    std_logic
  );
end entity customnamer;

architecture rtl of customnamer is

-- Dummy logic for demonstration

begin

  -- Tie off outputs
  avs_readdata         <= (others => '0');
  debug_stream_0_data  <= (others => '0');
  debug_stream_0_valid <= '0';
  debug_stream_1_data  <= (others => '0');
  debug_stream_1_valid <= '0';

end architecture rtl;
