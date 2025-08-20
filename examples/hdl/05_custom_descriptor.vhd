-- 05_custom_descriptor.vhd
-- This entity is generated from examples/yaml/ip/05_custom_descriptor.yaml

library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

entity customdescriptorip is
  port (
    -- Global signals
    sys_clk    : in    std_logic;
    sys_resetn : in    std_logic;

    -- Custom Bus Interface (CUSTOM_BUS)
    custom_addr     : in    std_logic_vector(15 downto 0);
    custom_wdata    : in    std_logic_vector(31 downto 0);
    custom_rdata    : out   std_logic_vector(31 downto 0);
    custom_write_en : in    std_logic;
    custom_read_en  : in    std_logic;
    custom_ready    : out   std_logic
  );
end entity customdescriptorip;

architecture rtl of customdescriptorip is

-- Dummy logic for demonstration

begin

  -- Tie off outputs
  custom_rdata <= (others => '0');
  custom_ready <= '1';

end architecture rtl;
