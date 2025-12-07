-- Example AXI4-Lite Peripheral for AI Parser Testing
-- This demonstrates how the AI parser can detect bus interfaces from comments and naming

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Simple AXI4-Lite slave peripheral with control and status registers
entity axi_example_peripheral is
    generic (
        -- AXI4-Lite address width
        C_S_AXI_ADDR_WIDTH : integer := 6;
        -- AXI4-Lite data width
        C_S_AXI_DATA_WIDTH : integer := 32;
        -- Peripheral specific parameters
        COUNTER_WIDTH    : integer := 32;
        ENABLE_INTERRUPT : boolean := true
    );
    port (
        -- Global Clock and Reset
        aclk    : in std_logic;
        aresetn : in std_logic;

        -- AXI4-Lite Slave Interface
        -- Write Address Channel
        s_axi_awaddr  : in std_logic_vector(C_S_AXI_ADDR_WIDTH - 1 downto 0);
        s_axi_awprot  : in std_logic_vector(2 downto 0);
        s_axi_awvalid : in std_logic;
        s_axi_awready : out std_logic;

        -- Write Data Channel
        s_axi_wdata  : in std_logic_vector(C_S_AXI_DATA_WIDTH - 1 downto 0);
        s_axi_wstrb  : in std_logic_vector((C_S_AXI_DATA_WIDTH/8) - 1 downto 0);
        s_axi_wvalid : in std_logic;
        s_axi_wready : out std_logic;

        -- Write Response Channel
        s_axi_bresp  : out std_logic_vector(1 downto 0);
        s_axi_bvalid : out std_logic;
        s_axi_bready : in std_logic;

        -- Read Address Channel
        s_axi_araddr  : in std_logic_vector(C_S_AXI_ADDR_WIDTH - 1 downto 0);
        s_axi_arprot  : in std_logic_vector(2 downto 0);
        s_axi_arvalid : in std_logic;
        s_axi_arready : out std_logic;

        -- Read Data Channel
        s_axi_rdata  : out std_logic_vector(C_S_AXI_DATA_WIDTH - 1 downto 0);
        s_axi_rresp  : out std_logic_vector(1 downto 0);
        s_axi_rvalid : out std_logic;
        s_axi_rready : in std_logic;

        -- Peripheral specific ports
        irq         : out std_logic;
        enable      : in std_logic;
        counter_out : out std_logic_vector(COUNTER_WIDTH - 1 downto 0)
    );
end entity axi_example_peripheral;

architecture rtl of axi_example_peripheral is
    -- Register map
    signal ctrl_reg    : std_logic_vector(31 downto 0);
    signal status_reg  : std_logic_vector(31 downto 0);
    signal counter_reg : std_logic_vector(COUNTER_WIDTH - 1 downto 0);

begin
    -- Implementation would go here

end architecture rtl;
