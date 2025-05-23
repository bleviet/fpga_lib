library ieee;
use ieee.std_logic_1164.all;

entity neorv32_cpu_pmp is
    generic (
        NUM_REGIONS : natural range 0 to 16;
        GRANULARITY : natural;
        TOR_EN : boolean;
        NAP_EN : boolean
    );
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        ctrl_i : in ctrl_bus_t;
        csr_o : out std_ulogic_vector(XLEN-1 downto 0);
        addr_ls_i : in std_ulogic_vector(XLEN-1 downto 0);
        fault_o : out std_ulogic
    );
end entity neorv32_cpu_pmp;