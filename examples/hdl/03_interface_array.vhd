-- 03_interface_array.vhd
-- This entity is generated from examples/yaml/ip/03_interface_array.yaml

library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

entity interfacearray is
  port (
    -- Global signals
    sys_clk    : in    std_logic;
    sys_resetn : in    std_logic;

    -- AXI4-Stream Slave Interface Array (S_AXIS_CHANNELS)
    -- Channel 0
    s_axis_ch_0_tdata  : in    std_logic_vector(31 downto 0);
    s_axis_ch_0_tvalid : in    std_logic;
    s_axis_ch_0_tready : out   std_logic;
    -- Channel 1
    s_axis_ch_1_tdata  : in    std_logic_vector(31 downto 0);
    s_axis_ch_1_tvalid : in    std_logic;
    s_axis_ch_1_tready : out   std_logic;
    -- Channel 2
    s_axis_ch_2_tdata  : in    std_logic_vector(31 downto 0);
    s_axis_ch_2_tvalid : in    std_logic;
    s_axis_ch_2_tready : out   std_logic;
    -- Channel 3
    s_axis_ch_3_tdata  : in    std_logic_vector(31 downto 0);
    s_axis_ch_3_tvalid : in    std_logic;
    s_axis_ch_3_tready : out   std_logic
  );
end entity interfacearray;

architecture rtl of interfacearray is

-- Dummy logic for demonstration

begin

  -- Tie off outputs
  s_axis_ch_0_tready <= '1';
  s_axis_ch_1_tready <= '1';
  s_axis_ch_2_tready <= '1';
  s_axis_ch_3_tready <= '1';

end architecture rtl;
