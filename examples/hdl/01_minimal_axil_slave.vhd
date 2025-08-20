-- 01_minimal_axil_slave.vhd
-- This entity is generated from examples/yaml/ip/01_minimal_axil_slave.yaml

library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

entity minimalaxilslave is
  port (
    -- Global signals
    sys_clk    : in    std_logic;
    sys_resetn : in    std_logic;

    -- AXI4-Lite Slave Interface (S_AXI_CTRL)
    s_axi_ctrl_awaddr  : in    std_logic_vector(31 downto 0);
    s_axi_ctrl_awprot  : in    std_logic_vector(2 downto 0);
    s_axi_ctrl_awvalid : in    std_logic;
    s_axi_ctrl_awready : out   std_logic;
    s_axi_ctrl_wdata   : in    std_logic_vector(31 downto 0);
    s_axi_ctrl_wstrb   : in    std_logic_vector(3 downto 0);
    s_axi_ctrl_wvalid  : in    std_logic;
    s_axi_ctrl_wready  : out   std_logic;
    s_axi_ctrl_bresp   : out   std_logic_vector(1 downto 0);
    s_axi_ctrl_bvalid  : out   std_logic;
    s_axi_ctrl_bready  : in    std_logic;
    s_axi_ctrl_araddr  : in    std_logic_vector(31 downto 0);
    s_axi_ctrl_arprot  : in    std_logic_vector(2 downto 0);
    s_axi_ctrl_arvalid : in    std_logic;
    s_axi_ctrl_arready : out   std_logic;
    s_axi_ctrl_rdata   : out   std_logic_vector(31 downto 0);
    s_axi_ctrl_rresp   : out   std_logic_vector(1 downto 0);
    s_axi_ctrl_rvalid  : out   std_logic;
    s_axi_ctrl_rready  : in    std_logic
  );
end entity minimalaxilslave;

architecture rtl of minimalaxilslave is

-- Dummy logic for demonstration

begin

  -- Tie off outputs
  s_axi_ctrl_awready <= '1';
  s_axi_ctrl_wready  <= '1';
  s_axi_ctrl_bresp   <= "00";
  s_axi_ctrl_bvalid  <= '0';
  s_axi_ctrl_arready <= '1';
  s_axi_ctrl_rdata   <= (others => '0');
  s_axi_ctrl_rresp   <= "00";
  s_axi_ctrl_rvalid  <= '0';

end architecture rtl;
