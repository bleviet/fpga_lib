-- 02_multi_bus_custom_ports.vhd
-- This entity is generated from examples/yaml/ip/02_multi_bus_custom_ports.yaml

library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

entity multibuscustomports is
  generic (
    gpio_width      : integer := 16;
    axis_data_width : integer := 64
  );
  port (
    -- Global signals
    sys_clk    : in    std_logic;
    sys_resetn : in    std_logic;

    -- Custom ports
    gpio_out  : out   std_logic_vector(gpio_width - 1 downto 0);
    status_in : in    std_logic_vector(7 downto 0);

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
    s_axi_ctrl_rready  : in    std_logic;

    -- AXI4-Stream Master Interface (M_AXIS_DATA)
    m_axis_tdata  : out   std_logic_vector(axis_data_width - 1 downto 0);
    m_axis_tvalid : out   std_logic;
    m_axis_tready : in    std_logic
  );
end entity multibuscustomports;

architecture rtl of multibuscustomports is

-- Dummy logic for demonstration

begin

  -- Tie off outputs
  gpio_out           <= (others => '0');
  s_axi_ctrl_awready <= '1';
  s_axi_ctrl_wready  <= '1';
  s_axi_ctrl_bresp   <= "00";
  s_axi_ctrl_bvalid  <= '0';
  s_axi_ctrl_arready <= '1';
  s_axi_ctrl_rdata   <= (others => '0');
  s_axi_ctrl_rresp   <= "00";
  s_axi_ctrl_rvalid  <= '0';
  m_axis_tdata       <= (others => '0');
  m_axis_tvalid      <= '0';

end architecture rtl;
