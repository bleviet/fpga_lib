library ieee;
use ieee.std_logic_1164.all;

entity neorv32_cpu_icc is
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        csr_we_i : in std_ulogic;
        csr_re_i : in std_ulogic;
        csr_addr_i : in std_ulogic_vector(11 downto 0);
        csr_wdata_i : in std_ulogic_vector(XLEN-1 downto 0);
        csr_rdata_o : out std_ulogic_vector(XLEN-1 downto 0);
        icc_tx_o : out icc_t;
        icc_rx_i : in icc_t
    );
end entity neorv32_cpu_icc;